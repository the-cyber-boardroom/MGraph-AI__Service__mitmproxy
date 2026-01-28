# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests - IN_MEMORY Mode
# ═══════════════════════════════════════════════════════════════════════════════

from unittest                                                                                                   import TestCase
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                           import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.service.semantic_text.register_semantic_text_service                           import register_semantic_text_service__in_memory
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Request    import Schema__Semantic_Text__Transformation__Request
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Response   import Schema__Semantic_Text__Transformation__Response
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Transformation__Mode            import Enum__Text__Transformation__Mode
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Transformation__Engine_Mode     import Enum__Text__Transformation__Engine_Mode
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Classification__Logic_Operator        import Enum__Classification__Logic_Operator
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Classification__Criteria        import Enum__Text__Classification__Criteria
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Classification__Filter_Mode           import Enum__Classification__Filter_Mode
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Classification__Criterion_Filter          import Schema__Classification__Criterion_Filter
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                               import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode             import Enum__Fast_API__Service__Registry__Client__Mode
from osbot_utils.testing.__                                                                                     import __
from osbot_utils.type_safe.primitives.core.Safe_Float                                                           import Safe_Float


class test_Semantic_Text__Service__Client__integration(TestCase):

    # Shared test data
    test_hash_single   = "aaa1234567"
    test_text_single   = "Some Text"
    test_hash_mapping  = {test_hash_single: test_text_single}
    test_hash_multiple = {"aaa1234567": "Positive text"    ,
                          "bbb2345678": "Negative content" ,
                          "ccc3456789": "Neutral statement"}

    @classmethod
    def setUpClass(cls):                                                        # Setup once for all tests
        fast_api__service__registry.configs__save(clear_configs=True)
        register_semantic_text_service__in_memory()

        cls.client = Semantic_Text__Service__Client()

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
    # Transform Text - Basic Tests
    # ───────────────────────────────────────────────────────────────────────────

    def test__transform_text__success__default_params(self):                    # Test default transformation
        request  = Schema__Semantic_Text__Transformation__Request(hash_mapping=self.test_hash_mapping)
        response = self.client.transform_text(request)

        assert type(response) is Schema__Semantic_Text__Transformation__Response
        assert response.success             is True
        assert response.error_message       is None
        assert response.total_hashes        == 1
        assert response.transformed_hashes  == 1
        assert response.transformation_mode == 'xxx'

        assert self.test_hash_single in response.transformed_mapping
        assert response.transformed_mapping[self.test_hash_single] == 'xxxx xxxx'  # "Some Text" → "xxxx xxxx"

    def test__transform_text__success__multiple_hashes(self):                   # Test multiple hashes
        request  = Schema__Semantic_Text__Transformation__Request(hash_mapping=self.test_hash_multiple)
        response = self.client.transform_text(request)

        assert response.success            is True
        assert response.total_hashes       == 3
        assert response.transformed_hashes == 3
        assert len(response.transformed_mapping) == 3

        for hash_id in self.test_hash_multiple.keys():
            assert hash_id in response.transformed_mapping

    def test__transform_text__with_engine_mode(self):                           # Test with specific engine
        request = Schema__Semantic_Text__Transformation__Request(
            hash_mapping = self.test_hash_mapping                          ,
            engine_mode  = Enum__Text__Transformation__Engine_Mode.TEXT_HASH
        )
        response = self.client.transform_text(request)

        assert response.success is True
        assert response.transformation_mode == 'xxx'

    def test__transform_text__with_transformation_mode(self):                   # Test with specific transformation
        request = Schema__Semantic_Text__Transformation__Request(
            hash_mapping        = self.test_hash_mapping               ,
            transformation_mode = Enum__Text__Transformation__Mode.HASHES
        )
        response = self.client.transform_text(request)

        assert response.success             is True
        assert response.transformation_mode == 'hashes'

    # ───────────────────────────────────────────────────────────────────────────
    # Transform Text - With Filters
    # ───────────────────────────────────────────────────────────────────────────

    def test__transform_text__with_filter(self):                                # Test with sentiment filter
        filter_criterion = Schema__Classification__Criterion_Filter(
            criterion   = Enum__Text__Classification__Criteria.POSITIVE,
            filter_mode = Enum__Classification__Filter_Mode.ABOVE      ,
            threshold   = Safe_Float(0.7)
        )

        request = Schema__Semantic_Text__Transformation__Request(
            hash_mapping      = self.test_hash_multiple,
            criterion_filters = [filter_criterion]     ,
            logic_operator    = Enum__Classification__Logic_Operator.AND
        )
        response = self.client.transform_text(request)

        assert response.success      is True
        assert response.total_hashes == 3

    def test__transform_text__scenario_mask_negative_content(self):             # Scenario: Mask negative content
        filter_negative = Schema__Classification__Criterion_Filter(
            criterion   = Enum__Text__Classification__Criteria.NEGATIVE,
            filter_mode = Enum__Classification__Filter_Mode.ABOVE      ,
            threshold   = Safe_Float(0.7)
        )

        request = Schema__Semantic_Text__Transformation__Request(
            hash_mapping        = self.test_hash_multiple              ,
            criterion_filters   = [filter_negative]                    ,
            transformation_mode = Enum__Text__Transformation__Mode.XXX ,
            engine_mode         = Enum__Text__Transformation__Engine_Mode.TEXT_HASH
        )
        response = self.client.transform_text(request)

        assert response.success             is True
        assert response.transformation_mode == 'xxx'
        assert response.total_hashes        == 3

    # ───────────────────────────────────────────────────────────────────────────
    # Response Validation
    # ───────────────────────────────────────────────────────────────────────────

    def test__transform_text__response_obj_validation(self):                    # Test .obj() response structure
        request  = Schema__Semantic_Text__Transformation__Request(hash_mapping=self.test_hash_mapping)
        response = self.client.transform_text(request)

        assert response.obj() == __(error_message       = None                        ,
                                    transformed_mapping = __(aaa1234567='xxxx xxxx')  ,
                                    transformation_mode = 'xxx'                       ,
                                    success             = True                        ,
                                    total_hashes        = 1                           ,
                                    transformed_hashes  = 1                           )

