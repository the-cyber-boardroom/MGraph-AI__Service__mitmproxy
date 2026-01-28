from osbot_utils.utils.Objects                                                                          import base_classes
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from unittest                                                                                           import TestCase
from osbot_fast_api.services.registry.Fast_API__Client__Requests                                        import Fast_API__Client__Requests
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client                              import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client__Requests import HTML__Service__Client__Requests


class test_HTML__Service__Client__Requests(TestCase):

    def test__init__(self):                                                     # Test auto-initialization
        with HTML__Service__Client__Requests() as _:
            assert type(_)         is HTML__Service__Client__Requests
            assert base_classes(_) == [Fast_API__Client__Requests, Type_Safe, object]

    def test__inherits_from_Fast_API__Client__Requests(self):                   # Test inheritance
        requests = HTML__Service__Client__Requests()
        assert isinstance(requests, Fast_API__Client__Requests)

