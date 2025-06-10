import unittest
from src.email_audit.llm.base_llm import BaseLLM
from pydantic import BaseModel
from typing import Optional, Union

class MockLLM(BaseLLM):
    async def ainvoke(self, prompt: str, schema: Optional[type[BaseModel]] = None) -> Optional[Union[BaseModel, str]]:
        if schema:
            # Create a dummy instance of the schema if it has no required fields
            # or handle specific test schemas appropriately.
            # For a generic case, if schema has no args, schema() works.
            # If it has required fields, this would fail without defaults.
            # For this test, we assume it's a simple schema or this part isn't the focus.
            try:
                return schema()
            except Exception: # If schema() fails due to missing required fields
                # Fallback for complex schemas in a generic mock, consider a more specific mock if needed
                class DummyModel(BaseModel):
                    message: str = "dummy model for complex schema"
                return DummyModel()
        return "test response"

class TestBaseLLM(unittest.TestCase):
    def test_base_llm_creation(self):
        llm = MockLLM(api_key="test_key", model_name="test_model", temperature=0.5)
        self.assertEqual(llm.api_key, "test_key")
        self.assertEqual(llm.model_name, "test_model")
        self.assertEqual(llm.temperature, 0.5)

if __name__ == '__main__':
    unittest.main()
