# ═══════════════════════════════════════════════════════════════════════════════
# Stateless Pattern Tests
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                                   import TestCase
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                           import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.service.semantic_text.register_semantic_text_service                           import register_semantic_text_service__in_memory
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Request    import Schema__Semantic_Text__Transformation__Request
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                               import fast_api__service__registry


class test_Semantic_Text__Service__Client__stateless_pattern(TestCase):

    @classmethod
    def setUpClass(cls):
        fast_api__service__registry.configs__save(clear_configs=True)
        register_semantic_text_service__in_memory()

    @classmethod
    def tearDownClass(cls):
        fast_api__service__registry.configs__restore()

    def test__multiple_client_instances__all_work(self):                        # Multiple clients all work
        client_1 = Semantic_Text__Service__Client()
        client_2 = Semantic_Text__Service__Client()
        client_3 = Semantic_Text__Service__Client()

        assert client_1.health() is True
        assert client_2.health() is True
        assert client_3.health() is True

    def test__multiple_client_instances__same_config(self):                     # All get same config
        client_1 = Semantic_Text__Service__Client()
        client_2 = Semantic_Text__Service__Client()

        config_1 = client_1.requests().config()
        config_2 = client_2.requests().config()

        assert config_1 is config_2                                             # Same config object

    def test__client_created_inline(self):                                      # Client can be created on the fly
        def some_business_logic(hash_mapping):
            client  = Semantic_Text__Service__Client()                          # Create inline
            request = Schema__Semantic_Text__Transformation__Request(hash_mapping=hash_mapping)
            return client.transform_text(request)

        response = some_business_logic({"abc1234567": "Test text"})
        assert response.success is True

