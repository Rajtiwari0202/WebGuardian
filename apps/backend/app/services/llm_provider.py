import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from apps.backend.app.core.config import settings

logger = logging.getLogger("webguardian")

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate plain text from prompt."""
        pass

    @abstractmethod
    def extract_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate structured JSON from prompt."""
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.api_key = api_key
        # Delay import of openai to keep imports lightweight
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI error in generate: {str(e)}")
            raise e

    def extract_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt + "\nOutput MUST be valid JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as e:
            logger.error(f"OpenAI error in extract_json: {str(e)}")
            # Fallback
            return {}

class MockProvider(LLMProvider):
    def __init__(self):
        logger.info("Initializing WebGuardian Mock LLM Provider (Demo Simulation Mode)")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return "This is a mock textual response for simulation purposes."

    def extract_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        # Detect if it's querying for laptop price repair candidates
        prompt_lower = prompt.lower()
        
        # 1. Failure Triage Node Request
        if "failure" in prompt_lower or "triage" in prompt_lower:
            return {
                "severity": "CRITICAL",
                "failure_type": "DOM_DRIFT",
                "description": "The primary CSS selector for field 'price' (.price) did not extract any elements. Critical structure change suspected."
            }

        # 2. Intent Recovery Request
        elif "intent" in prompt_lower or "semantic" in prompt_lower:
            return {
                "field": "price",
                "intent": "Extract product current selling price in numeric or currency format.",
                "type": "currency"
            }

        # 3. Repair Planning (Candidate generation)
        elif "candidate" in prompt_lower or "repair planning" in prompt_lower:
            return {
                "field": "price",
                "candidates": [
                    {
                        "selector": "[data-testid='price']",
                        "strategy": "attribute_match",
                        "model_confidence": 96.4,
                        "reasoning": "Matches element tag containing text equivalent to price and possesses data-testid attribute set to price."
                    },
                    {
                        "selector": ".product-tile .amount",
                        "strategy": "structural_match",
                        "model_confidence": 84.7,
                        "reasoning": "Follows layout structure but uses classes indicating general amount."
                    },
                    {
                        "selector": "span.price-value",
                        "strategy": "semantic_match",
                        "model_confidence": 72.1,
                        "reasoning": "Contains price keyword in class name but has lower selector specificity."
                    }
                ]
            }

        # Fallback default
        return {
            "status": "success",
            "message": "Mock simulation output",
            "candidates": []
        }

def get_llm_provider() -> LLMProvider:
    provider_type = settings.LLM_PROVIDER.lower()
    if provider_type == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider(model_name=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY)
    elif provider_type == "mock":
        return MockProvider()
    else:
        # Fallback to mock and log warning
        logger.warning(f"LLM_PROVIDER '{provider_type}' not available or missing API keys. Falling back to MockProvider.")
        return MockProvider()
