from unittest                                                                           import TestCase
from mgraph_ai_service_cache_client.client.cache_service.register_cache_service         import register_cache_service__in_memory
from osbot_utils.testing.__                                                             import __
from osbot_utils.testing.__helpers                                                      import obj
from mgraph_ai_service_mitmproxy.utils.testing.Testing__Cache_Service__With__Test_Data  import setup__testing__cache_service__with__test_data


class test_Proxy__Cache__Service__transformations(TestCase):

    @classmethod
    def setUpClass(cls):
        register_cache_service__in_memory()
        with setup__testing__cache_service__with__test_data() as _:
            cls.cache_test_data = _
            cls.cache_service   = _.cache_service
            _.add_test_data()

    @classmethod
    def tearDownClass(cls):
        cls.cache_test_data.stop__fast_api__cache_server()


    def test__get_transformations(self):                                    # Test retrieving transformations for a page
        test_url = "https://example.com/"

        # Verify HTML transformation exists
        html_content = self.cache_service.get_cached_transformation(test_url, "url-to-html")
        assert html_content is not None
        assert "<html>" in html_content

        # Verify text transformation exists
        text_content = self.cache_service.get_cached_transformation(test_url, "url-to-lines")
        assert text_content is not None
        assert "Test text content" in text_content

    def test__transformation_metadata(self):        # Test retrieving transformation metadata
        test_url  = "https://example.com"
        page_refs = self.cache_service.get_or_create_page_entry(test_url)
        cache_id  = page_refs.cache_id

        # get metadata for HTML transformation
        metadata = self.cache_service.cache_client.data().retrieve().data__json__with__id_and_key(cache_id     = cache_id                                 ,
                                                                                                  namespace    = self.cache_service.cache_config.namespace,
                                                                                                  data_key     = "transformations/html/metadata"          ,
                                                                                                  data_file_id = " latest"                                )
        assert type(metadata) is dict
        assert obj(metadata) == __(status_code=200, content_type='text/html')       # todo: review this metadata value, since there should be more useful data here


    def test__multiple_pages_cached(self):                          # Test that multiple pages are properly cached
        test_urls = [ "https://example.com/"                  ,     # Verify all test pages exist
                      "https://docs.diniscruz/ai"             ,
                      "https://docs.diniscruz/ai/about.html"  ]

        for url in test_urls:
            assert self.cache_service.page_exists(url)
            assert self.cache_service.has_cached_transformation(url, "url-to-html" )         # Verify both transformations exist
            assert self.cache_service.has_cached_transformation(url, "url-to-lines")

    def test__cache_key_path_structure(self):                                               # Test hierarchical cache_key structure
        key1 = self.cache_service.url_to_cache_key("https://example.com/page")              # Different domains
        key2 = self.cache_service.url_to_cache_key("https://blog.example.com/page")

        assert key1.startswith("sites/example.com/pages/")
        assert key2.startswith("sites/blog.example.com/pages/")
        assert key1 != key2

        # Same domain, different paths
        key3 = self.cache_service.url_to_cache_key("https://example.com/article-1")
        key4 = self.cache_service.url_to_cache_key("https://example.com/article-2")

        assert key3.startswith("sites/example.com/pages/")
        assert key4.startswith("sites/example.com/pages/")
        assert key3 != key4

    def test__cache_stats_accumulate(self):                                         # Test that cache stats properly accumulate
        initial_stats = self.cache_service.get_cache_stats()

        test_url = "https://example.com/article-1"                                  # Make some cache operations

        self.cache_service.get_cached_transformation(test_url, "url-to-html")       # Cache hit
        self.cache_service.increment_cache_hit()


        self.cache_service.get_cached_transformation("https://example.com/nonexistent", "url-to-html")      # Cache miss
        self.cache_service.increment_cache_miss()

        updated_stats = self.cache_service.get_cache_stats()                                                # Get updated stats

        assert updated_stats["cache_hits"  ] >= initial_stats["cache_hits"]
        assert updated_stats["cache_misses"] >= initial_stats["cache_misses"]
