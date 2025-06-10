import json
import os
from typing import Optional, Type, Any, Dict
from pydantic import BaseModel, ValidationError
from anthropic import AsyncAnthropic # Use AsyncAnthropic for asynchronous operations

from .base_llm import BaseLLM
from loguru import logger

class AnthropicLLM(BaseLLM):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "claude-3-opus-20240229", temperature: float = 0.0):
        super().__init__(api_key, model_name, temperature)
        self.api_key = api_key or self._get_env_var("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable or pass it as an argument.")
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def ainvoke(self, prompt: str, schema: Optional[Type[BaseModel]] = None) -> Optional[BaseModel | str]:
        logger.debug(f"AnthropicLLM invoking model {self.model_name} with temperature {self.temperature}")
        try:
            system_prompt = ""
            if schema:
                # Instruct the model to return JSON matching the schema
                # This is a common approach for Anthropic models when specific tool use/function calling is not as mature or desired.
                schema_json = schema.model_json_schema()
                # Remove "title" from schema_json if present, as it can sometimes confuse the model
                if "title" in schema_json:
                    del schema_json["title"]

                system_prompt = (
                    "You are a helpful assistant that always responds in JSON format. "
                    "Please provide a response that strictly adheres to the following JSON schema. "
                    "Do not include any explanatory text or markdown formatting before or after the JSON object. "
                    "The entire response must be a single valid JSON object.\n"
                    f"JSON Schema:\n{json.dumps(schema_json)}"
                )
                logger.debug(f"Anthropic system prompt for schema {schema.__name__}:\n{system_prompt}")


            messages = [{"role": "user", "content": prompt}]

            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=4096, # Recommended max_tokens for Claude 3 Opus, adjust as needed
                temperature=self.temperature,
                system=system_prompt if system_prompt else None, # System prompt for structured JSON output
                messages=messages
            )

            logger.debug(f"Anthropic response: {response}")

            if response.content and isinstance(response.content, list) and len(response.content) > 0:
                # Assuming the first content block is the one we want, and it's of type TextBlock
                raw_response_content = response.content[0].text if hasattr(response.content[0], 'text') else None

                if not raw_response_content:
                    logger.warning("No text content found in Anthropic response block.")
                    return None

                logger.debug(f"Raw Anthropic response content: {raw_response_content}")

                if schema:
                    try:
                        # Attempt to parse the JSON string into the Pydantic model
                        # Remove potential markdown code block fences if the model adds them
                        cleaned_json_string = raw_response_content.strip()
                        if cleaned_json_string.startswith("```json"):
                            cleaned_json_string = cleaned_json_string[7:]
                        if cleaned_json_string.endswith("```"):
                            cleaned_json_string = cleaned_json_string[:-3]

                        cleaned_json_string = cleaned_json_string.strip()

                        data = json.loads(cleaned_json_string)
                        return schema(**data)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSONDecodeError parsing Anthropic response: {e}, content: {raw_response_content}")
                        # Fallback: return the raw string if JSON parsing fails, so it can be inspected
                        return raw_response_content
                    except ValidationError as e:
                        logger.error(f"Pydantic ValidationError for Anthropic response: {e}, content: {raw_response_content}")
                        # Fallback: return the raw string
                        return raw_response_content
                else:
                    # No schema, return the raw text content
                    return raw_response_content
            else:
                logger.warning("No content blocks found in Anthropic response.")
                return None

        except Exception as e:
            logger.error(f"Error invoking Anthropic model {self.model_name}: {e}")
            # Consider re-raising or returning a specific error object
            return None
