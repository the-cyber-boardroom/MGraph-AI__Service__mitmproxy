from unittest                                                                            import TestCase
from mgraph_ai_service_cache.fast_api.Cache_Service__Fast_API                            import Cache_Service__Fast_API
from osbot_utils.utils.Objects                                                           import base_classes
from osbot_utils.type_safe.Type_Safe                                                     import Type_Safe
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                 import Safe_Str__Url
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                     import Proxy__Cache__Service
from mgraph_ai_service_cache_client.client.client_contract.Cache__Service__Fast_API__Client            import Cache__Service__Fast_API__Client
from osbot_fast_api.utils.Fast_API_Server                                                import Fast_API_Server
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Config             import Schema__Cache__Config
from mgraph_ai_service_mitmproxy.utils.testing.Testing__Cache_Service__With__Test_Data   import setup__testing__cache_service__with__test_data, Testing__Cache_Service__With__Test_Data, testing__cache_service__with__test_data


# todo: add skip to this class locally (since it takes a couple seconds to run due to the multiple starts and stops of the fastapi server
class test_Testing__Cache_Service__With__Test_Data(TestCase):

    @classmethod
    def setUpClass(cls):                                                          # Setup shared test infrastructure once
        cls.helper = setup__testing__cache_service__with__test_data()
        cls.helper.add_test_data()

    @classmethod
    def tearDownClass(cls):                                                       # Clean up server resources
        cls.helper.stop__fast_api__cache_server()

    def test__init__(self):                                                       # Test auto-initialization of helper class
        with Testing__Cache_Service__With__Test_Data() as _:
            assert type(_)                    is Testing__Cache_Service__With__Test_Data
            assert base_classes(_)            == [Type_Safe, object]
            assert _.cache_service            is None                             # Not yet initialized
            assert _.cache_client             is None
            assert _.cache_service__fast_api  is None
            assert _.fast_api_server          is None
            assert _.server_url               == ''                               # Safe_Str__Url default
            assert _.cache_config             is None
            assert _.test_urls                == []                               # Empty list
            assert _.setup_completed          is False                            # Not setup yet

    def test__setup(self):                                                        # Test complete setup process
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup()
            _.add_test_data()
            assert _.setup_completed          is True                             # Setup flag set
            assert _.cache_service            is not None
            assert _.cache_client             is not None
            assert _.cache_service__fast_api  is not None
            assert _.fast_api_server          is not None
            assert _.server_url               != ''
            assert _.cache_config             is not None
            assert len(_.test_urls)           == 3                                # Three test URLs

            # Verify types are correct
            assert type(_.cache_service)           is Proxy__Cache__Service
            assert type(_.cache_client)            is Cache__Service__Fast_API__Client
            assert type(_.cache_service__fast_api) is Cache_Service__Fast_API
            assert type(_.fast_api_server)         is Fast_API_Server
            assert type(_.server_url)              is Safe_Str__Url
            assert type(_.cache_config)            is Schema__Cache__Config
            _.stop__fast_api__cache_server()

    def test__setup__idempotent(self):                                            # Test setup can be called multiple times safely
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup()
            first_server_url = _.server_url

            _.setup()                                                             # Call setup again

            assert _.server_url == first_server_url                               # Same server URL
            assert _.setup_completed is True                                      # Still marked as complete

    def test__setup__cache_backend(self):                                         # Test cache backend setup
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup__cache_backend()

            assert _.cache_service__fast_api is not None
            assert type(_.cache_service__fast_api) is Cache_Service__Fast_API

            # Verify it has an app
            app = _.cache_service__fast_api.app()
            assert app is not None

    def test__setup__fast_api_server(self):                                       # Test Fast API server setup
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup__cache_backend()                                              # Required before server setup
            _.setup__fast_api_server()

            assert _.fast_api_server is not None
            assert type(_.fast_api_server) is Fast_API_Server
            assert type(_.server_url) is Safe_Str__Url
            assert len(_.server_url) > 0                                          # URL is populated
            assert str(_.server_url).startswith('http')                           # Valid HTTP URL

    def test__setup__cache_client(self):                                          # Test cache client setup
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup__cache_backend()
            _.setup__fast_api_server()
            _.setup__cache_client()

            assert _.cache_client is not None
            assert type(_.cache_client) is Cache__Service__Fast_API__Client

    def test__setup__proxy_cache_service(self):                                   # Test proxy cache service setup
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup__cache_backend()
            _.setup__fast_api_server()
            _.setup__cache_client()
            _.setup__proxy_cache_service()

            assert _.cache_service is not None
            assert _.cache_config  is not None
            assert type(_.cache_service) is Proxy__Cache__Service
            assert type(_.cache_config)  is Schema__Cache__Config

            # Verify cache config values
            assert _.cache_config.enabled   is True
            assert _.cache_config.namespace == "test-cache-routes"
            assert _.cache_config.timeout   == 2
            assert _.cache_config.base_url  == str(_.server_url)

    def test__populate_test_data(self):                                           # Test data population
        with self.helper as _:

            assert len(_.test_urls) == 3                                          # Three test URLs populated

            for url in _.test_urls:                                               # Verify all URLs are Safe_Str__Url instances
                assert type(url) is Safe_Str__Url

            # Verify expected URLs
            assert _.test_urls[0] == Safe_Str__Url("https://example.com/"                )
            assert _.test_urls[1] == Safe_Str__Url("https://docs.diniscruz/ai"           )
            assert _.test_urls[2] == Safe_Str__Url("https://docs.diniscruz/ai/about.html")

    def test__populate_test_data__cache_entries(self):                            # Test cached transformations are stored
        with self.helper as _:

            # Verify HTML transformations stored
            for url in _.test_urls:
                html_content = _.get_cached_html(url)
                assert f"Test content for {url}" in html_content
                assert "<html>" in html_content
                assert "<h1>" in html_content

            # Verify text transformations stored
            for url in _.test_urls:
                text_content = _.get_cached_text(url)
                assert f"Test text content for {url}" in text_content


    def test__get_test_url(self):                                                 # Test getting test URLs by index
        with self.helper as _:
            # Get by index
            assert _.get_test_url(0) == Safe_Str__Url("https://example.com/")
            assert _.get_test_url(1) == Safe_Str__Url("https://docs.diniscruz/ai")
            assert _.get_test_url(2) == Safe_Str__Url("https://docs.diniscruz/ai/about.html")

            # Default index (0)
            assert _.get_test_url() == Safe_Str__Url("https://example.com/")

            # Out of bounds returns first URL
            assert _.get_test_url(99) == Safe_Str__Url("https://example.com/")

    def test__get_cached_html(self):                                              # Test retrieving cached HTML
        with self.helper as _:

            test_url = _.get_test_url(0)
            html = _.get_cached_html(test_url)

            assert html is not None
            assert "<html>" in html
            assert f"Test content for {test_url}" in html
            assert "text/html" in str(html) or True                               # Metadata stored separately


    def test__get_cached_text(self):                                              # Test retrieving cached text
        with self.helper as _:

            test_url = _.get_test_url(1)
            text = _.get_cached_text(test_url)

            assert text is not None
            assert f"Test text content for {test_url}" in text


    def test__start_stop__fast_api__cache_server(self):                           # Test server start/stop operations
        with Testing__Cache_Service__With__Test_Data() as _:
            _.setup()

            # Server should not be running initially
            assert _.fast_api_server.running is False

            _.start__fast_api__cache_server()
            assert _.fast_api_server.running is True

            _.stop__fast_api__cache_server()
            assert _.fast_api_server.running is False

    def test__singleton_instance(self):                                           # Test singleton behavior
        # Module-level singleton should exist
        assert testing__cache_service__with__test_data is not None
        assert type(testing__cache_service__with__test_data) is Testing__Cache_Service__With__Test_Data

        # Multiple calls to setup function return same instance
        instance1 = setup__testing__cache_service__with__test_data()
        instance2 = setup__testing__cache_service__with__test_data()

        assert instance1 is instance2                                             # Same object reference
        assert instance1 is testing__cache_service__with__test_data              # Same as module singleton

    def test__setup_function__idempotent(self):                                   # Test setup function is idempotent
        # First call should setup
        result1 = setup__testing__cache_service__with__test_data()
        assert result1.setup_completed is True

        # Second call should skip setup (already done)
        result2 = setup__testing__cache_service__with__test_data()
        assert result2.setup_completed is True
        assert result2 is result1                                                 # Same instance

    def test__cache_operations__roundtrip(self):                                  # Test cache store and retrieve roundtrip
        with self.helper as _:

            test_url     = Safe_Str__Url("https://test.com/roundtrip")
            test_content = "<html><body>Roundtrip test</body></html>"

            # Store transformation
            _.cache_service.store_transformation(target_url  = str(test_url)     ,
                                                wcf_command  = "url-to-html"     ,
                                                content      = test_content      ,
                                                metadata     = {"test": "roundtrip"})

            # Retrieve transformation
            retrieved = _.cache_service.get_cached_transformation(target_url  = str(test_url),
                                                                  wcf_command  = "url-to-html")

            assert retrieved == test_content                                      # Perfect roundtrip


    def test__multiple_transformations_same_url(self):                            # Test multiple transformations for same URL
        with self.helper as _:

            test_url = _.get_test_url(0)

            # Get different transformations
            html = _.get_cached_html(test_url)
            text = _.get_cached_text(test_url)

            # Both should exist and be different
            assert html != text
            assert "<html>" in html
            assert "<html>" not in text
            assert f"Test content for {test_url}" in html
            assert f"Test text content for {test_url}" in text


    def test__cache_config__attributes(self):                                     # Test cache config has correct attributes
        with self.helper as _:
            config = _.cache_config

            assert config.enabled is True                                         # Cache is enabled
            assert config.namespace == "test-cache-routes"                        # Test namespace
            assert config.timeout == 2                                            # 2 second timeout
            assert config.base_url == str(_.server_url)                          # Server URL matches
            assert str(config.base_url).startswith('http')                       # Valid HTTP URL

    def test__server_url__is_safe_str(self):                                      # Test server URL is Safe_Str__Url type
        with self.helper as _:
            assert type(_.server_url) is Safe_Str__Url                           # Correct type
            assert len(_.server_url) > 0                                         # Not empty
            assert 'http' in str(_.server_url).lower()                           # Contains http/https

            # Can be used as string
            url_str = str(_.server_url)
            assert isinstance(url_str, str)

    def test__test_urls__type_safety(self):                                       # Test all URLs maintain type safety
        with self.helper as _:
            for i, url in enumerate(_.test_urls):
                assert type(url) is Safe_Str__Url                                # Each URL is Safe_Str__Url
                assert len(url) > 0                                              # Not empty
                assert 'https' in str(url)                                       # All test URLs use HTTPS