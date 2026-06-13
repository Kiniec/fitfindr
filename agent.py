"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import (
    create_fit_card,
    popular_trends,
    price_comparison,
    search_listings,
    style_profile,
    suggest_outfit,
)


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "style_profile": {},         # loaded user style preferences (size, preferred tags/categories)
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit and price_comparison
        "wardrobe": wardrobe,        # user's wardrobe dict
        "price_verdict": None,       # dict from price_comparison: verdict, avg_price, cheaper_alternatives
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "trending_tags": [],         # list[str] of trending style tags from popular_trends
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── query parser ─────────────────────────────────────────────────────────────

def _parse_query(query: str, profile: dict) -> dict:
    """
    Extract description, size, and max_price from a natural language query.
    Falls back to values stored in the style profile when the query omits them.

    Returns a dict with keys: description (str), size (str|None), max_price (float|None).
    """
    text = query.lower()

    # max_price — matches "under $30", "under 30", "less than $25", "max $40"
    price_match = re.search(
        r'(?:under|less than|max(?:imum)?)\s+\$?(\d+(?:\.\d+)?)', text
    )
    max_price = float(price_match.group(1)) if price_match else None

    # size — matches "size M", "size XL", or a standalone token (S/M/L/XL/XXL etc.)
    # Negative lookbehind (?<![a-z0-9']) blocks matches inside contractions
    # (e.g. "what's") and inside longer words (e.g. "sneakers", "mostly").
    size_match = re.search(
        r'\bsize\s+([a-z0-9/]+)\b|(?<![a-z0-9\'])(x{0,2}s|x{0,2}l|x{0,3}l|s/m|m/l|small|medium|large)(?![a-z0-9])',
        text,
    )
    if size_match:
        raw = (size_match.group(1) or size_match.group(2)).strip()
        size = raw.upper()
    else:
        size = profile.get("size")  # fall back to saved profile

    # description — strip price and size clauses, filler phrases, then normalise
    description = re.sub(
        r'(?:under|less than|max(?:imum)?)\s+\$?\d+(?:\.\d+)?', '', text
    )
    description = re.sub(
        r'\bsize\s+[a-z0-9/]+|(?<![a-z0-9\'])(?:x{0,2}s|x{0,2}l|x{0,3}l|s/m|m/l|small|medium|large)(?![a-z0-9])',
        '', description,
    )
    description = re.sub(
        r"\b(?:i'?m?\s+)?(?:looking for|searching for|find me|show me|i want)\b",
        '', description,
    )
    description = ' '.join(description.split()).strip()

    return {"description": description, "size": size, "max_price": max_price}


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)

    # Step 1 — load style profile; use saved size/tags as fallback defaults
    session["style_profile"] = style_profile("load")

    # Step 2 — parse the query into description, size, max_price
    session["parsed"] = _parse_query(query, session["style_profile"])

    # Step 3 — search listings, with up to two retries loosening constraints
    desc = session["parsed"]["description"]
    size = session["parsed"]["size"]
    max_price = session["parsed"]["max_price"]

    results = search_listings(desc, size=size, max_price=max_price)

    if results is None:
        session["error"] = "Something went wrong loading listings. Please try again."
        return session

    if not results and size is not None:
        results = search_listings(desc, size=None, max_price=max_price)

    if not results and max_price is not None:
        results = search_listings(desc, size=None, max_price=None)

    if not results:
        parts = []
        if max_price is not None:
            parts.append(f"under ${max_price:.0f}")
        if size is not None:
            parts.append(f"in size {size}")
        qualifier = " " + " ".join(parts) if parts else ""
        session["error"] = (
            f"No listings found{qualifier}. Want me to broaden the search?"
        )
        return session

    session["search_results"] = results
    session["selected_item"] = results[0]

    # Step 4 — price comparison (optional; skip gracefully if no comparables)
    session["price_verdict"] = price_comparison(session["selected_item"])

    # Step 5 — suggest outfit
    item = session["selected_item"]
    if not wardrobe.get("items"):
        session["error"] = (
            "Your wardrobe is empty — add items or I can style this piece on its own."
        )
        return session

    session["outfit_suggestion"] = suggest_outfit(item, wardrobe)

    if session["outfit_suggestion"] is None:
        session["error"] = (
            "No strong match in your wardrobe for this item. "
            "Try adding more pieces, or broaden the style tags."
        )
        return session

    # Step 6 — popular trends (optional); flag trending tags in the outfit context
    session["trending_tags"] = popular_trends(
        category=item.get("category"),
        size=item.get("size"),
    )
    outfit_context = session["outfit_suggestion"]
    if session["trending_tags"]:
        shared = set(item.get("style_tags", [])) & set(session["trending_tags"])
        if shared:
            outfit_context = (
                f"[Trending now: {', '.join(shared)}] " + outfit_context
            )

    # Step 7 — create fit card
    session["fit_card"] = create_fit_card(outfit_context, item)

    if session["fit_card"] is None:
        session["error"] = "I couldn't build a fit card — outfit data is incomplete."
        return session

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
