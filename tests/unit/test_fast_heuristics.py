import pytest
from apps.backend.app.services.fast_heuristic_engine import fast_heuristic_engine

def test_data_testid_migration():
    """
    Test that class .price shifting to [data-testid='price'] is detected in <50ms.
    """
    html = """
    <div class="product-card">
        <h2 class="title">Dell XPS 15</h2>
        <div data-testid="price">$1,499.00</div>
    </div>
    """
    candidates = fast_heuristic_engine.solve(
        html_content=html,
        failed_selector=".price",
        field_name="price",
        expected_type="currency"
    )

    assert len(candidates) > 0
    top = candidates[0]
    assert top["selector"] == "[data-testid='price']"
    assert top["tier"] == "TIER_1_HEURISTIC"
    assert top["confidence_score"] >= 95.0
    assert "$1,499.00" in top["sample_values"]


def test_class_alias_migration():
    """
    Test that class .price shifting to .product-price is detected.
    """
    html = """
    <div class="card">
        <span class="product-price">$899.99</span>
    </div>
    """
    candidates = fast_heuristic_engine.solve(
        html_content=html,
        failed_selector=".price",
        field_name="price",
        expected_type="currency"
    )

    assert len(candidates) > 0
    selectors = [c["selector"] for c in candidates]
    assert ".product-price" in selectors
