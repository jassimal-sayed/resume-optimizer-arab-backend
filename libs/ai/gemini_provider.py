import json
import os
from typing import Optional, Type, Union

from google import genai
from google.genai import types
from libs.common import get_settings
from pydantic import BaseModel

from .base import BaseLLMProvider

settings = get_settings()


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or settings.GEMINI_API_KEY
        if not api_key:
            # Optionally raise or log warning
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)

        # Use models/gemini-2.0-flash for the latest version with JSON schema support
        self.model_name = "gemini-2.0-flash"
        self.embedding_model = "text-embedding-004"

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
    ) -> Union[str, BaseModel]:
        if not self.client:
            raise ValueError("Gemini API Key not configured")

        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt,
            response_mime_type="application/json" if json_schema else "text/plain",
            response_schema=json_schema,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name, contents=user_prompt, config=config
        )

        text_response = response.text

        if json_schema:
            # The SDK handles schema validation if response_schema is passed,
            # but returning the parsed object directly depends on the SDK version capabilities.
            # Assuming we receive a JSON string or need to parse it:
            if hasattr(response, "parsed") and response.parsed:
                return response.parsed

            # Fallback manual parse if needed
            cleaned_text = (
                text_response.replace("```json", "").replace("```", "").strip()
            )
            return json_schema.model_validate_json(cleaned_text)

        return text_response

    async def get_embedding(self, text: str) -> list[float]:
        if not self.client:
            return []

        result = await self.client.aio.models.embed_content(
            model=self.embedding_model,
            contents=text,
        )
        # Verify the structure of result.embeddings
        # Usually it returns an object with an 'embedding' attribute or list of embeddings
        return result.embeddings[0].values
