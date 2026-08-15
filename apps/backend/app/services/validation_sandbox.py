import re
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

logger = logging.getLogger("webguardian")

class ValidationSandbox:
    @staticmethod
    def extract_with_selector(html_content: str, card_selector: str, field_selector: str) -> List[str]:
        """Helper to run BeautifulSoup selector extraction on cards."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            cards = soup.select(card_selector)
            if not cards:
                # Fallback: if no product cards, run selector globally
                elements = soup.select(field_selector)
                return [el.text.strip() for el in elements if el]
                
            results = []
            for card in cards:
                el = card.select_one(field_selector)
                results.append(el.text.strip() if el else None)
            return results
        except Exception as e:
            logger.error(f"Error in sandbox extraction: {str(e)}")
            return []

    @staticmethod
    def score_semantic_match(extracted_values: List[str], expected_type: str, examples: List[str]) -> float:
        """
        Calculates a semantic match score (0-100) by comparing extracted data format.
        """
        valid_items = [val for val in extracted_values if val is not None]
        if not valid_items:
            return 0.0

        score_sum = 0.0
        for val in valid_items:
            # Check price/currency types
            if expected_type == "currency" or expected_type == "price":
                # Matches patterns like $999, ₹89,999, 1,299.00
                if re.search(r'[\$\d₹\,]', val):
                    score_sum += 100.0
                elif any(char.isdigit() for char in val):
                    score_sum += 80.0
                else:
                    score_sum += 10.0
            # Numeric types
            elif expected_type == "number" or expected_type == "integer" or expected_type == "float":
                cleaned = re.sub(r'[^\d\.]', '', val)
                if cleaned:
                    score_sum += 100.0
                else:
                    score_sum += 0.0
            # Default strings
            else:
                score_sum += 100.0

        return score_sum / len(valid_items)

    @staticmethod
    def evaluate_candidate(
        html_content: str,
        card_selector: str,
        field_name: str,
        candidate_selector: str,
        strategy: str,
        model_confidence: float,
        contract: Dict[str, Any],
        old_selector: str
    ) -> Dict[str, Any]:
        """
        Runs candidate extraction, validates outcomes, and scores the strategy:
        Final Score = 30% semantic_match + 30% validation_coverage + 20% schema_validity + 10% structural_similarity + 10% model_confidence
        """
        # 1. Extract values
        extracted = ValidationSandbox.extract_with_selector(html_content, card_selector, candidate_selector)
        total_rows = len(extracted) if extracted else 0
        
        # 2. Validation Coverage (what % of rows are non-null)
        non_null_count = sum(1 for v in extracted if v is not None and v != "")
        validation_coverage = (non_null_count / total_rows * 100.0) if total_rows > 0 else 0.0
        
        # 3. Schema Validity (does it match types and constraints)
        expected_type = contract.get("type", "string")
        required = contract.get("required", False)
        
        schema_valid = True
        schema_score = 100.0
        
        if required and validation_coverage == 0.0:
            schema_valid = False
            schema_score = 0.0
        else:
            # Check type parsing for non-nulls
            for val in extracted:
                if val is not None:
                    if expected_type in ["number", "integer", "float", "currency"]:
                        # Ensure it contains digits
                        if not any(c.isdigit() for c in val):
                            schema_score = max(0.0, schema_score - 20.0)
        
        # 4. Semantic Match Score
        examples = contract.get("examples", [])
        semantic_score = ValidationSandbox.score_semantic_match(extracted, expected_type, examples)
        
        # 5. Structural Similarity Score (0-100)
        # Simply checks class/attribute overlap between new and old selector
        common_words = set(re.findall(r'\w+', old_selector)) & set(re.findall(r'\w+', candidate_selector))
        structural_similarity = 100.0 if not old_selector else (len(common_words) * 20.0)
        structural_similarity = min(100.0, max(20.0, structural_similarity))
        
        # Calculate Final Score
        final_score = (
            (0.30 * semantic_score) +
            (0.30 * validation_coverage) +
            (0.20 * schema_score) +
            (0.10 * structural_similarity) +
            (0.10 * model_confidence)
        )
        
        # Normalize and round
        final_score = round(min(100.0, max(0.0, final_score)), 2)
        
        status = "VALIDATED" if final_score >= 70.0 else "REJECTED"
        
        return {
            "selector": candidate_selector,
            "strategy": strategy,
            "model_confidence": model_confidence,
            "validation_score": validation_coverage,
            "semantic_score": semantic_score,
            "coverage_score": validation_coverage,
            "structural_similarity": structural_similarity,
            "schema_validity": schema_score,
            "final_score": final_score,
            "status": status,
            "extracted_sample": [v for v in extracted if v is not None][:3]
        }
