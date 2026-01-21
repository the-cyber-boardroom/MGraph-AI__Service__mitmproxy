from unittest                                                                                   import TestCase
from osbot_utils.type_safe.primitives.core.Safe_Float                                           import Safe_Float
from mgraph_ai_service_mitmproxy.service.html_graph.HTML_Graph__Service__Client                 import HTML_Graph__Service__Client


class test_HTML_Graph__Service__Client__error_handling(TestCase):               # Test error scenarios

    def test_store_html__no_test_client_no_server(self):                        # Test error when no connection
        with HTML_Graph__Service__Client(base_url = "http://localhost:99999"    # Non-existent server
                                         ) as client:
            client.timeout = Safe_Float(0.5)                                    # Short timeout for fast failure
            url    = "https://example.com/test"
            html   = "<html></html>"
            result = client.store_html(url=url, html=html)

            assert result.success   is False
            assert result.error     is not None
            assert len(str(result.error)) > 0

    def test_load_html__no_test_client_no_server(self):                         # Test error when no connection
        with HTML_Graph__Service__Client(base_url = "http://localhost:99999"    # Non-existent server
                                         ) as client:
            client.timeout = Safe_Float(0.5)                                    # Short timeout for fast failure
            url    = "https://example.com/test"
            result = client.load_html(url)

            assert result.success   is False
            assert result.error     is not None