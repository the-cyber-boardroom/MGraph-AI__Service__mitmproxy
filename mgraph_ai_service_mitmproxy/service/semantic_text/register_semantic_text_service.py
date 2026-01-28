# ═══════════════════════════════════════════════════════════════════════════════
# register_semantic_text_service
# Registration helpers for Semantic Text Service
# ═══════════════════════════════════════════════════════════════════════════════

from mgraph_ai_service_semantic_text.fast_api.Semantic_Text__Service__Fast_API                          import Semantic_Text__Service__Fast_API
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                                    import Serverless__Fast_API__Config
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import Fast_API__Service__Registry
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.Fast_API__Service__Registry__Client__Config               import Fast_API__Service__Registry__Client__Config
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode     import Enum__Fast_API__Service__Registry__Client__Mode
from osbot_utils.utils.Env                                                                              import get_env
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                   import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.schemas.semantic_text.const__semantic_text                             import (ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL ,
                                                                                                                ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_NAME  ,
                                                                                                                ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_VALUE )


def register_semantic_text_service__in_memory(registry      : Fast_API__Service__Registry = None,
                                              return_client : bool                        = False
                                             ):
    """Register Semantic Text Service config for IN_MEMORY mode.
    
    Creates FastAPI app and registers config. Use for testing.
    """
    if registry is None:
        registry = fast_api__service__registry

    
    serverless_config = Serverless__Fast_API__Config(enable_api_key=False)
    fast_api          = Semantic_Text__Service__Fast_API(config=serverless_config).setup()
    
    config = Fast_API__Service__Registry__Client__Config(
        mode         = Enum__Fast_API__Service__Registry__Client__Mode.IN_MEMORY,
        fast_api_app = fast_api.app()                                           ,
        fast_api     = fast_api                                                 )
    
    registry.register(Semantic_Text__Service__Client, config)
    
    if return_client:
        return Semantic_Text__Service__Client()


def register_semantic_text_service__remote(registry      : Fast_API__Service__Registry = None,
                                           base_url      : str                          = None,
                                           api_key_name  : str                          = None,
                                           api_key_value : str                          = None
                                          ) -> None:
    """Register Semantic Text Service config for REMOTE mode.
    
    If credentials not provided, reads from environment variables.
    Use for production.
    """
    if registry is None:
        registry = fast_api__service__registry
        
    # Use provided values or fall back to env vars
    url   = base_url      or get_env(ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL )
    name  = api_key_name  or get_env(ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_NAME )
    value = api_key_value or get_env(ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_VALUE)
    
    if not url:
        raise ValueError(f"REMOTE mode requires base_url or {ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL} env var")
    
    config = Fast_API__Service__Registry__Client__Config(
        mode          = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
        base_url      = url                                                   ,
        api_key_name  = name                                                  ,
        api_key_value = value                                                 )
    
    registry.register(Semantic_Text__Service__Client, config)


def register_semantic_text_service__from_env(registry: Fast_API__Service__Registry = None
                                            ) -> None:
    """Register Semantic Text Service config based on environment.
    
    If SEMANTIC_TEXT_SERVICE_BASE_URL is set, uses REMOTE mode.
    Otherwise, uses IN_MEMORY mode (for testing).
    """
    if registry is None:
        registry = fast_api__service__registry
        
    target_url = get_env(ENV_VAR__AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL)
    
    if target_url:
        register_semantic_text_service__remote(registry=registry)
    else:
        register_semantic_text_service__in_memory(registry=registry)


def register_semantic_text_service__local_server(registry       : Fast_API__Service__Registry = None,
                                                 base_url       : str                          = None,
                                                 return_client  : bool                         = False
                                                ):
    """Register Semantic Text Service config for local server mode.
    
    Use this when you've started a local server via Fast_API_Server
    and want to test against it with real HTTP transport.
    """
    if registry is None:
        registry = fast_api__service__registry
    
    if not base_url:
        raise ValueError("base_url is required for local server mode")
    
    config = Fast_API__Service__Registry__Client__Config(
        mode     = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
        base_url = base_url                                              )
    
    registry.register(Semantic_Text__Service__Client, config)
    
    if return_client:
        return Semantic_Text__Service__Client()
