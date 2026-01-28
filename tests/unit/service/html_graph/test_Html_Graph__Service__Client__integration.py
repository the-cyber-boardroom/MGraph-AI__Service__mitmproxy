from unittest                                                                                   import TestCase
from mgraph_ai_service_html_graph.client.Html_Graph__Service__Client                    import Html_Graph__Service__Client
from mgraph_ai_service_html_graph.client.register_html_graph_service                    import register_html_graph_service__in_memory
from mgraph_ai_service_html_graph.schemas.flet.domain.Schema__Html__Load__Response import Schema__Html__Load__Response
from mgraph_ai_service_html_graph.schemas.flet.domain.Schema__Html__Store__Response import Schema__Html__Store__Response


class test_Html_Graph__Service__Client__integration(TestCase):                  # Integration tests

    @classmethod
    def setUpClass(cls):                                                        # Setup in-memory HTML Graph service
        register_html_graph_service__in_memory()
        cls.client      = Html_Graph__Service__Client()#.set_test_client(cls.test_client)
        cls.test_url    = "https://test.example.com/integration-test"
        cls.test_html   = "<html><body><h1>Integration Test</h1></body></html>"

    def test_store_html(self):                                                  # Test storing HTML
        result = self.client.store_html(url  = self.test_url ,
                                        html = self.test_html)

        assert type(result)      is Schema__Html__Store__Response
        assert result.success    is True
        assert result.char_count > 0
        assert len(str(result.cache_key)) > 0

    def test_load_html__cache_miss(self):                                       # Test loading non-existent entry
        url    = "https://nonexistent.example.com/page-that-does-not-exist"
        result = self.client.load_html(url)

        assert type(result)      is Schema__Html__Load__Response
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

