# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests - IN_MEMORY Mode
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                           import TestCase
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Service__Request                            import Schema__HTML__Service__Request
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode                           import Enum__HTML__Transformation_Mode
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode     import Enum__Fast_API__Service__Registry__Client__Mode
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client                              import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.html.client.register_html_service                              import register_html_service__in_memory


class test_HTML__Service__Client__integration(TestCase):

    @classmethod
    def setUpClass(cls):                                                        # Setup once for all tests
        fast_api__service__registry.configs__save(clear_configs=True)
        register_html_service__in_memory()

        cls.client = HTML__Service__Client()

    @classmethod
    def tearDownClass(cls):                                                     # Restore global registry
        fast_api__service__registry.configs__restore()

    # ───────────────────────────────────────────────────────────────────────────
    # Health Check Tests
    # ───────────────────────────────────────────────────────────────────────────

    def test__health__returns_true(self):                                       # Test health() method
        assert self.client.health() is True

    # ───────────────────────────────────────────────────────────────────────────
    # Config Lookup Tests
    # ───────────────────────────────────────────────────────────────────────────

    def test__requests__config__returns_registered_config(self):                # Test config lookup
        config = self.client.requests().config()

        assert config is not None
        assert config.mode == Enum__Fast_API__Service__Registry__Client__Mode.IN_MEMORY

    def test__requests__config__has_fast_api_app(self):                         # Test config has app
        config = self.client.requests().config()
        assert config.fast_api_app is not None

    # ───────────────────────────────────────────────────────────────────────────
    # Transform HTML Tests
    # ───────────────────────────────────────────────────────────────────────────

    def test__transform_html__roundtrip(self):                                  # Test HTML roundtrip
        html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"

        request  = Schema__HTML__Service__Request(html                = html                                      ,
                                                  transformation_mode = Enum__HTML__Transformation_Mode.ROUNDTRIP)
        response = self.client.transform_html(request)

        assert response.status_code == 200
        assert response.success     is True
        assert '<title>Test</title>' in response.body
        assert '<p>Content</p>'      in response.body

    def test__transform_html__hashes_mode(self):                                # Test hashes transformation
        html = "<html><body><p>Test paragraph</p></body></html>"

        request  = Schema__HTML__Service__Request(html                = html                                   ,
                                                  transformation_mode = Enum__HTML__Transformation_Mode.HASHES)
        response = self.client.transform_html(request)

        assert response.status_code == 200
        assert response.success     is True
        assert response.body       != ""

    def test__transform_html__dict_mode(self):                                  # Test dict transformation
        html = "<html><body>test</body></html>"

        request  = Schema__HTML__Service__Request(html                = html                                 ,
                                                  transformation_mode = Enum__HTML__Transformation_Mode.DICT)
        response = self.client.transform_html(request)

        assert response.status_code == 200
        assert response.success     is True

    def test__transform_html__empty_html(self):                                 # Test with empty HTML
        request = Schema__HTML__Service__Request(html                = ""                                    ,
                                                 transformation_mode = Enum__HTML__Transformation_Mode.HASHES)

        response = self.client.transform_html(request)

        assert response.success is False                                        # Should handle gracefully

    def test__transform_html__malformed_html(self):                             # Test with malformed HTML
        request = Schema__HTML__Service__Request(
            html                = "<html><body><p>Unclosed paragraph</body></html>",
            transformation_mode = Enum__HTML__Transformation_Mode.HASHES
        )

        response = self.client.transform_html(request)

        assert response.status_code == 200                                      # Parser should handle gracefully
        assert response.success     is True

    def test__transform_html__all_modes(self):                                  # Test all transformation modes
        html = "<html><body><p>Test paragraph</p></body></html>"

        modes_to_test = [Enum__HTML__Transformation_Mode.HASHES    ,
                         Enum__HTML__Transformation_Mode.XXX       ,
                         Enum__HTML__Transformation_Mode.ROUNDTRIP ,
                         Enum__HTML__Transformation_Mode.DICT      ]

        for mode in modes_to_test:
            request  = Schema__HTML__Service__Request(html=html, transformation_mode=mode)
            response = self.client.transform_html(request)

            assert response.status_code == 200                                  # All valid modes should succeed
            assert response.success     is True
            assert response.body       != ""
