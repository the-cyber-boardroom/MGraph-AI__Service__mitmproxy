from unittest                                                                                   import TestCase
from osbot_utils.type_safe.primitives.domains.identifiers.Cache_Id                              import Cache_Id
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html                       import Safe_Str__Html
from osbot_utils.utils.Objects                                                                  import base_types
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                            import Safe_UInt
from mgraph_ai_service_mitmproxy.service.cache.schemas.safe_str.Safe_Str__Proxy__Cache_Key      import Safe_Str__Proxy__Cache_Key
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Load_Result     import Schema__HTML_Graph__Load_Result

class test_Schema__HTML_Graph__Load_Result(TestCase):                           # Test load result schema

    def test__init__(self):                                                     # Test auto-initialization
        with Schema__HTML_Graph__Load_Result() as _:
            assert type(_)           is Schema__HTML_Graph__Load_Result
            assert Type_Safe         in base_types(_)
            assert _.success         is False
            assert _.found           is False
            assert type(_.html)      is Safe_Str__Html
            assert type(_.cache_id)  is Cache_Id
            assert type(_.cache_key) is Safe_Str__Proxy__Cache_Key
            assert type(_.char_count)is Safe_UInt
            assert _.error           is None

    def test__with_values(self):                                                # Test with explicit values
        html_content = "<html><body>Test</body></html>"
        with Schema__HTML_Graph__Load_Result(success    = True              ,
                                             found      = True              ,
                                             html       = html_content      ,
                                             cache_id   = Cache_Id.new()    ,
                                             cache_key  = "example.com/test",
                                             char_count = 31                ) as _:
            assert _.success         is True
            assert _.found           is True
            assert "<body>Test</body>" in _.html
            assert _.char_count      == 31

