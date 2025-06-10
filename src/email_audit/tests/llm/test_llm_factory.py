import unittest
from unittest.mock import patch
import os

from src.email_audit.llm.llm_factory import LLMFactory
from src.email_audit.llm.openai_llm import OpenAILLM
from src.email_audit.llm.anthropic_llm import AnthropicLLM

class TestLLMFactory(unittest.TestCase):

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key", "ANTHROPIC_API_KEY": "fake_key"}, clear=True)
    def test_create_openai_llm(self):
        llm = LLMFactory.create_llm(provider="openai", model_name="gpt-test-factory", temperature=0.3)
        self.assertIsInstance(llm, OpenAILLM)
        self.assertEqual(llm.model_name, "gpt-test-factory")
        self.assertEqual(llm.temperature, 0.3)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key", "ANTHROPIC_API_KEY": "fake_key"}, clear=True)
    def test_create_anthropic_llm(self):
        llm = LLMFactory.create_llm(provider="anthropic", model_name="claude-test-factory", temperature=0.4)
        self.assertIsInstance(llm, AnthropicLLM)
        self.assertEqual(llm.model_name, "claude-test-factory")
        self.assertEqual(llm.temperature, 0.4)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key", "ANTHROPIC_API_KEY": "fake_key"}, clear=True)
    def test_create_llm_case_insensitive_provider(self):
        llm_openai = LLMFactory.create_llm(provider="OpenAI", model_name="gpt-test-case", temperature=0.1)
        self.assertIsInstance(llm_openai, OpenAILLM)
        llm_anthropic = LLMFactory.create_llm(provider="Anthropic", model_name="claude-test-case", temperature=0.2)
        self.assertIsInstance(llm_anthropic, AnthropicLLM)

    def test_create_unsupported_provider(self):
        with self.assertRaises(ValueError) as context:
            LLMFactory.create_llm(provider="unsupported", model_name="test", temperature=0.5)
        self.assertIn("Unsupported LLM provider: unsupported", str(context.exception))

if __name__ == '__main__':
    unittest.main()
