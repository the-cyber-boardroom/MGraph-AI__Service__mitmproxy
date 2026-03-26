"""Cache client setup — registers Cache__Service__Client in the service registry."""

from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client                      import Cache__Service__Client
from osbot_fast_api.services.registry.Fast_API__Service__Registry                                   import fast_api__service__registry
from osbot_fast_api.services.schemas.registry.Fast_API__Service__Registry__Client__Config           import Fast_API__Service__Registry__Client__Config
from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode import Enum__Fast_API__Service__Registry__Client__Mode
from osbot_utils.helpers.cache.Cache__Hash__Generator                                               import Cache__Hash__Generator
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy                import Enum__Cache__Store__Strategy


def setup_client(config: dict) -> Cache__Service__Client:
    """Register and return a configured Cache__Service__Client."""

    client_config = Fast_API__Service__Registry__Client__Config(
        base_url       = config['CACHE_SERVICE_BASE_URL'],
        api_key_name   = config['CACHE_SERVICE_API_KEY_NAME'],
        api_key_value  = config['CACHE_SERVICE_API_KEY_VALUE'],
        mode           = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE,
    )

    fast_api__service__registry.register(Cache__Service__Client, client_config)

    return Cache__Service__Client()


def resolve_cache_id(client: Cache__Service__Client, namespace: str, cache_key: str = 'inject') -> str:
    """Get or create the cache_id for the inject scripts entry."""

    cache_hash = Cache__Hash__Generator().from_string(cache_key)

    # Try to find existing
    result = client.retrieve().retrieve__hash__cache_hash(
        cache_hash=cache_hash, namespace=namespace)

    if result:
        return result.metadata.cache_id

    # Create entry
    import json
    entry_body = json.dumps({'type': 'inject-scripts', 'cache_key': cache_key})

    result = client.store().store__json__cache_key(
        namespace       = namespace,
        strategy        = Enum__Cache__Store__Strategy.KEY_BASED,
        cache_key       = cache_key,
        file_id         = 'inject-entry',
        body            = entry_body,
        json_field_path = 'cache_key')

    if result:
        return result.cache_id

    raise RuntimeError(f"Failed to create cache entry for '{cache_key}'")
