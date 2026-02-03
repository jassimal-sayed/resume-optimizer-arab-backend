import json
import os
from typing import Optional, Type, Union

from libs.common import get_settings
from openai import AsyncOpenAI
from pydantic import BaseModel

from .base import BaseLLMProvider

settings = get_settings()


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
    ) -> Union[str, BaseModel]:
        model = "gpt-4o"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        if json_schema:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
            )
            content = response.choices[0].message.content or "{}"
            return json_schema.model_validate_json(content)
        else:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""

    async def get_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            input=text, model="text-embedding-3-small"
        )
        return response.data[0].embedding
