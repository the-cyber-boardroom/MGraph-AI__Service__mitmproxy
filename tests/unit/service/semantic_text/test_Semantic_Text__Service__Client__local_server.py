# ═══════════════════════════════════════════════════════════════════════════════
# Local Server Tests (with actual HTTP transport)
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                                   import TestCase
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                           import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.service.semantic_text.register_semantic_text_service                           import register_semantic_text_service__local_server
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Request    import Schema__Semantic_Text__Transformation__Request
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                               import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode             import Enum__Fast_API__Service__Registry__Client__Mode


class test_Semantic_Text__Service__Client__local_server(TestCase):
    """Tests using actual HTTP transport against a local server."""

    @classmethod
    def setUpClass(cls):
        from mgraph_ai_service_semantic_text.fast_api.Semantic_Text__Service__Fast_API import Semantic_Text__Service__Fast_API
        from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config           import Serverless__Fast_API__Config
        from osbot_fast_api.utils.Fast_API_Server                                      import Fast_API_Server

        fast_api__service__registry.configs__save(clear_configs=True)

        # Create and start local server
        cls.serverless_config      = Serverless__Fast_API__Config(enable_api_key=False)
        cls.semantic_text_fast_api = Semantic_Text__Service__Fast_API(config=cls.serverless_config).setup()
        cls.fast_api_server        = Fast_API_Server(app=cls.semantic_text_fast_api.app())
        cls.server_url             = cls.fast_api_server.url().rstrip("/")
        cls.fast_api_server.start()

        # Register with REMOTE mode pointing to local server
        register_semantic_text_service__local_server(base_url=cls.server_url)

        cls.client = Semantic_Text__Service__Client()

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

    def test__transform_text__via_http(self):                                   # Test actual HTTP call
        request  = Schema__Semantic_Text__Transformation__Request(hash_mapping={"abc1234567": "Test via HTTP"})
        response = self.client.transform_text(request)

        assert response.success is True
        assert "abc1234567" in response.transformed_mapping
