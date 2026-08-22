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

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        if not model_name or "gemini" not in model_name.lower():
            self.model_name = "gemini-1.5-flash"
        else:
            self.model_name = model_name
        logger.info(f"Initialized Live Gemini Provider using model '{self.model_name}'")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        full_text = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": full_text}]}]
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.post(url, json=payload)
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            return ""

    def extract_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        import httpx
        import re
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        sys_instruction = (system_prompt or "") + "\nOutput MUST be valid raw JSON format only. No markdown formatting."
        payload = {
            "contents": [{"parts": [{"text": f"{sys_instruction}\n\n{prompt}"}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.post(url, json=payload)
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw_text.strip(), flags=re.MULTILINE)
                return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Gemini extract_json error: {e}")
            return {}


def get_llm_provider() -> LLMProvider:
    provider_type = settings.LLM_PROVIDER.lower()
    
    # 1. Gemini
    if settings.GEMINI_API_KEY or provider_type == "gemini":
        if settings.GEMINI_API_KEY:
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model_name=settings.LLM_MODEL if "gemini" in settings.LLM_MODEL.lower() else "gemini-1.5-flash"
            )

    # 2. OpenAI
    if settings.OPENAI_API_KEY or provider_type == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAIProvider(model_name=settings.LLM_MODEL, api_key=settings.OPENAI_API_KEY)

    # 3. Default to zero-config MockProvider for demo simulation
    return MockProvider()
