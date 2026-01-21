import re
from unittest                                                                                   import TestCase
import pytest

from mgraph_ai_service_mitmproxy.service.html_graph.HTML_Graph__Service__Client                 import HTML_Graph__Service__Client

class test_HTML_Graph__Service__Client__url_to_cache_key(TestCase):             # Test URL conversion

    @classmethod
    def setUpClass(cls):                                                        # Setup shared client
        cls.client = HTML_Graph__Service__Client()

    def test_simple_url(self):                                                  # Test basic URL conversion
        url       = "https://example.com/about"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/about"

    def test_url_with_root_path(self):                                          # Test homepage URL
        url       = "https://example.com/"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/root"

    def test_url_without_trailing_slash(self):                                  # Test URL without trailing slash
        url       = "https://example.com"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/root"

    def test_url_with_nested_path(self):                                        # Test multi-level path
        url       = "https://example.com/blog/post/123"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/blog/post/123"

    def test_url_with_subdomain(self):                                          # Test subdomain handling
        url       = "https://api.example.com/v1/users"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "api.example.com/v1/users"

    def test_url_with_query_stripped(self):                                     # Test query string removal
        url       = "https://example.com/search?q=test&page=1"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/search"                        # Query stripped

    def test_url_with_fragment_stripped(self):                                  # Test fragment removal
        url       = "https://example.com/page#section"
        cache_key = self.client.url_to_cache_key(url)
        assert str(cache_key)    == "example.com/page"                          # Fragment stripped

    def test_invalid_url(self):                                                 # Test fallback for invalid URL
        url       = "/just/a/path"
        error_message = "Parameter 'url' expected type <class 'osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url.Safe_Str__Url'>, but got <class 'str'>"
        with pytest.raises(ValueError, match=re.escape(error_message)):
            self.client.url_to_cache_key(url)


