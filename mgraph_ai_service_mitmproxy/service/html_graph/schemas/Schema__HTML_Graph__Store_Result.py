from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Key import Safe_Str__Cache__File__Cache_Key
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                        import Safe_UInt
from osbot_utils.type_safe.primitives.domains.common.safe_str.Safe_Str__Text                import Safe_Str__Text
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash    import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                          import Cache_Id


class Schema__HTML_Graph__Store_Result(Type_Safe):                              # Result from storing HTML in cache
    success     : bool                                                          # Operation succeeded
    cache_id    : Cache_Id                                                      # Unique cache entry ID
    cache_key   : Safe_Str__Cache__File__Cache_Key                              # URL-based cache key
    cache_hash  : Safe_Str__Cache_Hash                                          # Content hash
    char_count  : Safe_UInt                                                     # HTML character count
    error       : Safe_Str__Text                    = None                      # Error message if failed


