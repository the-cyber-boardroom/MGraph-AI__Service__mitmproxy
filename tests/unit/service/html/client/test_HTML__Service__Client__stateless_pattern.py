# ═══════════════════════════════════════════════════════════════════════════════
# Stateless Pattern Tests
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                           import TestCase
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Service__Request                            import Schema__HTML__Service__Request
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode                           import Enum__HTML__Transformation_Mode
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import fast_api__service__registry
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client                              import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.html.client.register_html_service                              import register_html_service__in_memory


class test_HTML__Service__Client__stateless_pattern(TestCase):

    @classmethod
    def setUpClass(cls):
        fast_api__service__registry.configs__save(clear_configs=True)
        register_html_service__in_memory()

    @classmethod
    def tearDownClass(cls):
        fast_api__service__registry.configs__restore()

    def test__multiple_client_instances__all_work(self):                        # Multiple clients all work
        client_1 = HTML__Service__Client()
        client_2 = HTML__Service__Client()
        client_3 = HTML__Service__Client()

        assert client_1.health() is True
        assert client_2.health() is True
        assert client_3.health() is True

    def test__multiple_client_instances__same_config(self):                     # All get same config
        client_1 = HTML__Service__Client()
        client_2 = HTML__Service__Client()

        config_1 = client_1.requests().config()
        config_2 = client_2.requests().config()

        assert config_1 is config_2                                             # Same config object

    def test__client_created_inline(self):                                      # Client can be created on the fly
        def some_business_logic(html):
            client = HTML__Service__Client()                                    # Create inline
            request = Schema__HTML__Service__Request(
                html                = html,
                transformation_mode = Enum__HTML__Transformation_Mode.ROUNDTRIP
            )
            return client.transform_html(request)

        response = some_business_logic("<html><body>Test</body></html>")
        assert response.success is True

