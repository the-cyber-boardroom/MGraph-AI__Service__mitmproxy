# ═══════════════════════════════════════════════════════════════════════════════
# test_HTML__Service__Client
# Tests for the stateless HTML Service client
# ═══════════════════════════════════════════════════════════════════════════════
from osbot_utils.utils.Objects                                                                          import base_classes
from osbot_utils.type_safe.Type_Safe                                                                    import Type_Safe
from unittest                                                                                           import TestCase
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client                              import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client__Requests                    import HTML__Service__Client__Requests


# ═══════════════════════════════════════════════════════════════════════════════
# Unit Tests - Client Structure
# ═══════════════════════════════════════════════════════════════════════════════

class test_HTML__Service__Client(TestCase):

    def test__init__(self):                                                     # Test auto-initialization
        with HTML__Service__Client() as _:
            assert type(_)         is HTML__Service__Client
            assert base_classes(_) == [Type_Safe, object]

    def test__no_config_attribute(self):                                        # Client is stateless - no config
        client = HTML__Service__Client()
        assert hasattr(client, 'config')   is False
        assert hasattr(client, 'base_url') is False
        assert hasattr(client, 'timeout')  is False

    def test__requests__returns_transport(self):                                # Test requests creates transport
        with HTML__Service__Client() as _:
            requests = _.requests()
            assert type(requests) is HTML__Service__Client__Requests

    def test__requests__sets_service_type(self):                                # Test service_type is set
        with HTML__Service__Client() as _:
            requests = _.requests()
            assert requests.service_type is HTML__Service__Client

    def test__requests__cached_on_self(self):                                   # Test requests is cached
        with HTML__Service__Client() as _:
            requests_1 = _.requests()
            requests_2 = _.requests()
            assert requests_1 is requests_2