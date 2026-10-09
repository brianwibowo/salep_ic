"""SALEP Agent tools — function tools for the AI agent to call."""

import json
from pathlib import Path

from agents import function_tool

from app.agent.schemas import Product

_PRODUCTS_PATH = Path(__file__).resolve().parents[2] / "data" / "products.json"
_products_cache: list[Product] | None = None


def _load_products() -> list[Product]:
    global _products_cache
    if _products_cache is None:
        with open(_PRODUCTS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _products_cache = [Product(**p) for p in raw]
    return _products_cache


@function_tool
def search_products(keyword: str) -> str:
    """Search company products/services relevant to a keyword.

    Args:
        keyword: A search term related to the prospect's needs.

    Returns:
        JSON array of matching products with id, name, and description.
    """
    keyword_lower = keyword.lower()
    products = _load_products()

    matches = []
    for product in products:
        product_text = " ".join([
            product.name.lower(),
            product.description.lower(),
            " ".join(kw.lower() for kw in product.keywords),
        ])
        if keyword_lower in product_text:
            matches.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
            })

    if not matches:
        return json.dumps({"results": [], "message": f"No products found for '{keyword}'."})

    return json.dumps({"results": matches})


@function_tool
def get_product(product_id: str) -> str:
    """Get detailed information about a specific company service.

    Args:
        product_id: The product/service ID (e.g., 'svc-001').

    Returns:
        JSON object with full product details, or error if not found.
    """
    products = _load_products()
    for product in products:
        if product.id == product_id:
            return json.dumps({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "keywords": product.keywords,
            })

    return json.dumps({"error": f"Product '{product_id}' not found."})
