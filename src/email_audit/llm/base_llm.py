import abc
import os
from typing import Optional, Type
from pydantic import BaseModel

class BaseLLM(abc.ABC):
    def __init__(self, api_key: Optional[str], model_name: str, temperature: float):
        """
        Initializes the base LLM.

        Args:
            api_key: The API key for the LLM provider. If None, it will be fetched from the environment variable.
            model_name: The name of the model to use.
            temperature: The temperature to use for generation.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature

    @abc.abstractmethod
    async def ainvoke(self, prompt: str, schema: Optional[Type[BaseModel]] = None) -> Optional[BaseModel | str]:
        """
        Invokes the language model with the given prompt.

        Args:
            prompt: The prompt to send to the model.
            schema: An optional Pydantic schema. If provided, the LLM is expected
                    to return a response that can be parsed into this schema.
                    If not provided, the LLM should return a string.

        Returns:
            A Pydantic model instance if a schema is provided and parsing is successful,
            or a string if no schema is provided or parsing fails (though ideally,
            implementations should try to enforce schema compliance or handle errors).
            Returns None if the invocation fails.
        """
        pass

    @staticmethod
    def _get_env_var(name: str) -> Optional[str]:
        """Helper to get environment variables."""
        return os.getenv(name)
