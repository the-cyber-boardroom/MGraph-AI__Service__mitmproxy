from unittest                                                                                                   import TestCase
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                           import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client__Requests                 import Semantic_Text__Service__Client__Requests
from osbot_fast_api.services.registry.Fast_API__Client__Requests                                                import Fast_API__Client__Requests
from osbot_utils.type_safe.Type_Safe                                                                            import Type_Safe
from osbot_utils.utils.Objects                                                                                  import base_classes


class test_Semantic_Text__Service__Client__Requests(TestCase):

    def test__init__(self):                                                     # Test auto-initialization
        with Semantic_Text__Service__Client__Requests() as _:
            assert type(_)         is Semantic_Text__Service__Client__Requests
            assert base_classes(_) == [Fast_API__Client__Requests, Type_Safe, object]

    def test__inherits_from_Fast_API__Client__Requests(self):                   # Test inheritance
        requests = Semantic_Text__Service__Client__Requests()
        assert isinstance(requests, Fast_API__Client__Requests)
