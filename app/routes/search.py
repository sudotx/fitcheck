from flask import Blueprint, request, jsonify
from app.services.search_service import search_service
from app.services.ai_service import ai_service
from app.utils.decorators import handle_errors
from flask_jwt_extended import get_jwt_identity, jwt_required

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
@handle_errors
def search_items():
    """
    Search for clothing items with various filters and sorting options.

    Query Parameters:
    - q: Search query string
    - category: Filter by category (e.g., tops, bottoms, shoes)
    - color: Filter by color
    - brand: Filter by brand
    - min_price: Minimum price
    - max_price: Maximum price
    - sort: Sort field (e.g., price, created_at)
    - order: Sort order (asc or desc)
    - page: Page number for pagination
    - per_page: Items per page

    Returns:
    - JSON response with search results and facets
    """
    # Get search parameters
    query = request.args.get("q", "")
    category = request.args.get("category")
    color = request.args.get("color")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if color:
        filters["color"] = color
    if brand:
        filters["brand"] = brand
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price

    # Get search results
    pagination = search_service.search_items(
        query=query,
        filters=filters,
        sort=sort,
        order=order,
        page=page,
        per_page=per_page,
    )

    # Get facets for the current search
    facets = search_service.get_facets(query=query, filters=filters)

    # Get tag suggestions if query is provided
    tag_suggestions = []
    if query:
        tag_suggestions = ai_service.get_tag_suggestions(query)

    return jsonify(
        {
            "results": {
                "items": [item.to_dict() for item in pagination.items],
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "facets": facets,
            "tag_suggestions": tag_suggestions,
            "page": page,
            "per_page": per_page,
        }
    )


@search_bp.route("/search/facets", methods=["GET"])
@handle_errors
def get_facets():
    """Get available facets for the current search results"""
    query = request.args.get("q", "")
    facets = search_service.get_facets(query)
    return jsonify(facets)


@search_bp.route("/tags/suggestions", methods=["GET"])
def get_suggestions():
    query = request.args.get("q", "")
    limit = request.args.get("limit", 10, type=int)

    suggestions = ai_service.get_tag_suggestions(query, limit)
    return jsonify({"suggestions": suggestions}), 200
