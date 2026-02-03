"""
Anthropic Claude LLM Provider.

Uses Claude models for resume optimization.
"""

import json
from typing import Optional, Type, Union

import anthropic
from libs.common import get_settings
from pydantic import BaseModel

from .base import BaseLLMProvider

settings = get_settings()


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None)
        if not api_key:
            self.client = None
        else:
            self.client = anthropic.AsyncAnthropic(api_key=api_key)

        # Use Claude 3.5 Sonnet for best balance of speed and quality
        self.model_name = "claude-sonnet-4-20250514"

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
    ) -> Union[str, BaseModel]:
        if not self.client:
            raise ValueError("Anthropic API Key not configured")

        # Add JSON instruction if schema is provided
        if json_schema:
            schema_json = json_schema.model_json_schema()
            system_prompt = f"""{system_prompt}

You MUST respond with valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Respond ONLY with the JSON object, no additional text."""

        message = await self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
        )

        text_response = message.content[0].text

        if json_schema:
            # Clean up response (remove markdown code blocks if present)
            cleaned_text = text_response.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            return json_schema.model_validate_json(cleaned_text)

        return text_response

    async def get_embedding(self, text: str) -> list[float]:
        """Anthropic doesn't provide embeddings API, return empty list."""
        # For embeddings, you'd need to use a different provider like OpenAI
        # or a local embedding model
        return []
