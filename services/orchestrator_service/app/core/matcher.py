"""
Matcher: Embedding-based similarity matching for resumes and job descriptions.

Features:
- Similarity calculation (cosine similarity)
- Weighted aggregation (skills, experience, education)
- Ranked candidate scoring
"""

import logging
from typing import Optional

import numpy as np
from libs.ai import BaseLLMProvider

logger = logging.getLogger("orchestrator.matcher")


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)

    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


class ResumeMatcher:
    """
    Embedding-based resume-job matching.

    Weights for aggregation (Chapter 5 spec):
    - Skills: 50%
    - Experience: 30%
    - Education: 20%
    """

    WEIGHTS = {
        "skills": 0.50,
        "experience": 0.30,
        "education": 0.20,
    }

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using LLM provider."""
        if not text.strip():
            return []

        try:
            embedding = await self.llm.get_embedding(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return []

    async def calculate_match_score(
        self,
        resume_skills: list[str],
        resume_experience: list[str],
        resume_education: list[str],
        job_description: str,
    ) -> dict:
        """
        Calculate weighted match score between resume components and job description.

        Returns:
            {
                "overall_score": float (0-100),
                "skills_score": float,
                "experience_score": float,
                "education_score": float,
                "breakdown": {...}
            }
        """
        # Concatenate resume sections for embedding
        skills_text = ", ".join(resume_skills) if resume_skills else ""
        experience_text = " | ".join(resume_experience) if resume_experience else ""
        education_text = ", ".join(resume_education) if resume_education else ""

        # Get embeddings
        job_embedding = await self.get_embedding(job_description)

        if not job_embedding:
            logger.warning("Could not get job description embedding")
            return {
                "overall_score": 0,
                "skills_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "error": "Failed to compute embeddings",
            }

        scores = {}

        # Calculate similarity for each component
        if skills_text:
            skills_embedding = await self.get_embedding(skills_text)
            scores["skills"] = (
                cosine_similarity(job_embedding, skills_embedding)
                if skills_embedding
                else 0
            )
        else:
            scores["skills"] = 0

        if experience_text:
            exp_embedding = await self.get_embedding(experience_text)
            scores["experience"] = (
                cosine_similarity(job_embedding, exp_embedding) if exp_embedding else 0
            )
        else:
            scores["experience"] = 0

        if education_text:
            edu_embedding = await self.get_embedding(education_text)
            scores["education"] = (
                cosine_similarity(job_embedding, edu_embedding) if edu_embedding else 0
            )
        else:
            scores["education"] = 0

        # Calculate weighted overall score (convert to 0-100 scale)
        overall = sum(scores[k] * self.WEIGHTS[k] * 100 for k in self.WEIGHTS)

        logger.info(
            f"Match scores - skills: {scores['skills']:.2f}, exp: {scores['experience']:.2f}, edu: {scores['education']:.2f}"
        )

        return {
            "overall_score": round(overall, 1),
            "skills_score": round(scores["skills"] * 100, 1),
            "experience_score": round(scores["experience"] * 100, 1),
            "education_score": round(scores["education"] * 100, 1),
            "breakdown": {
                "skills_weight": self.WEIGHTS["skills"],
                "experience_weight": self.WEIGHTS["experience"],
                "education_weight": self.WEIGHTS["education"],
            },
        }

    async def rank_candidates(
        self,
        candidates: list[dict],  # [{id, skills, experience, education}]
        job_description: str,
    ) -> list[dict]:
        """
        Rank multiple candidates against a job description.

        Returns sorted list with scores appended.
        """
        results = []

        for candidate in candidates:
            score_data = await self.calculate_match_score(
                resume_skills=candidate.get("skills", []),
                resume_experience=candidate.get("experience", []),
                resume_education=candidate.get("education", []),
                job_description=job_description,
            )

            results.append(
                {
                    "id": candidate.get("id"),
                    "name": candidate.get("name", "Unknown"),
                    **score_data,
                }
            )

        # Sort by overall score descending
        results.sort(key=lambda x: x["overall_score"], reverse=True)

        return results
