from unittest                                                                                   import TestCase
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace           import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                        import Safe_Str__Url
from osbot_utils.utils.Objects                                                                  import base_types
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_Float                                           import Safe_Float
from mgraph_ai_service_mitmproxy.service.html_graph.HTML_Graph__Service__Client                 import HTML_Graph__Service__Client
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.consts__html_graph                  import DEFAULT__HTML_GRAPH__NAMESPACE, DEFAULT__HTML_GRAPH__TIMEOUT


class test_HTML_Graph__Service__Client(TestCase):                               # Test client initialization

    def test__init__(self):                                                     # Test auto-initialization with defaults
        with HTML_Graph__Service__Client() as _:
            assert type(_)           is HTML_Graph__Service__Client
            assert Type_Safe         in base_types(_)
            assert type(_.base_url)  is Safe_Str__Url
            assert type(_.namespace) is Safe_Str__Cache__Namespace
            assert type(_.timeout)   is Safe_Float
            assert str(_.base_url)   == ''
            assert str(_.namespace)  == DEFAULT__HTML_GRAPH__NAMESPACE
            assert float(_.timeout)  == DEFAULT__HTML_GRAPH__TIMEOUT
            assert _.test_client     is None

    def test_setup(self):                                                       # Test setup method returns self
        with HTML_Graph__Service__Client() as _:
            result = _.setup()
            assert result            is _                                       # Returns self for chaining

    def test_set_test_client(self):                                             # Test TestClient injection
        with HTML_Graph__Service__Client() as _:
            mock_client = "test_client_object"                                  # Placeholder
            result      = _.set_test_client(mock_client)
            assert result            is _                                       # Returns self for chaining
            assert _.test_client     == mock_client

    def test_get_auth_headers(self):                                            # Test header generation
        with HTML_Graph__Service__Client() as _:
            headers = _.get_auth_headers()
            assert type(headers)     is dict
            assert "Content-Type"    in headers
            assert headers["Content-Type"] == "application/json"

