from unittest                                                                                       import TestCase
from mgraph_ai_service_cache_client.client.cache_service.register_cache_service                     import register_cache_service__in_memory
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Storage_Mode                    import Enum__Cache__Storage_Mode
from mgraph_ai_service_cache_client.schemas.consts.const__Fast_API                                  import ENV_VAR__CACHE__SERVICE__BUCKET_NAME
from mgraph_ai_service_cache_client.schemas.consts.const__Storage                                   import ENV_VAR__CACHE__SERVICE__STORAGE_MODE
from osbot_aws.testing.Temp__Random__AWS_Credentials                                                import Temp_AWS_Credentials
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                   import fast_api__service__registry
from osbot_local_stack.local_stack.Local_Stack                                                      import Local_Stack
from osbot_utils.testing.Temp_Env_Vars                                                              import Temp_Env_Vars
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                                import Proxy__Cache__Service
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Config                        import Schema__Cache__Config
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Stats                         import Schema__Cache__Stats
from mgraph_ai_service_mitmproxy.service.proxy.inject.Proxy__Inject__Service                        import EMPTY_STUB, INJECT_DATA_FILE_ID, Proxy__Inject__Service


FULL_FILTER = 'window.__localStackFilter = { active: true };'
DOMAIN      = 'inject-localstack.example.com'


class test_Proxy__Inject__Service__localstack(TestCase):

    @classmethod
    def setUpClass(cls):
        fast_api__service__registry.configs__save()
        cls.temp_env_vars = Temp_Env_Vars(env_vars={
            ENV_VAR__CACHE__SERVICE__BUCKET_NAME  : 'akeia-inject-localstack-tests',
            ENV_VAR__CACHE__SERVICE__STORAGE_MODE : Enum__Cache__Storage_Mode.S3.value,
        }).set_vars()
        Temp_AWS_Credentials().with_localstack_credentials()
        cls.local_stack = Local_Stack().activate()
        register_cache_service__in_memory()

        cache_config = Schema__Cache__Config(enabled=True, namespace='inject-localstack-tests')
        cache_service = Proxy__Cache__Service(cache_config = cache_config          ,
                                              stats        = Schema__Cache__Stats())
        cls.inject_service = Proxy__Inject__Service(cache_service=cache_service)

    @classmethod
    def tearDownClass(cls):
        fast_api__service__registry.configs__restore()
        cls.temp_env_vars.restore_vars()

    def test_confirmed_s3_miss_creates_stub_then_s3_replacement_is_served(self):
        first_result = self.inject_service.resolve_script(DOMAIN)

        assert first_result == EMPTY_STUB
        assert self.inject_service._cache_id is not None

        store_result = self.inject_service.cache_service.cache_client.data_store().data__store_string__with__id_and_key(
            cache_id     = self.inject_service._cache_id,
            namespace    = self.inject_service.cache_service.cache_config.namespace,
            data_key     = self.inject_service.data_key_for_domain(DOMAIN),
            data_file_id = INJECT_DATA_FILE_ID,
            body         = FULL_FILTER)
        assert store_result

        second_result = self.inject_service.resolve_script(DOMAIN)

        assert second_result == FULL_FILTER
