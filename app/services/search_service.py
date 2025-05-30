from app.models.clothing_item import Item
from app.extensions import db
from sqlalchemy import or_


class SearchService:
    def search_items(
        self,
        query="",
        filters=None,
        sort="created_at",
        order="desc",
        page=1,
        per_page=20,
    ):
        """
        Search for clothing items with filters and sorting

        Args:
            query (str): Search query string
            filters (dict): Dictionary of filters to apply
            sort (str): Field to sort by (e.g., price, created_at)
            order (str): Sort order (asc or desc)
            page (int): Page number
            per_page (int): Results per page

        Returns:
            Pagination object containing the search results
        """
        # Start with base query
        base_query = Item.query.filter(Item.is_public == True)

        # Apply text search if query is provided
        if query:
            search_terms = query.split()
            search_conditions = []
            for term in search_terms:
                search_conditions.append(
                    or_(
                        Item.name.ilike(f"%{term}%"),
                        Item.description.ilike(f"%{term}%"),
                        Item.brand.ilike(f"%{term}%"),
                        Item.category.ilike(f"%{term}%"),
                    )
                )
            base_query = base_query.filter(or_(*search_conditions))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if field == "min_price":
                    base_query = base_query.filter(Item.price >= value)
                elif field == "max_price":
                    base_query = base_query.filter(Item.price <= value)
                else:
                    # Other filters use exact match
                    base_query = base_query.filter(getattr(Item, field) == value)

        # Apply sorting
        sort_field = getattr(Item, sort)
        if order.lower() == "desc":
            sort_field = sort_field.desc()
        else:
            sort_field = sort_field.asc()
        base_query = base_query.order_by(sort_field)

        # Apply pagination
        return base_query.paginate(page=page, per_page=per_page)

    def get_facets(self, query="", filters=None):
        """
        Get available facets for the current search results

        Args:
            query (str): Search query string
            filters (dict): Dictionary of filters to apply

        Returns:
            dict: Dictionary containing facet counts
        """
        # Start with base query
        base_query = Item.query.filter(Item.is_public == True)

        # Apply text search if query is provided
        if query:
            search_terms = query.split()
            search_conditions = []
            for term in search_terms:
                search_conditions.append(
                    or_(
                        Item.name.ilike(f"%{term}%"),
                        Item.description.ilike(f"%{term}%"),
                        Item.brand.ilike(f"%{term}%"),
                        Item.category.ilike(f"%{term}%"),
                    )
                )
            base_query = base_query.filter(or_(*search_conditions))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if field == "min_price":
                    base_query = base_query.filter(Item.price >= value)
                elif field == "max_price":
                    base_query = base_query.filter(Item.price <= value)
                else:
                    # Other filters use exact match
                    base_query = base_query.filter(getattr(Item, field) == value)

        # Get facet counts
        facets = {
            "categories": db.session.query(Item.category, db.func.count(Item.id))
            .filter(Item.category.isnot(None))
            .group_by(Item.category)
            .all(),
            "brands": db.session.query(Item.brand, db.func.count(Item.id))
            .filter(Item.brand.isnot(None))
            .group_by(Item.brand)
            .all(),
            "colors": db.session.query(Item.color, db.func.count(Item.id))
            .filter(Item.color.isnot(None))
            .group_by(Item.color)
            .all(),
            "sizes": db.session.query(Item.size, db.func.count(Item.id))
            .filter(Item.size.isnot(None))
            .group_by(Item.size)
            .all(),
            "conditions": db.session.query(Item.condition, db.func.count(Item.id))
            .filter(Item.condition.isnot(None))
            .group_by(Item.condition)
            .all(),
        }

        # Convert to dictionary format
        return {
            "categories": [{"name": c[0], "count": c[1]} for c in facets["categories"]],
            "brands": [{"name": b[0], "count": b[1]} for b in facets["brands"]],
            "colors": [{"name": c[0], "count": c[1]} for c in facets["colors"]],
            "sizes": [{"name": s[0], "count": s[1]} for s in facets["sizes"]],
            "conditions": [{"name": c[0], "count": c[1]} for c in facets["conditions"]],
        }


# Create singleton instance
search_service = SearchService()
