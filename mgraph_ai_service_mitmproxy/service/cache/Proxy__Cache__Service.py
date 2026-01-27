import re
import time
from urllib.parse                                                                                   import urlparse
from typing                                                                                         import Optional, Dict

from osbot_fast_api.services.schemas.registry.enums.Enum__Fast_API__Service__Registry__Client__Mode import Enum__Fast_API__Service__Registry__Client__Mode

from mgraph_ai_service_cache_client.client.cache_client.Cache__Service__Client import Cache__Service__Client

from mgraph_ai_service_cache_client.schemas.consts.consts__Cache_Client                             import ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE
from osbot_utils.helpers.cache.Cache__Hash__Generator                                               import Cache__Hash__Generator
from osbot_utils.type_safe.Type_Safe                                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash            import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Random_Guid                               import Random_Guid
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                            import Safe_Str__Url
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                      import type_safe
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy                import Enum__Cache__Store__Strategy
from osbot_utils.utils.Env                                                                          import get_env
from mgraph_ai_service_mitmproxy.service.cache.schemas.Enum__Cache__Transformation_Type             import Enum__Cache__Transformation_Type
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Config                        import Schema__Cache__Config
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Page__Entry                   import Schema__Cache__Page__Entry
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Page__Refs                    import Schema__Cache__Page__Refs
from mgraph_ai_service_mitmproxy.service.cache.schemas.Schema__Cache__Stats                         import Schema__Cache__Stats
from mgraph_ai_service_mitmproxy.service.cache.schemas.safe_str.Safe_Str__Proxy__Cache_Key          import Safe_Str__Proxy__Cache_Key
from mgraph_ai_service_mitmproxy.service.consts.consts__proxy                                       import ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME, ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL

DEFAULT__TEXT__CACHE_NOT_FOUND = ''                             # this used to be 'Not found' # todo see if we still need this DEFAULT__TEXT__CACHE_NOT_FOUND variable
PAGE_ENTRY__JSON_FIELD_PATH    = 'cache_key'

class Proxy__Cache__Service(Type_Safe):                                 # Cache service for WCF transformations
    cache_client      : Cache__Service__Client                          # Cache service client
    cache_config      : Schema__Cache__Config                           # Configuration
    stats             : Schema__Cache__Stats                            # Cache statistics

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #
    #
    # def setup(self):
    #     self.setup__service_auth()
    #     return self
    #
    # def setup__service_auth(self):
    #     base_url  = get_env(ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL )
    #     key_name  = get_env(ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME )
    #     key_value = get_env(ENV_VAR__AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE)
    #
    #     auth__kwargs = dict(base_url       = base_url                 ,
    #                         api_key        = key_value                ,
    #                         api_key_header = key_name                 )
    #
    #     if base_url and key_name and key_value:
    #         cache_auth_available = True
    #         client_mode          = Enum__Fast_API__Service__Registry__Client__Mode.REMOTE
    #     else:
    #         cache_auth_available = False
    #         client_mode          = Enum__Fast_API__Service__Registry__Client__Mode.IN_MEMORY
    #
    #     #cache_enabled        = False # cache_auth_available     # For now disable the cache
    #     cache_enabled        = cache_auth_available     # For now disable the cache
    #     cache_client__config = Cache__Service__Fast_API__Client__Config(**auth__kwargs, mode=client_mode)
    #
    #     self.cache_config    = Schema__Cache__Config            (**auth__kwargs, enabled=cache_enabled)
    #     self.cache_client    = Cache__Service__Fast_API__Client (config=cache_client__config)
    #
    #     return self


    def url_to_cache_key(self, target_url : str                                         # Convert URL to hierarchical cache_key
                          ) -> Safe_Str__Proxy__Cache_Key:                              # Hierarchical cache_key

        parsed = urlparse(target_url)
        domain = parsed.netloc                                                          # Extract domain (including subdomain)
        path   = parsed.path.strip('/')                                                 # Extract path (remove leading/trailing slashes, ignore query/fragment)

        if not path:                                                                    # Handle empty path (homepage)
            path = "index"

        path       = self.sanitize_url_path(path)                                      # Sanitize path (replace problematic characters)
        cache_key = f"sites/{domain}/pages/{path}"                                      # Construct hierarchical cache_key
        return cache_key

    # todo: replace this with a Safe_Str__* usage
    def sanitize_url_path(self, path : str                      # Sanitize URL path for use in cache_key
                           ) -> str:                            # Sanitized path
        sanitized = re.sub(r'[^a-zA-Z0-9\-_/]', '-', path)
        sanitized = re.sub(r'-+', '-', sanitized)               # Remove consecutive hyphens
        return sanitized

    def get_page_entry__via__target_url(self, target_url : Safe_Str__Url ):
        cache_key       = self.url_to_cache_key(target_url)
        cache_hash      = Cache__Hash__Generator().from_string(cache_key)                                    # todo review the dependency of importing a class from mgraph_ai_service_cache (and if we shouldn't move this Cache__Hash__Generator to the mgraph_ai_service_cache_client project)
        return self.get_page_entry__via__cache_hash(cache_hash=cache_hash)

    def get_page_entry__via__cache_hash(self, cache_hash : Safe_Str__Cache_Hash                            # Get existing page cache_id
                                         ) -> Dict:
        result = self.cache_client.retrieve().retrieve__hash__cache_hash(cache_hash = cache_hash                 ,
                                                                         namespace  = self.cache_config.namespace)

        # todo: see if metadata is really the best place to get this page entry data
        if result:
            metadata = result.metadata                                   # todo: this metadata should be a Type_Safe object
            return metadata
        else:
            return None

    @type_safe
    def get_or_create_page_entry(self, target_url : Safe_Str__Url                           # Get existing page cache_id or create new page entry
                                  ) -> Schema__Cache__Page__Refs:                           # cache_id for the page

        json_field_path = PAGE_ENTRY__JSON_FIELD_PATH
        cache_key       = self.url_to_cache_key(target_url)
        page_refs       = Schema__Cache__Page__Refs(cache_key       = cache_key      ,
                                                    json_field_path = json_field_path)
        cache_hash = Cache__Hash__Generator().from_string(cache_key)                                    # todo review the dependency of importing a class from mgraph_ai_service_cache (and if we shouldn't move this Cache__Hash__Generator to the mgraph_ai_service_cache_client project)

        page_entry = self.get_page_entry__via__cache_hash(cache_hash = cache_hash)

        if page_entry:          # means the cache_hash was found
            page_refs.cache_id   = page_entry.cache_id
            page_refs.cache_hash = cache_hash
            return page_refs


        parsed       = urlparse(target_url)
        page_entry   = Schema__Cache__Page__Entry(url           = target_url,
                                                  cache_key     = cache_key,
                                                  domain        = parsed.netloc,
                                                  path          = parsed.path,
                                                  access_count  = 1)
        store_kwargs = dict(namespace       = self.cache_config.namespace            ,
                            strategy         = Enum__Cache__Store__Strategy.KEY_BASED,
                            cache_key        = cache_key                             ,
                            file_id          = "page-entry"                          ,  # Fixed file_id for page entries
                            body             = page_entry.json()                     ,
                            json_field_path  = json_field_path                       )

        result               = self.cache_client.store().store__json__cache_key(**store_kwargs)
        if result is None:

            raise Exception(f"Error in get_or_create_page_entry")     # todo: find a better way and location to catch these errors (which usually happen when the API key is not set)
        page_refs.cache_id   = result.cache_id
        page_refs.cache_hash = result.cache_hash

        if self.cache_config.track_stats:                                       # Update stats (only if this is a new page)
            self.stats.total_pages_cached += 1

        return page_refs


    def page_exists(self, target_url : str                      # Check if page exists in cache
                     ) -> bool:                                 # Page exists

        page_entry = self.get_page_entry__via__target_url(target_url=target_url)
        return page_entry is not None

    # review this method name (namely the '_cached_' bit)
    def get_cached_transformation(self, target_url  : str       ,  # Get cached WCF transformation
                                        wcf_command : str
                                   ) -> Optional[str]:          # Cached content or None
        if not self.cache_config.enabled:
            return None

        start_time = time.time()

        page_refs = self.get_or_create_page_entry(target_url)               # Get page cache_id (from mapping or by creating entry)
        cache_id  = page_refs.cache_id

        data_key = self._wcf_command_to_data_key(wcf_command)               # Get transformation data


        transformation = self.cache_client.data().retrieve().data__string__with__id_and_key(cache_id     = cache_id,
                                                                                            namespace    = self.cache_config.namespace,
                                                                                            data_key     = data_key,
                                                                                            data_file_id = self.cache_config.data_file_id)
        if transformation == DEFAULT__TEXT__CACHE_NOT_FOUND:                    # check if we got a Not found (aka 404) error
            return None

        duration_ms = (time.time() - start_time) * 1000                         # Update stats
        self._update_cache_hit_stats(duration_ms)

        return transformation

    def store_transformation(self, target_url  : str            ,   # Store WCF transformation result
                                   wcf_command : str            ,   # WCF command type (e.g., "url-to-html")
                                   content     : str            ,   # Transformed content (HTML, text, etc.)
                                   metadata    : dict               # WCF call metadata (response time, status, etc.)
                              ) -> Random_Guid:                     # cache_id of the page entry
        if not self.cache_config.enabled:
            return ""

        page_refs = self.get_or_create_page_entry(target_url)       # Ensure page entry exists
        cache_id  = page_refs.cache_id
        data_key  = self._wcf_command_to_data_key(wcf_command)       # Convert WCF command to data_key

        # Store transformation content as child data
        self.cache_client.data_store().data__store_string__with__id_and_key(cache_id     = cache_id                     ,
                                                                            namespace    = self.cache_config.namespace  ,
                                                                            data_key     = data_key                      ,
                                                                            data_file_id = self.cache_config.data_file_id,
                                                                            body         = content                       )

        if self.cache_config.cache_metadata:                                # Store metadata (optional, if enabled)
            metadata_key = f"{data_key}/metadata"

            self.cache_client.data_store().data__store_json__with__id_and_key(cache_id     = cache_id                       ,
                                                                              namespace    = self.cache_config.namespace    ,
                                                                              data_key     = metadata_key                   ,
                                                                              data_file_id = self.cache_config.data_file_id ,
                                                                              body         = metadata                       )

        return cache_id         # todo: see if cache is all we should be returning here

    def has_cached_transformation(self, target_url  : str       ,  # Check if transformation is cached
                                        wcf_command : str
                                   ) -> bool:                   # Is cached
        if not self.cache_config.enabled:
            return False

        cached = self.get_cached_transformation(target_url, wcf_command)

        return cached is not None

    def increment_cache_hit(self):                              # Record cache hit
        """Record cache hit"""
        if self.cache_config.track_stats:
            self.stats.cache_hits       += 1
            self.stats.wcf_calls_saved  += 1

    def increment_cache_miss(self):                             # Record cache miss
        """Record cache miss"""
        if self.cache_config.track_stats:
            self.stats.cache_misses += 1

    def get_cache_stats(self) -> dict:                          # Get cache statistics
        return { "enabled"                      : self.cache_config.enabled,                        # todo: refactor to Type_Safe class
                 "hit_rate"                     : self.stats.hit_rate(),
                 "cache_hits"                   : self.stats.cache_hits,
                 "cache_misses"                 : self.stats.cache_misses,
                 "wcf_calls_saved"              : self.stats.wcf_calls_saved,
                 "total_pages_cached"           : self.stats.total_pages_cached,
                 "avg_cache_hit_time_ms"        : self.stats.avg_cache_hit_time_ms,
                 "avg_cache_miss_time_ms"       : self.stats.avg_cache_miss_time_ms,
                 "avg_wcf_call_time_ms"         : self.stats.avg_wcf_call_time_ms,
                 "estimated_time_saved_seconds" : self.stats.estimated_time_saved_seconds() }

    def _wcf_command_to_data_key(self, wcf_command : str        # Convert WCF command to data_key path
                                   ) -> str:                    # data_key path
        try:
            command_type = Enum__Cache__Transformation_Type(wcf_command)
            return command_type.to_data_key()
        except ValueError:                                      # todo: review if this is a valid scenario
            # Unknown command - use generic path
            return f"transformations/{wcf_command.replace('-', '_')}"

    def _update_cache_hit_stats(self, duration_ms : float       # Update cache hit statistics
                                 ) -> None:                     # No return
        """Update cache hit statistics"""
        if not self.cache_config.track_stats:
            return

        # Update running average
        total_hits = float(self.stats.cache_hits)
        if total_hits == 0:
            self.stats.avg_cache_hit_time_ms = duration_ms
        else:
            current_avg = self.stats.avg_cache_hit_time_ms
            self.stats.avg_cache_hit_time_ms = ((current_avg * total_hits) + duration_ms) / (total_hits + 1)