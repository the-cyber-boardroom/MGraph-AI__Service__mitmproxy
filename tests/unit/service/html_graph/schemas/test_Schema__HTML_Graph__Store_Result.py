from unittest                                                                                   import TestCase
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__File__Cache_Key     import Safe_Str__Cache__File__Cache_Key
from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash        import Safe_Str__Cache_Hash
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                              import Cache_Id
from osbot_utils.utils.Objects                                                                  import base_types
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                            import Safe_UInt
from osbot_utils.type_safe.primitives.domains.identifiers.Safe_Id                               import Safe_Id
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Store_Result    import Schema__HTML_Graph__Store_Result
from mgraph_ai_service_mitmproxy.service.html_graph.utils.html_graph_service__utils import cache_hash__new


class test_Schema__HTML_Graph__Store_Result(TestCase):                          # Test store result schema

    def test__init__(self):                                                     # Test auto-initialization
        with Schema__HTML_Graph__Store_Result() as _:
            assert type(_)           is Schema__HTML_Graph__Store_Result
            assert Type_Safe         in base_types(_)
            assert _.success         is False                                   # Default bool is False
            assert type(_.cache_id)  is Cache_Id
            assert type(_.cache_key) is Safe_Str__Cache__File__Cache_Key
            assert type(_.cache_hash)is Safe_Str__Cache_Hash
            assert type(_.char_count)is Safe_UInt
            assert _.error           is None

    def test__with_values(self):                                                # Test with explicit values
        cache_id   = Cache_Id.new()
        cache_hash = cache_hash__new()
        with Schema__HTML_Graph__Store_Result(success    = True               ,
                                              cache_id   = cache_id           ,
                                              cache_key  = "example.com/page" ,
                                              cache_hash = cache_hash         ,
                                              char_count = 1000               ) as _:
            assert _.success         is True
            assert _.cache_id        == cache_id
            assert _.cache_key       == "example.com/page"
            assert _.cache_hash      == cache_hash
            assert _.char_count      == 1000

    def test__type_safety(self):                                                # Test type enforcement
        cache_id = Cache_Id.new()
        with Schema__HTML_Graph__Store_Result() as _:
            _.cache_id   = cache_id                                             # Auto-converts to Safe_Id
            _.char_count = 500                                                  # Auto-converts to Safe_UInt

            assert type(_.cache_id)   is Cache_Id
            assert type(_.char_count) is Safe_UInt
            assert _.cache_id         == cache_id
            assert _.char_count       == 500
