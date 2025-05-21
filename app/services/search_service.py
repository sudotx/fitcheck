# from algoliasearch.search.client import SearchClientSync
# from typing import List, Dict, Any

# from ..config import Config


# class SearchService:
#     def __init__(self):
#         self.client = SearchClientSync(Config.ALGOLIA_APP_ID, Config.ALGOLIA_API_KEY)
#         self.index_name = "clothing_items"
#         self._setup_index()

#     def _setup_index(self):
#         """Configure the search index with appropriate settings"""
#         # Define searchable attributes
#         self.client.set_settings(
#             index_name=self.index_name,
#             searchableAttributes=[
#                 "name",
#                 "description",
#                 "brand",
#                 "category",
#                 "tags",
#                 "color",
#             ],
#             attributesForFaceting=[
#                 "category",
#                 "brand",
#                 "color",
#                 "size",
#                 "condition",
#                 "price",
#                 "for_sale",
#             ],
#             attributesForSorting=["price", "created_at"],
#         )

#     def add_item(self, item: Dict[str, Any]):
#         """Add or update a clothing item in the search index"""
#         response = self.client.save_object(index_name=self.index_name, body=item)
#         # Wait for indexing to complete
#         self.client.wait_for_task(index_name=self.index_name, task_id=response.task_id)

#     def search_items(
#         self,
#         query: str,
#         filters: Dict[str, Any] = None,
#         sort: List[str] = None,
#         page: int = 1,
#         per_page: int = 20,
#     ) -> Dict[str, Any]:
#         """
#         Search for clothing items with filters and sorting

#         Args:
#             query: Search query string
#             filters: Dictionary of filters (e.g., {'category': 'tops', 'price': '0..100'})
#             sort: List of sort criteria (e.g., ['price:asc'])
#             page: Page number for pagination
#             per_page: Number of results per page
#         """
#         search_params = {
#             "page": page - 1,  # Algolia uses 0-based pagination
#             "hitsPerPage": per_page,
#         }

#         if filters:
#             filter_strings = []
#             for key, value in filters.items():
#                 if isinstance(value, (list, tuple)):
#                     filter_strings.append(f"{key}:{','.join(map(str, value))}")
#                 else:
#                     filter_strings.append(f"{key}:{value}")
#             search_params["filters"] = " AND ".join(filter_strings)

#         if sort:
#             search_params["sortFacetBy"] = sort[
#                 0
#             ]  # Algolia uses a single sort parameter

#         results = self.client.search(
#             {
#                 "requests": [
#                     {
#                         "indexName": self.index_name,
#                         "query": query,
#                         "params": search_params,
#                     }
#                 ]
#             }
#         )

#         # Transform results to match previous format
#         return {
#             "hits": results["results"][0]["hits"],
#             "estimatedTotalHits": results["results"][0]["nbHits"],
#             "page": page,
#             "hitsPerPage": per_page,
#         }

#     def delete_item(self, item_id: str):
#         """Remove an item from the search index"""
#         response = self.client.delete_object(
#             index_name=self.index_name, object_id=item_id
#         )
#         # Wait for deletion to complete
#         self.client.wait_for_task(index_name=self.index_name, task_id=response.task_id)

#     def get_facets(self, query: str = "") -> Dict[str, List[str]]:
#         """Get available facets for the current search results"""
#         results = self.client.search(
#             {
#                 "requests": [
#                     {
#                         "indexName": self.index_name,
#                         "query": query,
#                         "params": {
#                             "facets": [
#                                 "category",
#                                 "brand",
#                                 "color",
#                                 "size",
#                                 "condition",
#                             ]
#                         },
#                     }
#                 ]
#             }
#         )
#         return results["results"][0].get("facets", {})


# search_service = SearchService()
