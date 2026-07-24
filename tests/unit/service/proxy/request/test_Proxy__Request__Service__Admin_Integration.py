from unittest                                                                   import TestCase
from mgraph_ai_service_mitmproxy.service.proxy.request.Proxy__Request__Service  import Proxy__Request__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Stats__Service            import Proxy__Stats__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Content__Service          import Proxy__Content__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Cookie__Service           import Proxy__Cookie__Service
from mgraph_ai_service_mitmproxy.service.admin.Proxy__Admin__Service            import Proxy__Admin__Service
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Stats             import Schema__Proxy__Stats
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Request_Data      import Schema__Proxy__Request_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications     import Schema__Proxy__Modifications

PATH__MITM_PROXY__COOKIES = '/mitm-proxy/v0/v0.1.0/cookies.html'
PATH__MITM_PROXY__INDEX   = '/mitm-proxy/v0/v0.1.0/index.html'

class Test_Proxy__Request__Service__Admin_Integration(TestCase):

    def setUp(self):                                                            # Setup test fixtures
        self.stats_service   = Proxy__Stats__Service(stats=Schema__Proxy__Stats())
        self.content_service = Proxy__Content__Service()
        self.cookie_service  = Proxy__Cookie__Service()
        self.admin_service   = Proxy__Admin__Service(cookie_service = self.cookie_service,
                                                      stats_service  = self.stats_service )

        self.request_service = Proxy__Request__Service(stats_service   = self.stats_service  ,
                                                        content_service = self.content_service,
                                                        cookie_service  = self.cookie_service ,
                                                        admin_service   = self.admin_service  ).setup()

    def test__init__(self):                                                     # Test service initialization
        assert type(self.request_service)                is Proxy__Request__Service
        assert type(self.request_service.stats_service)  is Proxy__Stats__Service
        assert type(self.request_service.admin_service)  is Proxy__Admin__Service

    def test__process_request__regular_path(self):                             # Test regular path processing
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = '/regular/path'   ,
                                                    headers      = {'cookie': 'mitm-debug=true'},        # Opt in to the upstream debug headers
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        assert type(modifications)                 is Schema__Proxy__Modifications
        assert modifications.cached_response       == {}  # No cached response for regular paths
        assert 'x-mgraph-proxy'                    in modifications.headers_to_add
        assert self.stats_service.stats.total_requests == 1  # Stats incremented

    def test__process_request__admin_path_index(self):                         # Test admin dashboard path
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = PATH__MITM_PROXY__INDEX    ,
                                                    headers      = {}                ,
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        assert type(modifications)                     is Schema__Proxy__Modifications
        assert modifications.cached_response           != {}  # Has cached response
        assert modifications.cached_response['status_code'] == 200
        assert 'text/html'                             in modifications.cached_response['headers']['content-type']
        assert 'Dashboard'                             in modifications.cached_response['body']
        assert self.stats_service.stats.total_requests == 0  # Stats NOT incremented for admin paths

    def test__process_request__admin_path_invalid(self):                       # Test invalid admin path returns 404
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = '/mitm-proxy/invalid',
                                                    headers      = {}                ,
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        assert modifications.cached_response['status_code'] == 404
        assert '404'                                   in modifications.cached_response['body']

    def test__admin_path_early_detection(self):                                # Test admin paths detected before stats
        initial_requests = self.stats_service.stats.total_requests

        # Process admin path
        admin_request = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                     host         = 'example.com'     ,
                                                     path         = PATH__MITM_PROXY__INDEX    ,
                                                     headers      = {}                ,
                                                     stats        = {}                ,
                                                     version      = 'v1.0.0'           )

        self.request_service.process_request(admin_request)

        # Stats should NOT increment for admin paths
        assert self.stats_service.stats.total_requests == initial_requests

        # Process regular path
        regular_request = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                       host         = 'example.com'     ,
                                                       path         = '/regular/path'   ,
                                                       headers      = {}                ,
                                                       stats        = {}                ,
                                                       version      = 'v1.0.0'           )

        self.request_service.process_request(regular_request)

        # Stats SHOULD increment for regular paths
        assert self.stats_service.stats.total_requests == initial_requests + 1


    def test__regular_path_with_debug_cookies(self):                           # Test regular path processing with debug cookies
        request_data = Schema__Proxy__Request_Data(
            method       = 'GET'             ,
            host         = 'example.com'     ,
            path         = '/api/data'       ,
            headers      = { 'Cookie': 'mitm-debug=true' },
            stats        = {}                ,
            version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        # Regular path should NOT return cached response
        assert modifications.cached_response == {}

        # But should process debug cookies
        assert 'x-debug-params' in modifications.headers_to_add

    def test__admin_path_no_upstream_call(self):                               # Test admin paths return immediately
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = PATH__MITM_PROXY__INDEX    ,
                                                    headers      = {}                ,
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        # Should have cached_response set (means no upstream call)
        assert modifications.cached_response != {}
        assert modifications.cached_response['status_code'] == 200

        # Should not set other modification flags
        assert modifications.block_request is False

    def test__handle_admin_request__directly(self):                            # Test _handle_admin_request internal method
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = PATH__MITM_PROXY__INDEX    ,
                                                    headers      = {}                ,
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.handle_admin_request(request_data)

        assert type(modifications)                     is Schema__Proxy__Modifications
        assert modifications.cached_response           != {}
        assert modifications.cached_response['status_code'] == 200

    def test__regular_and_admin_path_isolation(self):                          # Test admin and regular paths don't interfere
        # Process regular path first
        regular_request = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                       host         = 'example.com'     ,
                                                       path         = '/api/endpoint'   ,
                                                       headers      = {}                ,
                                                       stats        = {}                ,
                                                       version      = 'v1.0.0'           )

        regular_mods = self.request_service.process_request(regular_request)

        assert regular_mods.cached_response == {}
        assert self.stats_service.stats.total_requests == 1

        # Process admin path
        admin_request = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                     host         = 'example.com'     ,
                                                     path         = PATH__MITM_PROXY__INDEX    ,
                                                     headers      = {}                ,
                                                     stats        = {}                ,
                                                     version      = 'v1.0.0'           )

        admin_mods = self.request_service.process_request(admin_request)

        assert admin_mods.cached_response != {}
        assert self.stats_service.stats.total_requests == 1  # Still 1, admin didn't increment

        # Process another regular path
        regular_request2 = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                        host         = 'example.com'     ,
                                                        path         = '/another/path'   ,
                                                        headers      = {}                ,
                                                        stats        = {}                ,
                                                        version      = 'v1.0.0'           )

        regular_mods2 = self.request_service.process_request(regular_request2)

        assert regular_mods2.cached_response == {}
        assert self.stats_service.stats.total_requests == 2  # Incremented again

    def test__blocked_path_still_processed(self):                              # Test blocked paths still work normally
        request_data = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                    host         = 'example.com'     ,
                                                    path         = '/blocked/path'   ,
                                                    headers      = {}                ,
                                                    stats        = {}                ,
                                                    version      = 'v1.0.0'           )

        modifications = self.request_service.process_request(request_data)

        # Blocked path should be blocked
        assert modifications.block_request   is True
        assert 'blocked by policy'           in modifications.block_message

        # Admin paths should NOT be blocked
        admin_request = Schema__Proxy__Request_Data(method       = 'GET'             ,
                                                     host         = 'example.com'     ,
                                                     path         = PATH__MITM_PROXY__INDEX    ,
                                                     headers      = {}                ,
                                                     stats        = {}                ,
                                                     version      = 'v1.0.0'           )

        admin_mods = self.request_service.process_request(admin_request)

        assert admin_mods.block_request is False
        assert admin_mods.cached_response != {}
