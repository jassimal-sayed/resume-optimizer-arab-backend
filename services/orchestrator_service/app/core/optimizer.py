"""
Resume Optimizer: Core business logic for LLM-based resume optimization.

Features:
- Entity extraction (skills, education, experience)
- JSON validation with retry logic
- Alignment insights (matched/missing/weak)
- Latency tracking
"""

import logging
import re
import time
from typing import Optional

from libs.ai import BaseLLMProvider
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("orchestrator.optimizer")

# Max retry attempts for invalid JSON
MAX_RETRIES = 3

LANGUAGE_LABELS = {
    "en": "English",
    "ar": "Arabic",
}

ARABIC_LETTER_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)


def language_name(code: Optional[str]) -> str:
    return LANGUAGE_LABELS.get(code or "", "English")


def build_language_instructions(
    resume_lang: Optional[str],
    jd_lang: Optional[str],
    desired_output_lang: Optional[str],
) -> str:
    target_lang = desired_output_lang or resume_lang or "en"
    resume_label = language_name(resume_lang)
    jd_label = language_name(jd_lang)
    target_label = language_name(target_lang)

    return f"""Language context:
- Resume language: {resume_label}
- Job description language: {jd_label}
- Desired output language: {target_label}

Rules:
- preview_markdown MUST be written in {target_label}.
- If the resume or job description is in a different language, translate the content into {target_label}.
- Keep proper nouns (company names, product names, certifications) in their original language.
- If preserving ATS keywords helps, you may keep the original keyword in parentheses."""


def arabic_ratio(text: str) -> float:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    arabic_letters = ARABIC_LETTER_RE.findall(text)
    return len(arabic_letters) / len(letters)


def needs_translation(text: str, target_lang: str) -> bool:
    if not text.strip():
        return False
    if target_lang == "ar":
        return arabic_ratio(text) < 0.15
    if target_lang == "en":
        return arabic_ratio(text) > 0.15
    return False


# --- Typed sub-models for Gemini compatibility (no generic dict) ---


class ExperienceItem(BaseModel):
    """Single experience entry."""

    role: str
    company: str
    duration: str
    highlights: list[str]


class ContactInfo(BaseModel):
    """Contact information."""

    email: Optional[str]
    phone: Optional[str]
    linkedin: Optional[str]


class EvidenceItem(BaseModel):
    """Evidence item for alignment insights."""

    source: str  # "resume" or "job"
    snippet: str
    note: str


# --- Main schemas for LLM responses ---


class ExtractedEntities(BaseModel):
    """Entities extracted from resume.

    Note: No default values - Gemini API doesn't support defaults in response schemas.
    """

    skills: list[str]
    tools: list[str]
    education: list[str]
    experience: list[ExperienceItem]
    contact: Optional[ContactInfo]


class AlignmentInsights(BaseModel):
    """Resume-to-job alignment analysis.

    Note: No default values - Gemini API doesn't support defaults in response schemas.
    """

    matched: list[str]
    missing: list[str]
    weak: list[str]
    evidence: list[EvidenceItem]


class OptimizationResultCore(BaseModel):
    """Core optimization result fields for LLM response.

    Note: Separate from full result to avoid nested schema issues with Gemini.
    """

    score: int
    missing_keywords: list[str]
    covered_keywords: list[str]
    change_log: list[str]
    preview_markdown: str


class OptimizationResult(BaseModel):
    """Full optimization result with entities and insights (for internal use)."""

    score: int
    missing_keywords: list[str]
    covered_keywords: list[str]
    change_log: list[str]
    preview_markdown: str
    detected_resume_lang: Optional[str]
    detected_jd_lang: Optional[str]
    extracted_entities: Optional[ExtractedEntities]
    alignment_insights: Optional[AlignmentInsights]


class ReliabilityMetrics(BaseModel):
    """Metrics for Chapter 5 evaluation."""

    invalid_json_attempts: int = 0
    total_attempts: int = 0
    latency_seconds: float = 0.0
    last_run_valid: bool = True


class ResumeOptimizer:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.metrics = ReliabilityMetrics()

    async def translate_markdown(self, text: str, target_lang: str) -> str:
        target_label = language_name(target_lang)
        system_prompt = f"""You are a professional translator.
Translate the resume into {target_label}.

Rules:
- Preserve Markdown formatting and headings.
- Keep names, emails, URLs, and proper nouns as-is.
- Output ONLY the translated Markdown."""
        user_prompt = text
        translated = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_schema=None,
            temperature=0.2,
        )
        return translated.strip() if isinstance(translated, str) else text

    async def extract_entities(self, resume_text: str) -> ExtractedEntities:
        """Extract structured entities from resume text."""
        system_prompt = """You are a resume parser. Extract structured information from the resume.

Return JSON with ALL of these fields (use empty list [] if not found):
- skills: list of technical and soft skills (required, use [] if none)
- tools: list of tools/technologies mentioned (required, use [] if none)
- education: list of degrees/certifications (required, use [] if none)
- experience: list of {role, company, duration, highlights} (required, use [] if none)
- contact: {email, phone, linkedin} or null if not found

IMPORTANT: Always include all fields in your response, even if empty. Be thorough but concise."""

        for attempt in range(MAX_RETRIES):
            try:
                result = await self.llm.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=resume_text,
                    json_schema=ExtractedEntities,
                    temperature=0.3,
                )
                if isinstance(result, ExtractedEntities):
                    return result
            except (ValidationError, Exception) as e:
                logger.warning(f"Entity extraction attempt {attempt + 1} failed: {e}")
                self.metrics.invalid_json_attempts += 1

        return ExtractedEntities(
            skills=[], tools=[], education=[], experience=[], contact=None
        )

    async def analyze_alignment(
        self, resume_text: str, job_description: str, entities: ExtractedEntities
    ) -> AlignmentInsights:
        """Analyze how well the resume aligns with job requirements."""
        system_prompt = """You are a resume-job matcher. Analyze alignment between resume and job description.

Return JSON with ALL of these fields (use empty list [] if none):
- matched: skills/requirements that both resume and job have (required, use [] if none)
- missing: requirements in job that resume lacks (required, use [] if none)
- weak: areas where resume partially matches but needs improvement (required, use [] if none)
- evidence: list of {source: "resume"|"job", snippet: "...", note: "explanation"} (required, use [] if none)

IMPORTANT: Always include all fields in your response. Focus on concrete, actionable insights."""

        user_prompt = f"""Resume Skills: {', '.join(entities.skills + entities.tools)}

Job Description:
{job_description}"""

        for attempt in range(MAX_RETRIES):
            try:
                result = await self.llm.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_schema=AlignmentInsights,
                    temperature=0.3,
                )
                if isinstance(result, AlignmentInsights):
                    return result
            except (ValidationError, Exception) as e:
                logger.warning(f"Alignment analysis attempt {attempt + 1} failed: {e}")
                self.metrics.invalid_json_attempts += 1

        return AlignmentInsights(matched=[], missing=[], weak=[], evidence=[])

    async def optimize(
        self, payload: dict
    ) -> tuple[OptimizationResult, ReliabilityMetrics]:
        """
        Full optimization pipeline with entity extraction and alignment.
        Returns result and reliability metrics for evaluation.
        """
        start_time = time.time()
        self.metrics = ReliabilityMetrics()  # Reset metrics

        resume_text = payload.get("resume_text", "")
        job_description = payload.get("job_description", "")
        instructions = payload.get("instructions", "")
        resume_lang = payload.get("resume_lang") or payload.get("resumeLang")
        jd_lang = payload.get("jd_lang") or payload.get("jdLang")
        desired_output_lang = payload.get("desired_output_lang") or payload.get(
            "desiredOutputLang"
        )
        language_instructions = build_language_instructions(
            resume_lang,
            jd_lang,
            desired_output_lang,
        )

        # Step 1: Extract entities
        entities = await self.extract_entities(resume_text)

        # Step 2: Analyze alignment
        alignment = await self.analyze_alignment(resume_text, job_description, entities)

        # Step 3: Generate optimized resume
        system_prompt = f"""You are an expert resume optimization assistant.
Analyze the resume against the job description and provide ALL of the following:
1. score: A match score from 0-100 (integer, required)
2. missing_keywords: Keywords from JD missing in resume (list of strings, required - use [] if none)
3. covered_keywords: Keywords from JD already in resume (list of strings, required - use [] if none)
4. change_log: Specific changes to make (list of strings, required - use [] if none)
5. preview_markdown: An improved resume in Markdown format (string, required)

IMPORTANT: Always include ALL 5 fields in your response. Respond in valid JSON format.

{language_instructions}"""

        user_prompt = f"""Resume:
{resume_text}

Job Description:
{job_description}

Additional Instructions:
{instructions or 'None'}"""

        core_result = None
        for attempt in range(MAX_RETRIES):
            self.metrics.total_attempts += 1
            try:
                llm_result = await self.llm.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    json_schema=OptimizationResultCore,
                    temperature=0.5,
                )
                if isinstance(llm_result, OptimizationResultCore):
                    core_result = llm_result
                    break
            except (ValidationError, Exception) as e:
                logger.warning(f"Optimization attempt {attempt + 1} failed: {e}")
                self.metrics.invalid_json_attempts += 1

        # Calculate metrics
        end_time = time.time()
        self.metrics.latency_seconds = round(end_time - start_time, 2)
        self.metrics.last_run_valid = core_result is not None

        # Build full result from core + entities + alignment
        if core_result is not None:
            target_lang = desired_output_lang or resume_lang or "en"
            preview_markdown = core_result.preview_markdown
            if needs_translation(preview_markdown, target_lang):
                logger.info(
                    "Translating preview_markdown to %s (arabic_ratio=%.2f)",
                    target_lang,
                    arabic_ratio(preview_markdown),
                )
                try:
                    preview_markdown = await self.translate_markdown(
                        preview_markdown, target_lang
                    )
                except Exception as e:
                    logger.warning("Translation fallback failed: %s", e)

            result = OptimizationResult(
                score=core_result.score,
                missing_keywords=core_result.missing_keywords,
                covered_keywords=core_result.covered_keywords,
                change_log=core_result.change_log,
                preview_markdown=preview_markdown,
                detected_resume_lang=None,
                detected_jd_lang=None,
                extracted_entities=entities,
                alignment_insights=alignment,
            )
        else:
            result = OptimizationResult(
                score=0,
                missing_keywords=[],
                covered_keywords=[],
                change_log=["Error: Failed to parse LLM response after retries"],
                preview_markdown=resume_text,
                detected_resume_lang=None,
                detected_jd_lang=None,
                extracted_entities=entities,
                alignment_insights=alignment,
            )

        logger.info(
            f"Optimization complete: score={result.score}, "
            f"latency={self.metrics.latency_seconds}s, "
            f"invalid_attempts={self.metrics.invalid_json_attempts}"
        )

        return result, self.metrics
