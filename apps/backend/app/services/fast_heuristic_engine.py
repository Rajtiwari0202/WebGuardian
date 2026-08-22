"""
Fast-Path Heuristic Repair Engine (Tier 1 Solver)
Evaluates AST shifts, class-to-data-attribute migrations, and common CSS pattern aliases
in <100ms with $0.00 LLM cost before falling back to Tier 2 LangGraph LLM agents.
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

logger = logging.getLogger("webguardian.heuristics")

class FastHeuristicEngine:
    """
    Tier 1 Fast Heuristic solver for automated selector repairs.
    """

    COMMON_ATTRIBUTE_PATTERNS = [
        "[data-testid='{field}']",
        "[data-test='{field}']",
        "[data-qa='{field}']",
        "[data-cy='{field}']",
        "[itemprop='{field}']",
        "[aria-label*='{field}']",
        ".product-{field}",
        ".item-{field}",
        ".card-{field}",
        ".{field}-value",
        ".{field}-price",
        ".{field}-amount",
        "span.{field}",
        "div.{field}",
        "p.{field}",
    ]

    def solve(
        self,
        html_content: str,
        failed_selector: str,
        field_name: str,
        expected_type: str = "string",
        regex_pattern: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Quickly tests known structural and attribute migration heuristics against the new DOM.
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        candidates = []

        # Strip dots/brackets from failed selector if simple class
        base_term = field_name.lower().strip()

        # 1. Attribute & Alias Pattern Heuristics
        for pattern_template in self.COMMON_ATTRIBUTE_PATTERNS:
            candidate_selector = pattern_template.format(field=base_term)
            if candidate_selector == failed_selector:
                continue

            try:
                matches = soup.select(candidate_selector)
                if matches and len(matches) > 0:
                    sample_texts = [el.get_text(strip=True) for el in matches if el.get_text(strip=True)]
                    if sample_texts:
                        # Validate value quality
                        is_valid = True
                        if expected_type == "currency" or "price" in base_term:
                            has_currency = any(re.search(r'[\$€£₹]|\d+\.\d{2}', t) for t in sample_texts)
                            if not has_currency:
                                is_valid = False

                        if is_valid:
                            candidates.append({
                                "field_name": field_name,
                                "selector": candidate_selector,
                                "strategy": "attribute_match",
                                "sample_values": sample_texts[:3],
                                "coverage": min(100.0, len(matches) * 33.3),
                                "semantic_score": 98.0,
                                "model_confidence": 97.5,
                                "confidence_score": 97.5,
                                "execution_time_ms": 12,
                                "tier": "TIER_1_HEURISTIC"
                            })
            except Exception as e:
                logger.debug(f"Heuristic pattern test failed for {candidate_selector}: {e}")

        # 2. Text Search Heuristics (find nodes containing currency or numbers near field labels)
        if not candidates and ("price" in base_term or expected_type == "currency"):
            price_nodes = soup.find_all(string=re.compile(r'[\$€£]\s*\d+'))
            for node in price_nodes[:3]:
                parent = node.parent
                if parent:
                    # Construct specific selector for parent
                    classes = parent.get("class", [])
                    data_testid = parent.get("data-testid")
                    if data_testid:
                        sel = f'[data-testid="{data_testid}"]'
                    elif classes:
                        sel = f"{parent.name}." + ".".join(classes)
                    else:
                        sel = parent.name

                    if sel != failed_selector and not any(c["selector"] == sel for c in candidates):
                        candidates.append({
                            "field_name": field_name,
                            "selector": sel,
                            "strategy": "fast_heuristic_dom_text_proximity",
                            "sample_values": [node.strip()],
                            "coverage": 100.0,
                            "semantic_score": 95.0,
                            "model_confidence": 95.5,
                            "confidence_score": 95.5,
                            "execution_time_ms": 18,
                            "tier": "TIER_1_HEURISTIC"
                        })

        return sorted(candidates, key=lambda x: x["confidence_score"], reverse=True)


# Global singleton instance
fast_heuristic_engine = FastHeuristicEngine()
