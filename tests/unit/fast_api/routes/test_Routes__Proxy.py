from unittest                                                                        import TestCase
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Proxy                       import Routes__Proxy
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Request_Data           import Schema__Proxy__Request_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications          import Schema__Proxy__Modifications

class test_Routes__Proxy(TestCase):

    @classmethod
    def setUpClass(cls):                                             # Setup once for all tests
        cls.routes = Routes__Proxy()

    def test__init__(self):                                          # Test initialization
        with self.routes as _:
            assert type(_)         is Routes__Proxy
            assert _.tag           == 'proxy'
            assert _.proxy_service is not None

    def test_process_request(self):                                  # Test process_request route
        # todo: fix the current (minor issue) that with this request we are getting on out test logs the console entry:
        #       ➡️    📥  GET    example.com                    /api/test
        with Schema__Proxy__Request_Data() as request:
            request.method  = "GET"
            request.host    = "example.com"
            request.path    = "/api/test"
            request.version = "v1.0.0"

            with self.routes.process_request(request) as modifications:
                assert type(modifications) is Schema__Proxy__Modifications
                assert modifications.headers_to_add == {}                       # Upstream debug headers are opt-in via mitm-debug cookie / x-mitm-debug header

            request.headers = {'cookie': 'mitm-debug=true'}                     # With the opt-in the debug headers are added
            with self.routes.process_request(request) as modifications:
                assert modifications.headers_to_add != {}

    def test_reset_proxy_stats(self):                                # Test stats reset
        # First, ensure we have some stats
        with Schema__Proxy__Request_Data() as request:
            request.method  = "GET"
            request.host    = "test.com"
            request.path    = "/test"
            request.version = "v1.0.0"
            self.routes.process_request(request)

        # # Now reset
        # with self.routes.reset_proxy_stats() as result:
        #     assert result["message"] == "Stats reset successfully"
        #     assert "previous_stats"  in result

        # Verify stats were reset
        # with self.routes.get_proxy_stats() as stats:
        #     assert stats["total_requests"] == 0