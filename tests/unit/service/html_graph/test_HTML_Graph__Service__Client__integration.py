import pytest
from unittest                                                                                   import TestCase

from osbot_utils.utils.Env import get_env
from osbot_utils.utils.Files                                                                    import path_combine
from mgraph_ai_service_mitmproxy.service.html_graph.HTML_Graph__Service__Client                 import HTML_Graph__Service__Client
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Load_Result     import Schema__HTML_Graph__Load_Result
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Store_Result    import Schema__HTML_Graph__Store_Result
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.consts__html_graph                  import ENV_VAR__AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__BASE_URL
from tests.unit.service.html_graph.Html_Graph__Client__Test_Objs                                import setup__html_graph_client__test_objs, load_local_dotenv


class test_HTML_Graph__Service__Client__integration(TestCase):                  # Integration tests

    @classmethod
    def setUpClass(cls):                                                        # Setup in-memory HTML Graph service
        cls.dot_env_file = path_combine(__file__, '../.local-cache.env')
        if load_local_dotenv(cls.dot_env_file) is False:
            pytest.skip('test needs local env vars set')
        test_objs       = setup__html_graph_client__test_objs()
        cls.test_client = test_objs.fast_api__client
        cls.client      = HTML_Graph__Service__Client().set_test_client(cls.test_client)
        cls.test_url    = "https://test.example.com/integration-test"
        cls.test_html   = "<html><body><h1>Integration Test</h1></body></html>"
        if get_env(ENV_VAR__AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__BASE_URL)  is None:
            pytest.skip("these tests need env-var")                                     # todo: BUG, fix this on load_html so that we can run the tests

    def test_store_html(self):                                                  # Test storing HTML
        result = self.client.store_html(url  = self.test_url ,
                                        html = self.test_html)

        assert type(result)      is Schema__HTML_Graph__Store_Result
        assert result.success    is True
        assert result.char_count > 0
        assert len(str(result.cache_key)) > 0

    def test_load_html__cache_miss(self):                                       # Test loading non-existent entry
        url    = "https://nonexistent.example.com/page-that-does-not-exist"
        result = self.client.load_html(url)

        assert type(result)      is Schema__HTML_Graph__Load_Result
        assert result.success    is True
        assert result.found      is False

    def test_store_then_load(self):                                             # Test store followed by load
        url  = "https://roundtrip.example.com/test-page"
        html = "<html><body>Round Trip Test Content</body></html>"

        # Store
        store_result = self.client.store_html(url=url, html=html)
        assert store_result.success is True

        # Load
        load_result = self.client.load_html(url)
        assert load_result.success  is True
        assert load_result.found    is True
        assert "Round Trip Test Content" in str(load_result.html)

    def test_store_overwrites_existing(self):                                   # Test that store updates existing entry
        url   = "https://overwrite.example.com/page"
        html1 = "<html><body>Version 1</body></html>"
        html2 = "<html><body>Version 2 - Updated</body></html>"

        # Store first version
        self.client.store_html(url=url, html=html1)

        # Store second version
        self.client.store_html(url=url, html=html2)

        # Load should return second version
        result = self.client.load_html(url)
        assert result.found         is True
        assert "Version 2"          in str(result.html)
        assert "Version 1"          not in str(result.html)

    def test_multiple_urls(self):                                               # Test caching multiple URLs
        urls_and_content = {"https://multi.example.com/page1": "<html>Page 1</html>",
                            "https://multi.example.com/page2": "<html>Page 2</html>",
                            "https://multi.example.com/page3": "<html>Page 3</html>"}

        # Store all
        for url, html in urls_and_content.items():
            result = self.client.store_html(url=url, html=html)
            assert result.success is True

        # Load and verify each
        for url, expected_html in urls_and_content.items():
            result = self.client.load_html(url)
            assert result.found   is True
            assert str(expected_html) in str(result.html)

