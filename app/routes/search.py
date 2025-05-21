# from flask import Blueprint, request, jsonify
# from ..services.search_service import search_service
# from ..utils.decorators import handle_errors
# from flask_jwt_extended import get_jwt_identity, jwt_required

# from app.services.search_service import search_items
# from app.services.ai_service import get_tag_suggestions

# search_bp = Blueprint("search", __name__)


# @search_bp.route("/search", methods=["GET"])
# @handle_errors
# def search_items():
#     """
#     Search for clothing items with filters and sorting

#     Query Parameters:
#         q: Search query string
#         category: Filter by category
#         brand: Filter by brand
#         color: Filter by color
#         size: Filter by size
#         condition: Filter by condition
#         min_price: Minimum price
#         max_price: Maximum price
#         sort: Sort criteria (e.g., price:asc, created_at:desc)
#         page: Page number
#         per_page: Results per page
#     """
#     # Get search query
#     query = request.args.get("q", "")
#     tags = request.args.getlist("tags")

#     # Get filters
#     filters = {}
#     for param in ["category", "brand", "color", "size", "condition"]:
#         value = request.args.get(param)
#         if value:
#             filters[param] = value

#     # Handle price range
#     min_price = request.args.get("min_price")
#     max_price = request.args.get("max_price")
#     if min_price or max_price:
#         price_range = []
#         if min_price:
#             price_range.append(f"price >= {min_price}")
#         if max_price:
#             price_range.append(f"price <= {max_price}")
#         filters["price"] = " AND ".join(price_range)

#     # Get sorting
#     sort = request.args.get("sort")
#     if sort:
#         sort = [sort]

#     # Get pagination
#     page = int(request.args.get("page", 1))
#     per_page = int(request.args.get("per_page", 20))

#     # Perform search
#     results = search_items(
#         query=query, tags=tags, filters=filters, sort=sort, page=page, per_page=per_page
#     )

#     # Get facets for the current search
#     facets = search_service.get_facets(query)

#     return (
#         jsonify(
#             {
#                 "items": [item.to_dict() for item in results.items],
#                 "total": results.total,
#                 "pages": results.pages,
#                 "current_page": results.page,
#                 "facets": facets,
#             }
#         ),
#         200,
#     )


# @search_bp.route("/search/facets", methods=["GET"])
# @handle_errors
# def get_facets():
#     """Get available facets for the current search results"""
#     query = request.args.get("q", "")
#     facets = search_service.get_facets(query)
#     return jsonify(facets)


# @search_bp.route("/tags/suggestions", methods=["GET"])
# def get_suggestions():
#     query = request.args.get("q", "")
#     limit = request.args.get("limit", 10, type=int)

#     suggestions = get_tag_suggestions(query, limit)
#     return jsonify({"suggestions": suggestions}), 200
