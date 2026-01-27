from unittest                                                                                       import TestCase
from mgraph_ai_service_cache_client.client.cache_service.register_cache_service                     import register_cache_service__in_memory
from osbot_utils.helpers.cache.Cache__Hash__Generator                                               import Cache__Hash__Generator
from osbot_utils.helpers.duration.decorators.capture_duration                                       import capture_duration
from osbot_utils.testing.__                                                                         import __, __SKIP__
from osbot_utils.type_safe.primitives.core.Safe_UInt                                                import Safe_UInt
from osbot_utils.utils.Misc                                                                         import is_guid
from osbot_utils.testing.__helpers                                                                  import obj
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                                import Proxy__Cache__Service
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Config                        import Schema__Cache__Config
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Page__Refs                    import Schema__Cache__Page__Refs
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Stats                         import Schema__Cache__Stats

class test_Proxy__Cache__Service(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with capture_duration() as duration:
            # cache_config = Cache__Config(storage_mode=Enum__Cache__Storage_Mode.MEMORY)
            #
            # cls.serverless_config       = Serverless__Fast_API__Config(enable_api_key=False)
            # cls.cache_service__fast_api = Cache_Service__Fast_API(config=cls.serverless_config,
            #                                                       cache_service=Cache__Service(cache_config=cache_config))  # Inject configured service
            #
            # cls.fast_api_server         = Fast_API_Server(app=cls.cache_service__fast_api.app())
            # cls.server_url              = cls.fast_api_server.url().rstrip("/")                              # note: the trailing / was causing issues with the auto-generated request code
            # #cls.server_url              = "http://0.0.0.0:10017"                                            # note: to use a local server we need to also add the auth
            #
            # cls.server_config           = Cache__Service__Fast_API__Client__Config(base_url=cls.server_url)
            # cls.fast_api_client         = Cache__Service__Fast_API__Client        (config=cls.server_config)
            #
            # cls.cache_service__fast_api.setup()
            # cls.fast_api_server        .start()
            #
            # cls.client_config = Cache__Service__Fast_API__Client__Config(base_url = cls.server_url   ,
            #                                                              fast_api_app = cls.cache_service__fast_api.app())
            # cls.cache_client  = Cache__Service__Fast_API__Client         (config   = cls.client_config)
            # cls.cache_config  = Schema__Cache__Config             (enabled  = True                ,
            #                                                        base_url  = cls.server_url     ,
            #                                                        namespace = "proxy-cache-tests",
            #                                                        timeout   = 30)
            # Create cache service instance
            register_cache_service__in_memory()
            cls.cache_config  = Schema__Cache__Config             (enabled  = True                ,
                                                                   namespace = "proxy-cache-tests")
            cls.cache_service = Proxy__Cache__Service(cache_config = cls.cache_config,
                                                      stats        = Schema__Cache__Stats())

        assert duration.seconds < 5               # server setup and start should not take more than 0.5 (locally takes about 0.25)

    # @classmethod
    # def tearDownClass(cls) -> None:
    #     cls.fast_api_server.stop()


    # def test__setUpClass(self):
    #     with self.cache_service as _:
    #         assert type(_) is Proxy__Cache__Service
    #
    #         # Check OpenAPI spec
    #
    #         open_api_json       = GET_json(self.server_url + '/openapi.json')
    #         open_api_json__obj  = obj(open_api_json)
    #         paths_json          = open_api_json.get('paths')
    #         storage_info        = GET_json(self.server_url + '/server/storage/info')                            # Verify we're using MEMORY storage mode
    #         storage_backend     = self.cache_service__fast_api.cache_service.storage_backend()                  # Verify storage backend type
    #
    #         assert open_api_json__obj.info.title                                        == 'Cache_Service__Fast_API'
    #         assert '/{namespace}/retrieve/{cache_id}'                                   in list_set(paths_json)                           # confirm the routes have been wired
    #         assert self.cache_service__fast_api.cache_service.cache_config.storage_mode == Enum__Cache__Storage_Mode.MEMORY # Additional verification - check the actual cache service configuration
    #         assert storage_info                                                         == { 'storage_mode': 'memory',   'ttl_hours': 24 }
    #         assert type(storage_backend)                                                is Storage_FS__Memory


    def test__url_to_cache_key(self):                          # Test URL to cache_key conversion
        with self.cache_service as _:
            # Basic URL
            cache_key = _.url_to_cache_key("https://example.com/articles/hello-world")
            assert cache_key == "sites/example.com/pages/articles/hello-world"

            # With query params (should be ignored)
            cache_key = _.url_to_cache_key("https://example.com/article?id=123&ref=twitter")
            assert cache_key == "sites/example.com/pages/article"

            # Homepage
            cache_key = _.url_to_cache_key("https://example.com")
            assert cache_key == "sites/example.com/pages/index"

            # With subdomain
            cache_key = _.url_to_cache_key("https://blog.example.com/post/2024/january")
            assert cache_key == "sites/blog.example.com/pages/post/2024/january"

            # With special characters (should be sanitized)
            cache_key = _.url_to_cache_key("https://example.com/articles/hello-world!@#$%")
            assert cache_key == "sites/example.com/pages/articles/hello-world-"

    def test__sanitize_url_path(self):                         # Test URL path sanitization
        with self.cache_service as _:
            # Basic alphanumeric
            assert _.sanitize_url_path("hello-world") == "hello-world"

            # With special characters
            assert _.sanitize_url_path("hello@world!test") == "hello-world-test"

            # With multiple consecutive special chars
            assert _.sanitize_url_path("hello!!!world") == "hello-world"

            # With forward slashes (should be preserved)
            assert _.sanitize_url_path("articles/2024/january") == "articles/2024/january"

    def test__get_or_create_page_entry(self):                  # Test page entry creation with KEY_BASED strategy
        url = "https://example.com/an-entry"

        with self.cache_service as _:
            expected_cache_key  = "sites/example.com/pages/an-entry"
            expected_cache_hash = Cache__Hash__Generator().from_string(expected_cache_key)
            page_refs_1         = _.get_or_create_page_entry(url)
            cache_id_1          = page_refs_1.cache_id

            assert _.url_to_cache_key(url)  == expected_cache_key
            assert expected_cache_hash      ==  "6d3c93d673a5a90c"
            assert type(page_refs_1)        is Schema__Cache__Page__Refs
            assert page_refs_1.obj()        == __(cache_id        = cache_id_1          ,
                                                  cache_key       = expected_cache_key  ,
                                                  cache_hash      = expected_cache_hash ,
                                                  json_field_path = 'cache_key'         )
            assert page_refs_1.cache_hash == expected_cache_hash
            assert page_refs_1.cache_key  == expected_cache_key
            assert is_guid(cache_id_1)    is True

            # Second call - returns same cache_id
            page_refs_2 = _.get_or_create_page_entry(url)
            cache_id_2  = page_refs_2.cache_id

            assert cache_id_2         == cache_id_1                                             # confirm cache_ids are the same

            assert page_refs_2.obj()  == __(cache_id        = cache_id_2          ,
                                            cache_key       = expected_cache_key  ,
                                            cache_hash      = expected_cache_hash ,
                                            json_field_path = 'cache_key'         )
            assert page_refs_1.obj() == page_refs_2.obj()                                       # confirm both are the same
            assert _.stats.total_pages_cached >= 1                                              # Stats should show one page cached

    def test__store_transformation(self):                      # Test storing WCF transformation as child data
        with self.cache_service as _:
            url = "https://example.com/test-page-2"
            wcf_command = "url-to-html"
            content = "<html><body><h1>Test Page</h1></body></html>"
            metadata = { "status_code"          : 200                    ,
                         "content_type"         : "text/html"            ,
                         "wcf_response_time_ms" : 1234.5                 ,
                         "cached_at"            : "2024-10-10T12:00:00Z" }

            # Store transformation
            cache_id = _.store_transformation(target_url    = url        ,
                                              wcf_command   = wcf_command,
                                              content       = content    ,
                                              metadata      = metadata   )

            assert is_guid(cache_id)

    def test__get_cached_transformation(self):                 # Test retrieving cached transformation
        with self.cache_service as _:
            url              = "https://example.com/test-page-3"
            wcf_command      = "url-to-html"
            expected_content = "<html><body><h1>Cached Content</h1></body></html>"

            _.store_transformation( target_url  = url                ,                          # First, store a transformation
                                    wcf_command = wcf_command        ,
                                    content     = expected_content   ,
                                    metadata    = {"test": "metadata"})

            cached_content = _.get_cached_transformation(url, wcf_command)                      # Then retrieve it

            assert cached_content is not None
            assert cached_content == expected_content

    def test__cache_miss(self):                                # Test cache miss scenario
        with self.cache_service as _:
            url = "https://example.com/non-existent-page"
            wcf_command = "url-to-html"

            # Try to get non-existent transformation
            cached_content = _.get_cached_transformation(url, wcf_command)

            assert cached_content is None

    def test__has_cached_transformation(self):                 # Test checking if transformation exists
        with self.cache_service as _:
            url = "https://example.com/test-page-6"
            wcf_command = "url-to-lines"
            content = "Plain text content"

            # Before storing
            assert _.has_cached_transformation(url, wcf_command) == False

            # Store transformation
            _.store_transformation(url, wcf_command, content, {})

            # After storing
            assert _.has_cached_transformation(url, wcf_command) == True

    def test__multiple_transformations_per_page(self):         # Test multiple transformation types for same page
        with self.cache_service as _:
            url = "https://example.com/test-page-5"

            # Store HTML transformation
            html_content = "<html><body><h1>Test</h1></body></html>"
            _.store_transformation(url, "url-to-html", html_content, {})

            # Store text transformation
            text_content = "Test heading"
            _.store_transformation(url, "url-to-lines", text_content, {})

            # Store ratings transformation
            ratings_content = '{"rating": "safe", "score": 0.95}'
            _.store_transformation(url, "url-to-ratings", ratings_content, {})

            # Retrieve all transformations
            html = _.get_cached_transformation(url, "url-to-html")
            text = _.get_cached_transformation(url, "url-to-lines")
            ratings = _.get_cached_transformation(url, "url-to-ratings")

            assert html == html_content
            assert text == text_content
            assert ratings == ratings_content
            #assert ratings == str_to_json(ratings_content)

    def test__wcf_command_to_data_key(self):                   # Test WCF command to data_key conversion
        with self.cache_service as _:
            assert _._wcf_command_to_data_key("url-to-html") == "transformations/html"
            assert _._wcf_command_to_data_key("url-to-lines") == "transformations/text"
            assert _._wcf_command_to_data_key("url-to-ratings") == "transformations/ratings"
            assert _._wcf_command_to_data_key("url-to-html-min-rating") == "transformations/html-filtered"

            # Unknown command - should use generic path
            assert _._wcf_command_to_data_key("unknown-command") == "transformations/unknown_command"

    def test__cache_statistics(self):                          # Test cache statistics tracking
        with self.cache_service as _:
            url = "https://example.com/test-page-6"
            wcf_command = "url-to-html"
            content = "<html><body>Test</body></html>"

            # Store transformation
            _.store_transformation(url, wcf_command, content, {})

            # First retrieval - cache hit
            _.get_cached_transformation(url, wcf_command)
            _.increment_cache_hit()

            # Check for non-existent transformation - cache miss
            _.get_cached_transformation("https://example.com/missing", wcf_command)
            _.increment_cache_miss()

            # Get statistics
            stats = _.get_cache_stats()

            assert stats["enabled"] == True
            assert stats["cache_hits"] > 0
            assert stats["cache_misses"] > 0
            assert stats["hit_rate"] > 0.0
            assert stats["wcf_calls_saved"] > 0

    def test__end_to_end_caching_flow(self):                   # Test complete caching flow (simulating WCF integration)
        with self.cache_service as _:
            url = "https://example.com/articles/end-to-end-test"
            wcf_command = "url-to-html"

            # Initial cache miss
            cached = _.get_cached_transformation(url, wcf_command)
            assert cached is None
            _.increment_cache_miss()

            # Simulate WCF call and cache result
            wcf_response = "<html><body><h1>Article Title</h1><p>Content...</p></body></html>"
            metadata = {
                "status_code": 200,
                "content_type": "text/html",
                "wcf_response_time_ms": 2345.6
            }

            _.store_transformation(url, wcf_command, wcf_response, metadata)

            # Subsequent request - cache hit
            cached = _.get_cached_transformation(url, wcf_command)
            assert cached is not None
            assert cached == wcf_response
            _.increment_cache_hit()

            # Verify statistics
            stats = _.get_cache_stats()
            assert stats["cache_misses"] >= 1
            assert stats["cache_hits"] >= 1

    def test__cache_service__url_to_cache_key(self):
        """Test URL to cache_key conversion for route path mapping"""
        with self.cache_service as _:
            # Test basic URL
            cache_key = _.url_to_cache_key("https://example.com/article-1")
            assert cache_key == "sites/example.com/pages/article-1"

            # Test subdomain
            cache_key = _.url_to_cache_key("https://blog.example.com/post-1")
            assert cache_key == "sites/blog.example.com/pages/post-1"


    def test__get_stats(self):              # Test /cache/stats endpoint logic
        # todo: add check to call /cache/stats
        stats = self.cache_service.get_cache_stats()

        assert obj(stats) == __(enabled                      = True             ,
                                hit_rate                     = 0.5              ,
                                cache_hits                   = Safe_UInt(2)     ,
                                cache_misses                 = Safe_UInt(2)     ,
                                wcf_calls_saved              = Safe_UInt(2)     ,
                                total_pages_cached           = Safe_UInt(7)     ,
                                avg_cache_hit_time_ms        = __SKIP__         ,
                                avg_cache_miss_time_ms       = __SKIP__         ,
                                avg_wcf_call_time_ms         = __SKIP__         ,
                                estimated_time_saved_seconds  = __SKIP__        )  # todo: review the use of this estimated_time_saved_seconds value, since I don't think we need it

    def test__get_page_by_cache_hash(self):      # Test retrieving specific page by cache_key
        test_url  = "https://example.com"                     # Get one of our test pages


        # Get cache_id
        page_refs  = self.cache_service.get_or_create_page_entry(test_url)
        cache_id   = page_refs.cache_id
        cache_hash = page_refs.cache_hash
        assert cache_id is not None

        assert self.cache_service.page_exists(test_url) is True             # Verify page exists

        result = self.cache_service.cache_client.retrieve().retrieve__hash__cache_hash(namespace=self.cache_service.cache_config.namespace, # Verify we can retrieve the page entry
                                                                                       cache_hash=cache_hash)
        assert result.obj() == __(data       = __(url              = 'https://example.com'            ,
                                                 cache_key        = 'sites/example.com/pages/index'  ,
                                                 domain           = 'example.com'                    ,
                                                 path             = ''                               ,
                                                 created_at       = __SKIP__                         ,
                                                 last_accessed    = __SKIP__                         ,
                                                 access_count     = 1                                ),
                                 metadata   = __(cache_id         = __SKIP__                         ,
                                                 cache_hash       = __SKIP__                         ,
                                                 cache_key        = 'sites/example.com/pages/index'  ,
                                                 file_id          = 'page-entry'                     ,
                                                 namespace        = 'proxy-cache-tests'              ,
                                                 strategy         = 'key_based'                      ,
                                                 stored_at        = __SKIP__                         ,
                                                 file_type        = 'json'                           ,
                                                 content_encoding = None                             ,
                                                 content_size     = 0                                ),
                                 data_type  = 'json'                                                  )

