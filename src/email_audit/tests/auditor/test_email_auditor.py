import unittest
from unittest.mock import patch, MagicMock
import os

# Assuming EmailAuditor is in src.email_audit.auditor.email_auditor
from src.email_audit.auditor.email_auditor import EmailAuditor
from src.email_audit.llm.openai_llm import OpenAILLM
from src.email_audit.llm.anthropic_llm import AnthropicLLM

class TestEmailAuditorInit(unittest.TestCase):

    @patch.dict(os.environ, {
        "PRIMARY_LLM_PROVIDER": "openai",
        "OPENAI_PRIMARY_MODEL": "gpt-primary",
        "OPENAI_API_KEY": "fake_openai", # Needed by OpenAILLM constructor
        "REASONING_LLM_PROVIDER": "anthropic",
        "ANTHROPIC_REASONING_MODEL": "claude-reasoning",
        "ANTHROPIC_API_KEY": "fake_anthropic", # Needed by AnthropicLLM constructor
        "DETAIL_LLM_PROVIDER": "openai",
        "OPENAI_DETAIL_MODEL": "gpt-detail",
    }, clear=True)
    @patch('src.email_audit.llm.llm_factory.LLMFactory.create_llm')
    def test_init_llm_configuration(self, mock_create_llm):
        # Mock the return values for create_llm
        # It's important that these mock instances are distinguishable
        mock_openai_primary = OpenAILLM(api_key="fake_openai", model_name="gpt-primary", temperature=0.0)
        mock_anthropic_reasoning = AnthropicLLM(api_key="fake_anthropic", model_name="claude-reasoning", temperature=0.3)
        mock_openai_detail = OpenAILLM(api_key="fake_openai", model_name="gpt-detail", temperature=0.1)

        # Side effect to return different mocks based on provider and model
        def side_effect_func(provider, model_name, temperature, api_key=None): # api_key is passed by factory
            if provider == "openai" and model_name == "gpt-primary" and temperature == 0.0:
                return mock_openai_primary
            elif provider == "anthropic" and model_name == "claude-reasoning" and temperature == 0.3:
                return mock_anthropic_reasoning
            elif provider == "openai" and model_name == "gpt-detail" and temperature == 0.1:
                return mock_openai_detail
            # Fallback for unexpected calls, useful for debugging tests
            m = MagicMock()
            m.provider = provider
            m.model_name = model_name
            m.temperature = temperature
            # raise ValueError(f"Unexpected call to mock_create_llm: provider='{provider}', model_name='{model_name}', temperature={temperature}")
            return m # Return a generic mock if no conditions match, to make debugging easier.

        mock_create_llm.side_effect = side_effect_func

        auditor = EmailAuditor()

        self.assertEqual(mock_create_llm.call_count, 3)

        # Check calls to factory
        # Using assert_any_call because the order of LLM initialization in EmailAuditor might not be guaranteed
        # if it iterates over a dictionary or similar for different LLM roles.
        # However, the current implementation initializes them sequentially.
        mock_create_llm.assert_any_call(provider="openai", model_name="gpt-primary", temperature=0.0)
        mock_create_llm.assert_any_call(provider="anthropic", model_name="claude-reasoning", temperature=0.3)
        mock_create_llm.assert_any_call(provider="openai", model_name="gpt-detail", temperature=0.1)

        self.assertIs(auditor.primary_llm, mock_openai_primary)
        self.assertIs(auditor.reasoning_llm, mock_anthropic_reasoning)
        self.assertIs(auditor.detail_llm, mock_openai_detail)

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "fake_openai_key_default",
        "ANTHROPIC_API_KEY": "fake_anthropic_key_default"
        # Other _PROVIDER and _MODEL env vars are deliberately not set to test defaults
    }, clear=True)
    @patch('src.email_audit.llm.llm_factory.LLMFactory.create_llm')
    def test_init_llm_default_providers_and_models(self, mock_create_llm):

        # This side effect will be called by LLMFactory.create_llm
        # It should simulate returning a real LLM instance based on input.
        def side_effect_default(provider, model_name, temperature, api_key=None):
            if provider == "openai":
                # The factory passes api_key=None, so the LLM class will try to load from env.
                # We've patched os.environ to include the fake keys.
                return OpenAILLM(api_key=os.getenv("OPENAI_API_KEY"), model_name=model_name, temperature=temperature)
            elif provider == "anthropic":
                return AnthropicLLM(api_key=os.getenv("ANTHROPIC_API_KEY"), model_name=model_name, temperature=temperature)
            raise ValueError(f"Unexpected provider for default test: {provider}")

        mock_create_llm.side_effect = side_effect_default

        auditor = EmailAuditor() # This will call the factory, which calls our side_effect

        self.assertEqual(mock_create_llm.call_count, 3)
        # Based on EmailAuditor's defaults if env vars are not set:
        # primary_llm_provider defaults to 'openai', model to DEFAULT_OPENAI_PRIMARY_MODEL ("gpt-4")
        # reasoning_llm_provider defaults to 'openai', model to DEFAULT_OPENAI_REASONING_MODEL ("gpt-4")
        # detail_llm_provider defaults to 'openai', model to DEFAULT_OPENAI_DETAIL_MODEL ("gpt-4")
        mock_create_llm.assert_any_call(provider="openai", model_name="gpt-4", temperature=0.0)
        mock_create_llm.assert_any_call(provider="openai", model_name="gpt-4", temperature=0.3)
        mock_create_llm.assert_any_call(provider="openai", model_name="gpt-4", temperature=0.1)

        self.assertIsInstance(auditor.primary_llm, OpenAILLM)
        self.assertEqual(auditor.primary_llm.model_name, "gpt-4")
        self.assertEqual(auditor.primary_llm.temperature, 0.0)
        self.assertTrue(auditor.primary_llm.api_key, "fake_openai_key_default")


        self.assertIsInstance(auditor.reasoning_llm, OpenAILLM)
        self.assertEqual(auditor.reasoning_llm.model_name, "gpt-4")
        self.assertEqual(auditor.reasoning_llm.temperature, 0.3)
        self.assertTrue(auditor.reasoning_llm.api_key, "fake_openai_key_default")

        self.assertIsInstance(auditor.detail_llm, OpenAILLM)
        self.assertEqual(auditor.detail_llm.model_name, "gpt-4")
        self.assertEqual(auditor.detail_llm.temperature, 0.1)
        self.assertTrue(auditor.detail_llm.api_key, "fake_openai_key_default")


if __name__ == '__main__':
    unittest.main()
