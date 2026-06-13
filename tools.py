"""
tools.py

FitFindr tools — each is a standalone function callable and testable independently.

Tools:
    search_listings(description, size, max_price)       → list[dict] | None
    suggest_outfit(new_item, wardrobe)                  → str | None
    create_fit_card(outfit, new_item)                   → str | None
    price_comparison(item)                              → dict | None
    style_profile(action, profile)                      → dict
    popular_trends(category, size)                      → list[str]
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()                        # project root .env
load_dotenv("venv/.env", override=False)  # fallback for venv/.env location

_GROQ_MODEL = "llama-3.3-70b-versatile"


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict] | None:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for.
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts sorted by relevance (best match first),
        or an empty list if nothing matches.
        Returns None if the data file cannot be loaded.

    Each listing dict has: id, title, description, category, style_tags (list),
    size, condition, price (float), colors (list), brand, platform.
    """
    try:
        listings = load_listings()
    except Exception:
        return None

    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    if size is not None:
        size_lower = size.lower()
        listings = [l for l in listings if size_lower in l["size"].lower()]

    keywords = set(description.lower().split())

    def _score(listing: dict) -> int:
        text = " ".join([
            listing["title"],
            listing["description"],
            listing["category"],
            " ".join(listing["style_tags"]),
            listing.get("brand") or "",
        ]).lower()
        return sum(1 for kw in keywords if kw in text)

    scored = [(s, l) for l in listings if (s := _score(l)) > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str | None:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key. May be empty.

    Returns:
        A string with outfit suggestions, or None if the wardrobe is empty
        or no strong pairing can be suggested.
    """
    items = wardrobe.get("items", [])
    if not items:
        return None

    wardrobe_lines = "\n".join(
        f"- {item['name']} ({item['category']}, tags: {', '.join(item['style_tags'])})"
        + (f" — {item['notes']}" if item.get("notes") else "")
        for item in items
    )

    prompt = (
        f"You are a thrift fashion stylist. A user found this secondhand item on {new_item['platform']}:\n\n"
        f"Item: {new_item['title']}\n"
        f"Description: {new_item['description']}\n"
        f"Style tags: {', '.join(new_item['style_tags'])}\n"
        f"Colors: {', '.join(new_item['colors'])}\n"
        f"Category: {new_item['category']}\n\n"
        f"Their existing wardrobe:\n{wardrobe_lines}\n\n"
        "Suggest 1–2 complete outfit combinations using this new item paired with "
        "specific pieces from their wardrobe. Name the exact wardrobe pieces. "
        "Keep it concise and practical."
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )
    result = response.choices[0].message.content.strip()
    return result if result else None


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str | None:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence caption string, or None if outfit is empty/missing.
    """
    if not outfit or not outfit.strip():
        return None

    prompt = (
        "Write a 2–4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
        f"Thrifted item: {new_item['title']} — ${new_item['price']} on {new_item['platform']}\n"
        f"Outfit: {outfit}\n\n"
        "Rules:\n"
        "- Casual and authentic, like a real OOTD post — not a product description\n"
        "- Mention the item name, price, and platform naturally (once each)\n"
        "- Capture the outfit vibe in specific terms\n"
        "- No hashtags"
    )

    client = _get_groq_client()
    response = client.chat.completions.create(
        model=_GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=200,
    )
    result = response.choices[0].message.content.strip()
    return result if result else None


# ── Tool 4: price_comparison ──────────────────────────────────────────────────

def price_comparison(item: dict) -> dict | None:
    """
    Estimate whether the item's price is fair compared to similar listings.

    Args:
        item: A listing dict from search_listings().

    Returns:
        A dict with:
            verdict (str):                  "good deal", "fair", or "overpriced"
            avg_price (float):              average price of comparable listings
            cheaper_alternatives (list):    up to 2 cheaper listings with similar tags
        Returns None if no comparable listings exist.
    """
    try:
        listings = load_listings()
    except Exception:
        return None

    item_tags = set(item.get("style_tags", []))
    comparables = [
        l for l in listings
        if l["id"] != item["id"]
        and l["category"] == item["category"]
        and item_tags & set(l.get("style_tags", []))
    ]

    if not comparables:
        return None

    avg_price = sum(l["price"] for l in comparables) / len(comparables)
    diff = (item["price"] - avg_price) / avg_price

    if diff < -0.20:
        verdict = "good deal"
    elif diff > 0.20:
        verdict = "overpriced"
    else:
        verdict = "fair"

    cheaper = sorted(
        [l for l in comparables if l["price"] < item["price"]],
        key=lambda l: l["price"],
    )[:2]

    return {
        "verdict": verdict,
        "avg_price": round(avg_price, 2),
        "cheaper_alternatives": cheaper,
    }


# ── Tool 5: style_profile ─────────────────────────────────────────────────────

_profile_store: dict = {}


def style_profile(action: str, profile: dict | None = None) -> dict:
    """
    Save or load a user's style preferences within the session.

    Args:
        action:  "save" to store a profile, "load" to retrieve it.
        profile: Dict with keys size (str), preferred_tags (list[str]),
                 preferred_categories (list[str]). Required when action="save".

    Returns:
        The stored profile dict, or an empty template if no profile exists.
    """
    global _profile_store

    empty = {"size": None, "preferred_tags": [], "preferred_categories": []}

    if action == "save" and profile:
        _profile_store = profile
        return _profile_store

    if action == "load":
        return _profile_store if _profile_store else empty

    return empty


# ── Tool 6: popular_trends ────────────────────────────────────────────────────

def popular_trends(
    category: str | None = None,
    size: str | None = None,
) -> list[str]:
    """
    Return the top trending style tags across the listings dataset,
    optionally filtered by category and size.

    Args:
        category: Listing category to filter by, or None for all categories.
        size:     Size string to filter by (case-insensitive), or None for all sizes.

    Returns:
        A list of up to 5 trending style tag strings, sorted by frequency.
        Returns an empty list if no listings match the filters or data cannot load.
    """
    try:
        listings = load_listings()
    except Exception:
        return []

    if category:
        listings = [l for l in listings if l["category"] == category]
    if size:
        size_lower = size.lower()
        listings = [l for l in listings if size_lower in l["size"].lower()]

    if not listings:
        return []

    tag_counts: dict[str, int] = {}
    for listing in listings:
        for tag in listing.get("style_tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return sorted(tag_counts, key=lambda t: tag_counts[t], reverse=True)[:5]
