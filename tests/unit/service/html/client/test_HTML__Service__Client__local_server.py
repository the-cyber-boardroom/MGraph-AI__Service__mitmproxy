# ═══════════════════════════════════════════════════════════════════════════════
# Local Server Tests (with actual HTTP transport)
# This is the pattern for testing with a real local server
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                           import TestCase
from mgraph_ai_service_html.html__fast_api.Html_Service__Fast_API                                       import Html_Service__Fast_API
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                                    import Serverless__Fast_API__Config
from osbot_fast_api.utils.Fast_API_Server                                                               import Fast_API_Server
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Service__Request                            import Schema__HTML__Service__Request
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode                           import Enum__HTML__Transformation_Mode
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode     import Enum__Fast_API__Service__Registry__Client__Mode
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client                              import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.html.client.register_html_service                              import register_html_service__local_server


class test_HTML__Service__Client__local_server(TestCase):
    """Tests using actual HTTP transport against a local server.

    This tests the REMOTE mode path with real network calls.
    """

    @classmethod
    def setUpClass(cls):
        fast_api__service__registry.configs__save(clear_configs=True)

        # Create and start local server
        cls.serverless_config = Serverless__Fast_API__Config(enable_api_key=False)
        cls.html_fast_api     = Html_Service__Fast_API(config=cls.serverless_config).setup()
        cls.fast_api_server   = Fast_API_Server(app=cls.html_fast_api.app())
        cls.server_url        = cls.fast_api_server.url().rstrip("/")
        cls.fast_api_server.start()

        # Register with REMOTE mode pointing to local server
        register_html_service__local_server(base_url=cls.server_url)

        cls.client = HTML__Service__Client()

    @classmethod
    def tearDownClass(cls):
        cls.fast_api_server.stop()
        fast_api__service__registry.configs__restore()

    def test__health(self):                                                     # Test health via HTTP
        assert self.client.health() is True

    def test__config__is_remote_mode(self):                                     # Verify REMOTE mode
        config = self.client.requests().config()
        assert config.mode          == Enum__Fast_API__Service__Registry__Client__Mode.REMOTE
        assert str(config.base_url) == self.server_url

    def test__transform_html__via_http(self):                                   # Test actual HTTP call
        html = "<html><body><p>Test via HTTP</p></body></html>"

        request  = Schema__HTML__Service__Request(html                = html                                      ,
                                                  transformation_mode = Enum__HTML__Transformation_Mode.ROUNDTRIP)
        response = self.client.transform_html(request)

        assert response.status_code == 200
        assert response.success     is True
        assert '<p>Test via HTTP</p>' in response.body
