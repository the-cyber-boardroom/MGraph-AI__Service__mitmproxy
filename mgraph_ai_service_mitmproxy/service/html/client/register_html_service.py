# ═══════════════════════════════════════════════════════════════════════════════
# register_html_service
# Registration helpers for HTML Service (mitmproxy)
# ═══════════════════════════════════════════════════════════════════════════════

from osbot_utils.utils.Env                                                                              import get_env
from mgraph_ai_service_mitmproxy.service.consts.consts__html_service                                    import (ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL ,ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__KEY_NAME ,ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__KEY_VALUE)
from mgraph_ai_service_html.html__fast_api.Html_Service__Fast_API                                       import Html_Service__Fast_API
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                                    import Serverless__Fast_API__Config
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import Fast_API__Service__Registry
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                       import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.Fast_API__Service__Registry__Client__Config               import Fast_API__Service__Registry__Client__Config
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode     import Enum__Fast_API__Service__Registry__Client__Mode


from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client import HTML__Service__Client


def register_html_service__in_memory(registry      : Fast_API__Service__Registry = None,
                                     return_client : bool                        = False
                                    ):
    """Register HTML Service config for IN_MEMORY mode.
    
    Creates FastAPI app and registers config. Use for testing.
    """
    if registry is None:
        registry = fast_api__service__registry

    
    serverless_config = Serverless__Fast_API__Config(enable_api_key=False)
    fast_api          = Html_Service__Fast_API(config=serverless_config).setup()
    
    config = Fast_API__Service__Registry__Client__Config(mode         = Enum__Fast_API__Service__Registry__Client__Mode.IN_MEMORY,
                                                         fast_api_app = fast_api.app()                                           ,
                                                         fast_api     = fast_api                                                 )
    
    registry.register(HTML__Service__Client, config)
    
    if return_client:
        return HTML__Service__Client()
    else:
        return None


def register_html_service__remote(registry      : Fast_API__Service__Registry = None,
                                  base_url      : str                          = None,
                                  api_key_name  : str                          = None,
                                  api_key_value : str                          = None
                                 ) -> None:
    """Register HTML Service config for REMOTE mode.
    
    If credentials not provided, reads from environment variables.
    Use for production.
    """
    if registry is None:
        registry = fast_api__service__registry
        
    # Use provided values or fall back to env vars
    url   = base_url      or get_env(ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL )
    name  = api_key_name  or get_env(ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__KEY_NAME )
    value = api_key_value or get_env(ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__KEY_VALUE)
    
    if not url:
        raise ValueError(f"REMOTE mode requires base_url or {ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL} env var")
    
    config = Fast_API__Service__Registry__Client__Config(mode          = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
                                                         base_url      = url                                                   ,
                                                         api_key_name  = name                                                  ,
                                                         api_key_value = value                                                 )
    
    registry.register(HTML__Service__Client, config)


def register_html_service__from_env(registry: Fast_API__Service__Registry = None
                                   ) -> None:
    """Register HTML Service config based on environment.
    
    If HTML_SERVICE_BASE_URL is set, uses REMOTE mode.
    Otherwise, uses IN_MEMORY mode (for testing).
    """
    if registry is None:
        registry = fast_api__service__registry
        
    target_url = get_env(ENV_VAR__AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL)
    
    if target_url:
        register_html_service__remote(registry=registry)
    else:
        register_html_service__in_memory(registry=registry)


def register_html_service__local_server(registry       : Fast_API__Service__Registry = None,
                                        base_url       : str                          = None,
                                        return_client  : bool                         = False
                                       ):
    """Register HTML Service config for local server mode (started separately).
    
    Use this when you've started a local server via Fast_API_Server
    and want to test against it with real HTTP transport.
    """
    if registry is None:
        registry = fast_api__service__registry
    
    if not base_url:
        raise ValueError("base_url is required for local server mode")
    
    config = Fast_API__Service__Registry__Client__Config(mode    = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
                                                         base_url = base_url                                             )
    
    registry.register(HTML__Service__Client, config)
    
    if return_client:
        return HTML__Service__Client()
