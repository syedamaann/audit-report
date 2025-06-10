import unittest
from unittest.mock import patch, AsyncMock
from pydantic import BaseModel, Field
from openai.types.chat import ChatCompletionMessage, ChatCompletion
from openai.types.chat.chat_completion import Choice # Added
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

from src.email_audit.llm.openai_llm import OpenAILLM
import os

class SampleSchema(BaseModel):
    name: str = Field(..., description="Name of the person")
    age: int = Field(..., description="Age of the person")

class TestOpenAILLM(unittest.IsolatedAsyncioTestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"}, clear=True)
    def setUp(self):
        self.llm = OpenAILLM(model_name="gpt-test", temperature=0.1)

    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_api_key(self):
        with self.assertRaises(ValueError) as context:
            OpenAILLM()
        self.assertIn("OpenAI API key not found", str(context.exception))

    @patch('openai.AsyncOpenAI')
    async def test_ainvoke_string_output(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        mock_completion = ChatCompletion(
            id="chatcmpl-xxxx",
            choices=[
                Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(role="assistant", content="Hello, world!"))
            ],
            created=12345,
            model="gpt-test",
            object="chat.completion",
            system_fingerprint=None,
            usage=None
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        response = await self.llm.ainvoke("Test prompt")
        self.assertEqual(response, "Hello, world!")
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-test",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.1
        )

    @patch('openai.AsyncOpenAI')
    async def test_ainvoke_structured_output_success(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        tool_call = ChatCompletionMessageToolCall(
            id="toolcall-xxxx",
            function=Function(name="structured_output", arguments='{"name": "John Doe", "age": 30}'),
            type="function"
        )
        mock_completion = ChatCompletion(
            id="chatcmpl-yyyy",
            choices=[
                Choice(finish_reason="tool_calls", index=0, message=ChatCompletionMessage(role="assistant", content=None, tool_calls=[tool_call]))
            ],
            created=12345,
            model="gpt-test",
            object="chat.completion",
            system_fingerprint=None,
            usage=None
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        response = await self.llm.ainvoke("Test prompt for schema", schema=SampleSchema)
        self.assertIsInstance(response, SampleSchema)
        self.assertEqual(response.name, "John Doe")
        self.assertEqual(response.age, 30)
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['tools'][0]['function']['name'], "structured_output")

    @patch('openai.AsyncOpenAI')
    async def test_ainvoke_structured_output_json_malformed(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        tool_call = ChatCompletionMessageToolCall(
            id="toolcall-zzzz",
            function=Function(name="structured_output", arguments='{"name": "Jane Doe", "age": "not_an_int"}'), # Malformed age
            type="function"
        )
        mock_completion = ChatCompletion(
            id="chatcmpl-aaaa",
            choices=[
                Choice(finish_reason="tool_calls", index=0, message=ChatCompletionMessage(role="assistant", content=None, tool_calls=[tool_call]))
            ],
            created=12345,
            model="gpt-test",
            object="chat.completion",
            system_fingerprint=None,
            usage=None
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        # Expecting None due to Pydantic ValidationError logged by the LLM class
        response = await self.llm.ainvoke("Test prompt for schema error", schema=SampleSchema)
        self.assertIsNone(response)


    @patch('openai.AsyncOpenAI')
    async def test_ainvoke_no_tool_call_fallback(self, MockAsyncOpenAI):
        mock_client = MockAsyncOpenAI.return_value
        # Simulate model not making a tool call but returning JSON in content
        mock_completion = ChatCompletion(
            id="chatcmpl-bbbb",
            choices=[
                Choice(finish_reason="stop", index=0, message=ChatCompletionMessage(role="assistant", content='{"name": "Fallback Fred", "age": 45}'))
            ],
            created=12345,
            model="gpt-test",
            object="chat.completion",
            system_fingerprint=None,
            usage=None
        )
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
        response = await self.llm.ainvoke("Test prompt for schema fallback", schema=SampleSchema)
        self.assertIsInstance(response, SampleSchema)
        self.assertEqual(response.name, "Fallback Fred")
        self.assertEqual(response.age, 45)


if __name__ == '__main__':
    unittest.main()
