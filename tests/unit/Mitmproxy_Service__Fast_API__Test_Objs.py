from fastapi                                                                    import FastAPI
from mgraph_ai_service_cache.fast_api.Cache_Service__Fast_API                   import Cache_Service__Fast_API
from mgraph_ai_service_cache_client.schemas.consts.const__Storage               import ENV_VAR__CACHE__SERVICE__STORAGE_MODE
from mgraph_ai_service_html.html__fast_api.Html_Service__Fast_API               import Html_Service__Fast_API
from mgraph_ai_service_semantic_text.fast_api.Semantic_Text__Service__Fast_API  import Semantic_Text__Service__Fast_API
from osbot_aws.testing.Temp__Random__AWS_Credentials                            import Temp_AWS_Credentials
from osbot_fast_api.api.Fast_API                                                import ENV_VAR__FAST_API__AUTH__API_KEY__NAME, ENV_VAR__FAST_API__AUTH__API_KEY__VALUE
from osbot_fast_api.utils.Fast_API_Server                                       import Fast_API_Server
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config            import Serverless__Fast_API__Config
from osbot_local_stack.local_stack.Local_Stack                                  import Local_Stack
from osbot_utils.type_safe.Type_Safe                                            import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Random_Guid           import Random_Guid
from osbot_utils.utils.Env                                                      import set_env
from starlette.testclient                                                       import TestClient
from mgraph_ai_service_mitmproxy.fast_api.Mitmproxy__Service__Fast_API          import Mitmproxy__Service__Fast_API

TEST_API_KEY__NAME = 'key-used-in-pytest'
TEST_API_KEY__VALUE = Random_Guid()

class Mitmproxy_Service__Fast_API__Test_Objs(Type_Safe):
    fast_api        : Mitmproxy__Service__Fast_API     = None
    fast_api__app   : FastAPI               = None
    fast_api__client: TestClient            = None
    local_stack     : Local_Stack           = None
    setup_completed : bool                  = False

service_fast_api_test_objs = Mitmproxy_Service__Fast_API__Test_Objs()


def setup_local_stack() -> Local_Stack:
    Temp_AWS_Credentials().with_localstack_credentials()
    local_stack = Local_Stack().activate()
    return local_stack

def setup__service_fast_api_test_objs():
    with service_fast_api_test_objs as _:
        if service_fast_api_test_objs.setup_completed is False:
            _.fast_api         = Mitmproxy__Service__Fast_API().setup()
            _.fast_api__app    = _.fast_api.app()
            _.fast_api__client = _.fast_api.client()
            _.local_stack      = setup_local_stack()
            _.setup_completed  = True

            set_env(ENV_VAR__FAST_API__AUTH__API_KEY__NAME , TEST_API_KEY__NAME)
            set_env(ENV_VAR__FAST_API__AUTH__API_KEY__VALUE, TEST_API_KEY__VALUE)
    return service_fast_api_test_objs



### Services objects

from threading                                                             import Lock
from typing                                                                import Type, TypeVar, Generic
from osbot_utils.type_safe.Type_Safe                                       import Type_Safe
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url   import Safe_Str__Url


# todo: move this to the Fast_API project (since this is used in multiple projects)

T = TypeVar("T", bound="FastAPI__Service__Test_Objs")                      # Generic type for service test objs

# -------------------------------------------------------------------------------
# Base Schema for all FastAPI Test Objects
# -------------------------------------------------------------------------------
class FastAPI__Service__Test_Objs(Type_Safe):                              # Shared attributes across FastAPI services
    config          : Serverless__Fast_API__Config                         # FastAPI config (no API key)
    fast_api_server : Fast_API_Server                                      # FastAPI server wrapper
    app             : FastAPI                                              # Underlying FastAPI app
    server_url      : Safe_Str__Url                                        # Root server URL (without trailing /)


# -------------------------------------------------------------------------------
# Generic Singleton Factory for FastAPI services
# -------------------------------------------------------------------------------
class Base__FastAPI__Service__Singleton(Generic[T]):                       # Base factory with singleton caching
    instance     : T          = None                                      # Cached instance
    service_cls  : Type_Safe  = None                                      # Service class, e.g. Html_Service__Fast_API
    test_obj_cls : Type[T]    = None                                      # Test object class, e.g. Html_Service__Fast_API__Test_Objs

    @classmethod
    def create_instance(cls) -> T:                                        # Build new singleton instance
        config = Serverless__Fast_API__Config(enable_api_key=False)        # Create config without API key

        with cls.service_cls(config=config) as service:                   # Context-managed setup
            service.setup()
            app             = service.app()
            fast_api_server = Fast_API_Server(app=app)
            server_url      = fast_api_server.url().rstrip("/")

            return cls.test_obj_cls(fast_api_server = fast_api_server     ,
                                    app             = app                 ,
                                    config          = config              ,
                                    server_url      = server_url          )

    @classmethod
    def get_instance(cls) -> T:                                            # Retrieve or lazily create singleton
        if cls.instance is None:
            cls.instance = cls.create_instance()
        return cls.instance


# -------------------------------------------------------------------------------
# HTML Service Singleton
# -------------------------------------------------------------------------------
class Html_Service__Fast_API__Test_Objs(FastAPI__Service__Test_Objs):      # HTML FastAPI service configuration
    pass

class Html_Service__Fast_API__Singleton(Base__FastAPI__Service__Singleton[Html_Service__Fast_API__Test_Objs]):
    service_cls  = Html_Service__Fast_API
    test_obj_cls = Html_Service__Fast_API__Test_Objs

def get__html_service__fast_api_server() -> Html_Service__Fast_API__Test_Objs:
    return Html_Service__Fast_API__Singleton.get_instance()


# -------------------------------------------------------------------------------
# CACHE Service Singleton
# -------------------------------------------------------------------------------
class Cache_Service__Fast_API__Test_Objs(FastAPI__Service__Test_Objs):     # Cache FastAPI service configuration
    pass

class Cache_Service__Fast_API__Singleton(Base__FastAPI__Service__Singleton[Cache_Service__Fast_API__Test_Objs]):
    service_cls  = Cache_Service__Fast_API
    test_obj_cls = Cache_Service__Fast_API__Test_Objs

def get__cache_service__fast_api_server() -> Cache_Service__Fast_API__Test_Objs:
    set_env(ENV_VAR__CACHE__SERVICE__STORAGE_MODE, 'memory')                            # configure the cache service to use an in-memory db (instead of trying to use S3)
    return Cache_Service__Fast_API__Singleton.get_instance()

# -------------------------------------------------------------------------------
# Mitmproxy Service Singleton
# -------------------------------------------------------------------------------
class Mitmproxy_Service__Fast_API__Test_Objs__Http(FastAPI__Service__Test_Objs):     # Cache FastAPI service configuration
    pass

class Mitmproxy_Service__Fast_API__Singleton(Base__FastAPI__Service__Singleton[Mitmproxy_Service__Fast_API__Test_Objs__Http]):
    service_cls  = Mitmproxy__Service__Fast_API
    test_obj_cls = Mitmproxy_Service__Fast_API__Test_Objs__Http

def get__mitmproxy_service__fast_api_server() -> Cache_Service__Fast_API__Test_Objs:
    set_env(ENV_VAR__CACHE__SERVICE__STORAGE_MODE, 'memory')                            # configure the cache service to use an in-memory db (instead of trying to use S3)
    return Mitmproxy_Service__Fast_API__Singleton.get_instance()

# -------------------------------------------------------------------------------
# HTML Service Singleton
# -------------------------------------------------------------------------------
class Semantic_Text_Service__Fast_API__Test_Objs(FastAPI__Service__Test_Objs):      # HTML FastAPI service configuration
    pass

class Semantic_Text_Service__Fast_API__Singleton(Base__FastAPI__Service__Singleton[Semantic_Text_Service__Fast_API__Test_Objs]):
    service_cls  = Semantic_Text__Service__Fast_API
    test_obj_cls = Semantic_Text_Service__Fast_API__Test_Objs

def get__semantic_text_service__fast_api_server() -> Semantic_Text_Service__Fast_API__Test_Objs:
    return Semantic_Text_Service__Fast_API__Singleton.get_instance()
