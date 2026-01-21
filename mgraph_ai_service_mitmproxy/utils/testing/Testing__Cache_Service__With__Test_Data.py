from typing                                                                                         import List, Any
# todo: refactor out this dependency of the mgraph_ai_service_cache, since this is the only one in this mgraph_ai_service_mitmproxy project
from mgraph_ai_service_cache.fast_api.Cache_Service__Fast_API                                       import Cache_Service__Fast_API
from mgraph_ai_service_cache.service.cache.Cache__Config                                            import Cache__Config
from mgraph_ai_service_cache.service.cache.Cache__Service                                           import Cache__Service
from mgraph_ai_service_cache_client.client.client_contract.Cache__Service__Fast_API__Client         import Cache__Service__Fast_API__Client
from mgraph_ai_service_cache_client.client.client_contract.Cache__Service__Fast_API__Client__Config import Cache__Service__Fast_API__Client__Config
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Storage_Mode                   import Enum__Cache__Storage_Mode
from osbot_fast_api.utils.Fast_API_Server                                                           import Fast_API_Server
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                                import Serverless__Fast_API__Config
from osbot_utils.type_safe.Type_Safe                                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                            import Safe_Str__Url
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                                import Proxy__Cache__Service
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Config                        import Schema__Cache__Config
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Stats                         import Schema__Cache__Stats


class Testing__Cache_Service__With__Test_Data(Type_Safe):                          # Shared cache service test infrastructure
    cache_service           : Any                                                  # Proxy__Cache__Service instance
    cache_client            : Any                                                  # Cache__Service__Fast_API__Client instance
    cache_service__fast_api : Any                                                  # Service__Fast_API instance
    fast_api_server         : Any                                                  # Fast_API_Server instance
    server_url              : Safe_Str__Url                                        # Server base URL
    cache_config            : Any                                                  # Schema__Cache__Config instance
    test_urls               : List[Safe_Str__Url]                                  # Test URLs for cache operations
    setup_completed         : bool                     = False                     # Tracks setup state

    def add_test_data(self) -> None:                                         # Populate cache with test transformations
        self.start__fast_api__cache_server()                                # make sure server is running (since these requests run on a live server)
        self.test_urls = [ Safe_Str__Url("https://example.com/")                ,
                          Safe_Str__Url("https://docs.diniscruz/ai")            ,
                          Safe_Str__Url("https://docs.diniscruz/ai/about.html")]

        for url in self.test_urls:
            self.cache_service.store_transformation(target_url  = str(url)                                               ,
                                                   wcf_command  = "url-to-html"                                         ,
                                                   content      = f"<html><body><h1>Test content for {url}</h1></body></html>",
                                                   metadata     = {"status_code": 200, "content_type": "text/html"}     )

            self.cache_service.store_transformation(target_url  = str(url)                        ,
                                                   wcf_command  = "url-to-lines"                  ,
                                                   content      = f"Test text content for {url}"  ,
                                                   metadata     = {"status_code": 200, "content_type": "text/plain"})
        return self

    def setup(self) -> 'Testing__Cache_Service__With__Test_Data':                  # Initialize cache service and populate test data
        with self as _:
            if _.setup_completed:                                                  # Skip if already setup
                return _

            _.setup__cache_backend      ()
            _.setup__fast_api_server    ()
            _.setup__cache_client       ()
            _.setup__proxy_cache_service()
            _.setup_completed = True

        return self

    def setup__cache_backend(self) -> None:                                       # Setup cache service backend
        cache_config                 = Cache__Config               (storage_mode    = Enum__Cache__Storage_Mode.MEMORY         )
        serverless_config            = Serverless__Fast_API__Config(enable_api_key  = False                                    )
        self.cache_service__fast_api = Cache_Service__Fast_API     (config          = serverless_config                       ,
                                                                    cache_service   = Cache__Service(cache_config=cache_config))
        self.cache_service__fast_api.setup()

    def setup__fast_api_server(self) -> None:                                     # Setup and configure Fast API server
        self.fast_api_server = Fast_API_Server(app=self.cache_service__fast_api.app())
        self.server_url      = self.fast_api_server.url().rstrip("/")

    def setup__cache_client(self) -> None:                                        # Setup cache client with server URL
        client_config    = Cache__Service__Fast_API__Client__Config(base_url     = str(self.server_url),
                                                                    fast_api_app = self.cache_service__fast_api.app())
        self.cache_client = Cache__Service__Fast_API__Client(config=client_config)

    def setup__proxy_cache_service(self) -> None:                                 # Setup proxy cache service with configuration
        self.cache_config = Schema__Cache__Config(enabled   = True               ,
                                                   base_url  = str(self.server_url),
                                                   namespace = "test-cache-routes",
                                                   timeout   = 2                  )

        self.cache_service = Proxy__Cache__Service(cache_client = self.cache_client,
                                                    cache_config = self.cache_config,
                                                    stats        = Schema__Cache__Stats())

    def start__fast_api__cache_server(self) -> bool:                                # Start the Fast API server
        if self.fast_api_server.running:                                            # note: we can't use context with fast_api_server, since it starts and stops the server on enter/exit
            return False
        else:
            self.fast_api_server.start()
            return True

    def stop__fast_api__cache_server(self) -> bool:                                 # Stop the Fast API server
        if self.fast_api_server.running:                                            # note: we can't use context with fast_api_server, since it starts and stops the server on enter/exit
            self.fast_api_server.stop()
            return True
        else:
            return False



    def get_test_url(self, index: int = 0) -> Safe_Str__Url:                     # Get test URL by index
        return self.test_urls[index] if index < len(self.test_urls) else self.test_urls[0]

    def get_cached_html(self, url: Safe_Str__Url) -> str:                        # Retrieve cached HTML transformation
        return self.cache_service.get_cached_transformation(target_url  = str(url)      ,
                                                            wcf_command  = "url-to-html" )

    def get_cached_text(self, url: Safe_Str__Url) -> str:                        # Retrieve cached text transformation
        return self.cache_service.get_cached_transformation(target_url  = str(url)       ,
                                                            wcf_command  = "url-to-lines" )



testing__cache_service__with__test_data = Testing__Cache_Service__With__Test_Data()     # Singleton instance and setup function

def setup__testing__cache_service__with__test_data():                                    # Setup shared cache service (called once per test suite)
    with testing__cache_service__with__test_data as _:
        if _.setup_completed is False:
            _.setup()
    return testing__cache_service__with__test_data