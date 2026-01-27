from osbot_fast_api.api.routes.Fast_API__Routes                         import Fast_API__Routes
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service    import Proxy__Cache__Service
from typing                                                             import Dict, Any

TAG__ROUTES_CACHE = 'cache'
ROUTES_PATHS__CACHE = [f'/{TAG__ROUTES_CACHE}/stats',
                       f'/{TAG__ROUTES_CACHE}/config',
                       f'/{TAG__ROUTES_CACHE}/health']

class Routes__Cache(Fast_API__Routes):                               # FastAPI routes for cache introspection
    tag           : str = TAG__ROUTES_CACHE
    cache_service: Proxy__Cache__Service            = None           # Cache service instance

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_service = Proxy__Cache__Service()#.setup()

    def health(self) -> Dict[str, Any]:                                 # Test cache service connection
        enabled = self.cache_service.cache_config.enabled

        return { "status"   : "ok" if enabled else "disabled"               ,           # todo: refactor to Type_Safe class
                 "enabled"  : enabled                                       ,
                 "base_url" : str(self.cache_service.cache_config.base_url) ,
                 "namespace": str(self.cache_service.cache_config.namespace)}

    def stats(self) -> Dict[str, Any]:                           # Retrieve current cache statistics
        return self.cache_service.get_cache_stats()             # todo: refactor to Type_Safe class

    def config(self) -> Dict[str, Any]:                         # Retrieve current cache configuration (sanitized)
        config = self.cache_service.cache_config

        if config.api_key  and config.api_key_header:           # Note: api_key is NOT exposed for security
            auth_configured = True                              # using this pattern to make sure we don't expose keys
        else:
            auth_configured = False
        return {  "enabled"         : config.enabled          ,                         # todo: refactor to Type_Safe class
                  "auth_configured" : auth_configured         ,
                  "base_url"        : str(config.base_url)    ,
                  "namespace"       : str(config.namespace)   ,
                  "timeout"         : int(config.timeout)     ,
                  "strategy"        : config.strategy.value   ,
                  "data_file_id"    : config.data_file_id     ,
                  "cache_metadata"  : config.cache_metadata   ,
                  "track_stats"     : config.track_stats      }

    # todo: add the pages capability to self.cache_service
    # def pages(self, limit: int = 20,                                                    # Maximum number of pages to return
    #                 offset: int = 0                                                     # Offset for pagination
    #            ) -> Dict[str, Any]:                                                     # Get list of cached pages
    #     """
    #     Get list of cached pages with pagination
    #
    #     Note: This endpoint queries the cache service for all entries in the namespace
    #     """

    # todo: refactor this to a 'Sites and Pages' service and endpoint
    # @route_path("/pages/{cache_key:path}")
    # def page__cache_key(self,cache_key: str                        # Cache key path (e.g., "sites/example.com/pages/article")
    #                     ) -> dict:                                 # Get specific page entry and its transformations
    #     """
    #     Retrieve a specific page entry by cache_key
    #
    #     Returns page metadata and available transformations
    #     """
    #     if not self.cache_service:
    #         return {"error": "Cache service not available"}
    #
    #     try:
    #         # Get cache_id from cache_key
    #         cache_id = self.cache_service.get_or_create_page_entry(
    #             f"https://{cache_key.replace('sites/', '').replace('/pages', '')}"
    #         )
    #
    #         # Try to retrieve page entry
    #         result = self.cache_service.cache_client.retrieve().retrieve__cache_key(
    #             namespace=self.cache_service.cache_config.namespace,
    #             strategy=self.cache_service.cache_config.strategy,
    #             cache_key=cache_key
    #         )
    #
    #         return {
    #             "cache_key": cache_key,
    #             "cache_id": cache_id,
    #             "page_data": result.get("body", {}),
    #             "metadata": result.get("metadata", {})
    #         }
    #
    #     except Exception as e:
    #         return {
    #             "error": str(e),
    #             "cache_key": cache_key,
    #             "message": "Page not found or error retrieving"
    #         }


    def setup_routes(self):
        self.add_route_get(self.health              )
        self.add_route_get(self.stats               )
        self.add_route_get(self.config              )