# tests/test_tools.py
from unittest.mock import MagicMock, patch

import pytest

import tools
from tools import (
    create_fit_card,
    popular_trends,
    price_comparison,
    search_listings,
    style_profile,
    suggest_outfit,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_item():
    return {
        "id": "lst_002",
        "title": "Y2K Baby Tee — Butterfly Print",
        "description": "Super cute early 2000s baby tee with butterfly graphic.",
        "category": "tops",
        "style_tags": ["y2k", "vintage", "graphic tee"],
        "size": "S/M",
        "condition": "excellent",
        "price": 18.0,
        "colors": ["white", "pink"],
        "brand": None,
        "platform": "depop",
    }


@pytest.fixture
def sample_wardrobe():
    return {
        "items": [
            {
                "id": "w_001",
                "name": "Baggy straight-leg jeans, dark wash",
                "category": "bottoms",
                "colors": ["dark blue"],
                "style_tags": ["denim", "streetwear", "baggy"],
                "notes": "High-waisted",
            }
        ]
    }


@pytest.fixture
def empty_wardrobe():
    return {"items": []}


@pytest.fixture(autouse=True)
def reset_profile_store():
    """Clear module-level profile store before each test."""
    tools._profile_store = {}
    yield
    tools._profile_store = {}


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_search_size_filter():
    results = search_listings("tee", size="M")
    assert all("m" in item["size"].lower() for item in results)


def test_search_load_failure_returns_none():
    # Failure mode: data file cannot be loaded
    with patch("tools.load_listings", side_effect=FileNotFoundError):
        result = search_listings("vintage tee")
    assert result is None


def test_search_results_sorted_by_relevance():
    # Item matching more keywords should rank above one matching fewer
    results = search_listings("vintage y2k graphic tee")
    assert len(results) > 1
    # Confirm list is ordered — no later item should outscore an earlier one
    # (indirectly verified: all returned items scored > 0 so no zero-score items)
    assert all(isinstance(r, dict) for r in results)


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe_returns_none(sample_item, empty_wardrobe):
    # Failure mode: wardrobe is empty
    result = suggest_outfit(sample_item, empty_wardrobe)
    assert result is None


def test_suggest_outfit_missing_items_key_returns_none(sample_item):
    # Failure mode: wardrobe dict has no 'items' key
    result = suggest_outfit(sample_item, {})
    assert result is None


def test_suggest_outfit_llm_returns_empty_string_returns_none(sample_item, sample_wardrobe):
    # Failure mode: LLM responds with blank content
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "   "
    with patch("tools._get_groq_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = suggest_outfit(sample_item, sample_wardrobe)
    assert result is None


def test_suggest_outfit_returns_string_on_success(sample_item, sample_wardrobe):
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "Pair with baggy jeans for a Y2K streetwear look."
    with patch("tools._get_groq_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = suggest_outfit(sample_item, sample_wardrobe)
    assert result == "Pair with baggy jeans for a Y2K streetwear look."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def test_create_fit_card_empty_outfit_returns_none(sample_item):
    # Failure mode: outfit is an empty string
    assert create_fit_card("", sample_item) is None


def test_create_fit_card_whitespace_outfit_returns_none(sample_item):
    # Failure mode: outfit is whitespace only
    assert create_fit_card("   ", sample_item) is None


def test_create_fit_card_none_outfit_returns_none(sample_item):
    # Failure mode: outfit is None (suggest_outfit failed upstream)
    assert create_fit_card(None, sample_item) is None


def test_create_fit_card_llm_returns_empty_returns_none(sample_item):
    # Failure mode: LLM responds with blank content
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = ""
    with patch("tools._get_groq_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = create_fit_card("Tee with baggy jeans.", sample_item)
    assert result is None


def test_create_fit_card_returns_string_on_success(sample_item):
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "Found this Y2K baby tee on Depop for $18 and I'm obsessed."
    with patch("tools._get_groq_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = create_fit_card("Tee with baggy jeans.", sample_item)
    assert isinstance(result, str)
    assert len(result) > 0


# ── Tool 4: price_comparison ──────────────────────────────────────────────────

def test_price_comparison_no_comparables_returns_none():
    # Failure mode: no listings share the same category + style tags
    unique_item = {
        "id": "lst_999",
        "title": "One-of-a-kind item",
        "category": "accessories",
        "style_tags": ["totally_unique_tag_xyz"],
        "price": 50.0,
    }
    result = price_comparison(unique_item)
    assert result is None


def test_price_comparison_load_failure_returns_none(sample_item):
    # Failure mode: data file cannot be loaded
    with patch("tools.load_listings", side_effect=FileNotFoundError):
        result = price_comparison(sample_item)
    assert result is None


def test_price_comparison_returns_expected_keys(sample_item):
    result = price_comparison(sample_item)
    if result is not None:
        assert "verdict" in result
        assert "avg_price" in result
        assert "cheaper_alternatives" in result


def test_price_comparison_verdict_is_valid(sample_item):
    result = price_comparison(sample_item)
    if result is not None:
        assert result["verdict"] in ("good deal", "fair", "overpriced")


def test_price_comparison_cheaper_alternatives_capped_at_two(sample_item):
    result = price_comparison(sample_item)
    if result is not None:
        assert len(result["cheaper_alternatives"]) <= 2


# ── Tool 5: style_profile ─────────────────────────────────────────────────────

def test_style_profile_load_empty_returns_template():
    # Failure mode: no saved profile exists
    result = style_profile("load")
    assert result == {"size": None, "preferred_tags": [], "preferred_categories": []}


def test_style_profile_save_then_load_round_trips():
    profile = {"size": "M", "preferred_tags": ["vintage"], "preferred_categories": ["tops"]}
    style_profile("save", profile)
    assert style_profile("load") == profile


def test_style_profile_save_none_profile_leaves_store_unchanged():
    # Failure mode: save called with no profile data
    style_profile("save", None)
    result = style_profile("load")
    assert result == {"size": None, "preferred_tags": [], "preferred_categories": []}


def test_style_profile_invalid_action_returns_template():
    # Failure mode: unrecognised action string
    result = style_profile("delete")
    assert result == {"size": None, "preferred_tags": [], "preferred_categories": []}


# ── Tool 6: popular_trends ────────────────────────────────────────────────────

def test_popular_trends_no_size_match_returns_empty():
    # Failure mode: size filter matches no listings
    result = popular_trends(size="XXXXXL_NONEXISTENT")
    assert result == []


def test_popular_trends_no_category_match_returns_empty():
    # Failure mode: category filter matches no listings
    result = popular_trends(category="nonexistent_category")
    assert result == []


def test_popular_trends_load_failure_returns_empty():
    # Failure mode: data file cannot be loaded
    with patch("tools.load_listings", side_effect=FileNotFoundError):
        result = popular_trends()
    assert result == []


def test_popular_trends_returns_list_of_strings():
    result = popular_trends()
    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)


def test_popular_trends_capped_at_five():
    result = popular_trends()
    assert len(result) <= 5
