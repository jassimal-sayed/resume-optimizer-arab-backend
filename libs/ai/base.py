from abc import ABC, abstractmethod
from typing import Optional, Type, Union

from pydantic import BaseModel


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Ensures that the worker service is decoupled from specific model libraries.
    """

    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
    ) -> Union[str, BaseModel]:
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        pass
