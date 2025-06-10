import unittest
from unittest.mock import patch, AsyncMock
from pydantic import BaseModel, Field
from anthropic.types import Message, TextBlock

from src.email_audit.llm.anthropic_llm import AnthropicLLM
import os

class SampleSchema(BaseModel):
    item: str = Field(..., description="Name of the item")
    quantity: int = Field(..., description="Quantity of the item")

class TestAnthropicLLM(unittest.IsolatedAsyncioTestCase):

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake_anthropic_key"}, clear=True)
    def setUp(self):
        self.llm = AnthropicLLM(model_name="claude-test", temperature=0.2)

    @patch.dict(os.environ, {}, clear=True)
    def test_init_no_api_key(self):
        with self.assertRaises(ValueError) as context:
            AnthropicLLM()
        self.assertIn("Anthropic API key not found", str(context.exception))

    @patch('anthropic.AsyncAnthropic')
    async def test_ainvoke_string_output(self, MockAsyncAnthropic):
        mock_client = MockAsyncAnthropic.return_value
        mock_response_message = Message(
            id="msg-xxxx",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text="Hello from Anthropic!")],
            model="claude-test",
            stop_reason="end_turn",
            stop_sequence=None,
            usage={"input_tokens": 10, "output_tokens": 10}
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response_message)

        response = await self.llm.ainvoke("Anthropic test prompt")
        self.assertEqual(response, "Hello from Anthropic!")
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertEqual(call_args['messages'][0]['content'], "Anthropic test prompt")
        self.assertIsNone(call_args['system']) # No schema, so no system prompt

    @patch('anthropic.AsyncAnthropic')
    async def test_ainvoke_structured_output_success(self, MockAsyncAnthropic):
        mock_client = MockAsyncAnthropic.return_value
        response_text = '{"item": "Widget", "quantity": 100}'
        mock_response_message = Message(
            id="msg-yyyy",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text=response_text)],
            model="claude-test",
            stop_reason="end_turn",
            stop_sequence=None,
            usage={"input_tokens": 10, "output_tokens": 20}
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response_message)

        response = await self.llm.ainvoke("Anthropic schema prompt", schema=SampleSchema)
        self.assertIsInstance(response, SampleSchema)
        self.assertEqual(response.item, "Widget")
        self.assertEqual(response.quantity, 100)
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        self.assertIn("JSON format", call_args['system']) # System prompt should request JSON

    @patch('anthropic.AsyncAnthropic')
    async def test_ainvoke_structured_output_json_malformed(self, MockAsyncAnthropic):
        mock_client = MockAsyncAnthropic.return_value
        response_text = '{"item": "Gadget", "quantity": "not_an_integer"}' # Malformed
        mock_response_message = Message(
            id="msg-zzzz",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text=response_text)],
            model="claude-test",
            stop_reason="end_turn",
            stop_sequence=None,
            usage={"input_tokens": 10, "output_tokens": 20}
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response_message)
        # Expecting raw string due to Pydantic error being logged and raw returned by LLM class
        response = await self.llm.ainvoke("Anthropic schema error prompt", schema=SampleSchema)
        self.assertEqual(response, response_text)

    @patch('anthropic.AsyncAnthropic')
    async def test_ainvoke_structured_output_with_markdown_fences(self, MockAsyncAnthropic):
        mock_client = MockAsyncAnthropic.return_value
        response_text = '```json\n{"item": "Gizmo", "quantity": 75}\n```'
        mock_response_message = Message(
            id="msg-aaaa",
            type="message",
            role="assistant",
            content=[TextBlock(type="text", text=response_text)],
            model="claude-test",
            stop_reason="end_turn",
            stop_sequence=None,
            usage={"input_tokens": 10, "output_tokens": 25}
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response_message)

        response = await self.llm.ainvoke("Anthropic schema with fences", schema=SampleSchema)
        self.assertIsInstance(response, SampleSchema)
        self.assertEqual(response.item, "Gizmo")
        self.assertEqual(response.quantity, 75)

if __name__ == '__main__':
    unittest.main()
