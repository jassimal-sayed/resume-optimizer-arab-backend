import os

from libs.common import get_settings

from .base import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider

settings = get_settings()


def get_llm_provider() -> BaseLLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic" or provider_name == "claude":
        # Lazy import to avoid requiring anthropic package when not used
        try:
            from .anthropic_provider import AnthropicProvider

            return AnthropicProvider()
        except ImportError:
            raise ImportError(
                "Anthropic provider requires the 'anthropic' package. "
                "Install it with: pip install anthropic>=0.40"
            )
    else:
        # Default fallback
        return OpenAIProvider()
