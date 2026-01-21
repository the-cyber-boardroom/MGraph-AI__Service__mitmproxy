from osbot_utils.type_safe.Type_Safe                                         import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                         import Safe_UInt
from osbot_utils.type_safe.primitives.domains.common.safe_str.Safe_Str__Text import Safe_Str__Text
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id           import Cache_Id
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html    import Safe_Str__Html

from mgraph_ai_service_mitmproxy.service.cache.schemas.safe_str.Safe_Str__Proxy__Cache_Key import Safe_Str__Proxy__Cache_Key


class Schema__HTML_Graph__Load_Result(Type_Safe):                               # Result from loading HTML from cache
    success     : bool                                                          # Operation succeeded
    found       : bool                                                          # Entry was found in cache
    html        : Safe_Str__Html                                                # HTML content (empty if not found)
    cache_id    : Cache_Id                                                       # Unique cache entry ID
    cache_key   : Safe_Str__Proxy__Cache_Key                                                      # URL-based cache key
    char_count  : Safe_UInt                                                     # HTML character count
    error       : Safe_Str__Text              = None                                  # Error message if failed