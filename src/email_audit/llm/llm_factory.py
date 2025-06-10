from typing import Optional
from .base_llm import BaseLLM
from .openai_llm import OpenAILLM
from .anthropic_llm import AnthropicLLM
from .grok_llm import GrokLLM
from .groq_llm import GroqLLM
from loguru import logger

class LLMFactory:
    @staticmethod
    def create_llm(
        provider: str,
        model_name: str,
        temperature: float,
        api_key: Optional[str] = None
    ) -> BaseLLM:
        """
        Creates an instance of a language model client.

        Args:
            provider: The LLM provider to use (e.g., "openai", "anthropic", "grok", "groq").
            model_name: The specific model name to use.
            temperature: The sampling temperature for the model.
            api_key: Optional API key. If not provided, the respective
                     LLM class will attempt to load it from environment variables.

        Returns:
            An instance of BaseLLM (OpenAILLM, AnthropicLLM, GrokLLM, or GroqLLM).

        Raises:
            ValueError: If an unsupported provider is specified.
        """
        logger.info(f"Creating LLM for provider: {provider}, model: {model_name}, temperature: {temperature}")
        provider_lower = provider.lower()

        if provider_lower == "openai":
            return OpenAILLM(api_key=api_key, model_name=model_name, temperature=temperature)
        elif provider_lower == "anthropic":
            return AnthropicLLM(api_key=api_key, model_name=model_name, temperature=temperature)
        elif provider_lower == "grok":
            return GrokLLM(api_key=api_key, model_name=model_name, temperature=temperature)
        elif provider_lower == "groq":
            return GroqLLM(api_key=api_key, model_name=model_name, temperature=temperature)
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers are 'openai', 'anthropic', 'grok', and 'groq'.")

# Example usage (optional, for testing or demonstration):
# if __name__ == "__main__":
#     # Make sure to set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables
#     # or pass them directly if you uncomment the api_key arguments.
#
#     try:
#         openai_llm = LLMFactory.create_llm(
#             provider="openai",
#             model_name="gpt-3.5-turbo", # Or your preferred model
#             temperature=0.1,
#             # api_key="your_openai_api_key_here" # Optional
#         )
#         logger.info(f"Successfully created OpenAILLM: {type(openai_llm)}")
#
#         # Example invocation (requires async context)
#         # import asyncio
#         # async def test_openai():
#         #     response = await openai_llm.ainvoke("Hello, OpenAI!")
#         #     logger.info(f"OpenAI Response: {response}")
#         # asyncio.run(test_openai())
#
#     except ValueError as e:
#         logger.error(f"Error creating OpenAI LLM: {e}")
#     except Exception as e:
#         logger.error(f"An unexpected error occurred with OpenAI: {e}")
#
#     try:
#         anthropic_llm = LLMFactory.create_llm(
#             provider="anthropic",
#             model_name="claude-3-haiku-20240307", # Or your preferred model
#             temperature=0.1,
#             # api_key="your_anthropic_api_key_here" # Optional
#         )
#         logger.info(f"Successfully created AnthropicLLM: {type(anthropic_llm)}")
#
#         # Example invocation (requires async context)
#         # import asyncio
#         # async def test_anthropic():
#         #     response = await anthropic_llm.ainvoke("Hello, Anthropic!")
#         #     logger.info(f"Anthropic Response: {response}")
#         # asyncio.run(test_anthropic())
#
#     except ValueError as e:
#         logger.error(f"Error creating Anthropic LLM: {e}")
#     except Exception as e:
#         logger.error(f"An unexpected error occurred with Anthropic: {e}")
