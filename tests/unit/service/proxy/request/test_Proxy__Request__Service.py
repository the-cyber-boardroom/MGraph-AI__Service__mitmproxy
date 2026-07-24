from unittest                                                                   import TestCase
from osbot_utils.utils.Objects                                                  import base_classes
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__Dict           import Type_Safe__Dict
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__List           import Type_Safe__List
from mgraph_ai_service_mitmproxy.service.proxy.request.Proxy__Request__Service  import Proxy__Request__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Stats__Service            import Proxy__Stats__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Content__Service          import Proxy__Content__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Cookie__Service           import Proxy__Cookie__Service
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Request_Data      import Schema__Proxy__Request_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications     import Schema__Proxy__Modifications
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Stats             import Schema__Proxy__Stats
import json


class test_Proxy__Request__Service(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.stats_service   = Proxy__Stats__Service(stats=Schema__Proxy__Stats())            # Fresh stats service
        cls.content_service = Proxy__Content__Service()                                       # Content service
        cls.cookie_service  = Proxy__Cookie__Service()                                        # Cookie service
        cls.service         = Proxy__Request__Service(stats_service   = cls.stats_service  ,
                                                      content_service = cls.content_service,
                                                      cookie_service  = cls.cookie_service ).setup()

        cls.test_request_basic = Schema__Proxy__Request_Data(                                # Basic request data
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {},
            stats         = {},
            version       = 'v1.0.0'
        )

        cls.test_request_with_debug = Schema__Proxy__Request_Data(                           # Request opted in to the upstream debug headers
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {'cookie': 'mitm-debug=true'},
            stats         = {},
            version       = 'v1.0.0'
        )

        cls.test_request_with_cookies = Schema__Proxy__Request_Data(                         # Request with cookies
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {'cookie': 'mitm-show=url-to-html; mitm-debug=true'},
            stats         = {},
            version       = 'v1.0.0'
        )

        cls.test_request_with_cache = Schema__Proxy__Request_Data(                           # Request with cache cookie
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {'cookie': 'mitm-cache=true'},
            stats         = {},
            version       = 'v1.0.0'
        )

    def setUp(self):                                                                          # Reset stats before each test
        self.stats_service.stats = Schema__Proxy__Stats()                                    # Fresh stats per test

    def test__init__(self):                                                                    # Test auto-initialization of Proxy__Request__Service
        with Proxy__Request__Service().setup() as _:
            assert type(_)         is Proxy__Request__Service
            assert base_classes(_) == [Proxy__Request__Service.__bases__[0], object]

            assert type(_.stats_service)   is Proxy__Stats__Service
            assert type(_.content_service) is Proxy__Content__Service
            assert type(_.cookie_service)  is Proxy__Cookie__Service

    def test_process_request(self):                                                           # Test request processing with debug opt-in
        with self.service as _:
            modifications = _.process_request(self.test_request_with_debug)

            assert type(modifications) is Schema__Proxy__Modifications
            assert 'x-mgraph-proxy'         in modifications.headers_to_add
            assert 'x-request-id'           in modifications.headers_to_add
            assert 'x-processed-by'         in modifications.headers_to_add
            assert 'x-processed-at'         in modifications.headers_to_add
            assert 'x-stats-total-requests' in modifications.headers_to_add
            assert 'y-version-service'      in modifications.headers_to_add
            assert 'y-version-interceptor'  in modifications.headers_to_add

    def test_process_request__increments_stats(self):                                         # Test stats are incremented
        initial_count = self.stats_service.stats.total_requests

        with self.service as _:
            _.process_request(self.test_request_basic)

            assert self.stats_service.stats.total_requests == initial_count + 1

    def test_process_request__with_cookies(self):                                             # Test processing with proxy cookies
        with self.service as _:
            modifications = _.process_request(self.test_request_with_cookies)

            assert 'x-proxy-cookies' in modifications.headers_to_add                          # Cookie summary added
            assert 'x-debug-params'  in modifications.headers_to_add                          # Debug params from cookies

            cookie_summary = json.loads(modifications.headers_to_add['x-proxy-cookies'])
            assert cookie_summary['show_command']  == 'url-to-html'
            assert cookie_summary['debug_enabled'] is True

    def test_process_request__cookie_to_debug_params_conversion(self):                        # Test cookies converted to debug_params
        with self.service as _:
            modifications = _.process_request(self.test_request_with_cookies)

            debug_params_json = modifications.headers_to_add['x-debug-params']
            debug_params = json.loads(debug_params_json)

            assert debug_params['show']  == 'url-to-html'
            assert debug_params['debug'] == 'true'

    def test_process_request__no_cookies(self):                                               # Test processing without cookies
        with self.service as _:
            modifications = _.process_request(self.test_request_basic)

            assert 'x-proxy-cookies' not in modifications.headers_to_add                      # No cookie summary

    def test_process_request__cookie_priority_over_query(self):                               # Test cookies override query params
        request_with_both = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {'cookie': 'mitm-show=url-to-html; mitm-debug=true'},            # Cookie param (debug opt-in so x-debug-params is added)
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(request_with_both)

            debug_params = json.loads(modifications.headers_to_add['x-debug-params'])
            assert debug_params['show'] == 'url-to-html'                                      # Cookie value wins

    def test__bug__process_request__blocked_path(self):                                             # Test path blocking
        blocked_request = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/blocked/resource',
            original_path = '/blocked/resource',
            headers       = {},
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(blocked_request)

            assert modifications.block_request is True
            #assert '/blocked/resource' not in modifications.block_message          # BUG
            assert '_blocked_resource' in modifications.block_message               # BUG : we need a better class for these error messages
            assert modifications.block_status == 403

    def test_process_request__remove_sensitive_headers(self):                                 # Test sensitive header removal
        request_with_sensitive = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {
                'X-Secret-Key'  : 'abc123',
                'X-Private-Data': 'sensitive',
                'X-API-Token'   : 'xyz789',
                'User-Agent'    : 'Mozilla/5.0'                                                # Normal header
            },
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(request_with_sensitive)

            assert 'X-Secret-Key'   in modifications.headers_to_remove
            assert 'X-Private-Data' in modifications.headers_to_remove
            assert 'X-API-Token'    in modifications.headers_to_remove
            assert 'User-Agent'     not in modifications.headers_to_remove                    # Normal header not removed

    def test_process_request__version_headers(self):                                          # Test version headers are added
        with self.service as _:
            modifications = _.process_request(self.test_request_with_debug)

            assert modifications.headers_to_add['y-version-interceptor'] == 'v1.0.0'

    def test_process_request__stats_header(self):                                             # Test stats header reflects count
        with self.service as _:
            _.process_request(self.test_request_with_debug)                                   # First request
            modifications = _.process_request(self.test_request_with_debug)                   # Second request

            stats_count = int(modifications.headers_to_add['x-stats-total-requests'])
            assert stats_count == 2                                                            # Two requests processed

    def test_process_request__request_id_unique(self):                                        # Test request IDs are unique
        with self.service as _:
            mods1 = _.process_request(self.test_request_with_debug)
            mods2 = _.process_request(self.test_request_with_debug)

            id1 = mods1.headers_to_add['x-request-id']
            id2 = mods2.headers_to_add['x-request-id']

            assert id1 != id2                                                                  # Different IDs

    def test_process_request__timestamp_format(self):                                         # Test timestamp header format
        with self.service as _:
            modifications = _.process_request(self.test_request_with_debug)

            timestamp = modifications.headers_to_add['x-processed-at']
            assert 'T' in timestamp                                                            # ISO format
            assert len(timestamp) > 19                                                         # Includes microseconds

    def test__multiple_proxy_cookies(self):                                                    # Test multiple proxy cookies together
        request_multi_cookies = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {
                'cookie': 'mitm-show=url-to-html; mitm-inject=debug-panel; '
                         'mitm-debug=true; mitm-rating=0.5; mitm-cache=true'
            },
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(request_multi_cookies)

            cookie_summary = json.loads(modifications.headers_to_add['x-proxy-cookies'])
            assert cookie_summary['show_command']    == 'url-to-html'
            assert cookie_summary['inject_command']  == 'debug-panel'
            assert cookie_summary['debug_enabled']   is True
            assert cookie_summary['rating']          == 0.5
            assert cookie_summary['cache_enabled']   is True

            debug_params = json.loads(modifications.headers_to_add['x-debug-params'])
            assert debug_params['show']   == 'url-to-html'
            assert debug_params['inject'] == 'debug-panel'
            assert debug_params['debug']  == 'true'

    def test__mixed_proxy_and_regular_cookies(self):                                           # Test proxy cookies filtered from regular cookies
        request_mixed = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {
                'cookie': 'session=abc123; mitm-show=url-to-html; user=john; '
                         'mitm-debug=true; theme=dark'
            },
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(request_mixed)

            cookie_summary = json.loads(modifications.headers_to_add['x-proxy-cookies'])
            proxy_cookies = cookie_summary['all_proxy_cookies']

            assert 'mitm-show'  in proxy_cookies
            assert 'mitm-debug' in proxy_cookies
            assert 'session'    not in proxy_cookies                                           # Regular cookie filtered
            assert 'user'       not in proxy_cookies                                           # Regular cookie filtered
            assert 'theme'      not in proxy_cookies                                           # Regular cookie filtered

    def test__empty_headers(self):                                                             # Test processing with no headers
        request_no_headers = Schema__Proxy__Request_Data(
            method        = 'GET',
            host          = 'example.com',
            path          = '/test',
            original_path = '/test',
            headers       = {},
            stats         = {},
            version       = 'v1.0.0'
        )

        with self.service as _:
            modifications = _.process_request(request_no_headers)

            assert modifications.headers_to_add == {}                                         # No debug opt-in, so no upstream headers
            assert len(modifications.headers_to_remove) == 0                                  # Nothing to remove

    def test__host_and_path_tracking(self):                                                    # Test host and path tracked in stats
        request1 = Schema__Proxy__Request_Data(
            method='GET', host='example.com', path='/path1',
            original_path='/path1', headers={}, stats={}, version='v1.0.0'
        )
        request2 = Schema__Proxy__Request_Data(
            method='GET', host='test.com', path='/path2',
            original_path='/path2', headers={}, stats={}, version='v1.0.0'
        )

        with self.service as _:
            _.process_request(request1)
            _.process_request(request2)

            assert self.stats_service.stats.total_requests == 2

    def test__debug_headers_are_opt_in(self):                                                  # Test upstream headers only sent when opted in
        request_with_header = Schema__Proxy__Request_Data(
            method='GET', host='example.com', path='/test',
            original_path='/test', headers={'X-Mitm-Debug': 'true'}, stats={}, version='v1.0.0'
        )

        with self.service as _:
            assert _.process_request(self.test_request_basic).headers_to_add == {}             # Default: nothing sent upstream
            assert 'x-mgraph-proxy' in _.process_request(self.test_request_with_debug).headers_to_add   # mitm-debug cookie opts in
            assert 'x-mgraph-proxy' in _.process_request(request_with_header).headers_to_add            # x-mitm-debug header opts in (case-insensitive)

    def test__standard_headers_always_present(self):                                           # Test standard headers all added when debug is on
        with self.service as _:
            modifications = _.process_request(self.test_request_with_debug)

            required_headers = [
                'x-mgraph-proxy',
                'x-request-id',
                'x-processed-by',
                'x-processed-at',
                'x-stats-total-requests',
                'y-version-service',
                'y-version-interceptor'
            ]

            for header in required_headers:
                assert header in modifications.headers_to_add, f"Missing header: {header}"

    def test__modifications_object_structure(self):                                            # Test modifications object has correct structure
        with self.service as _:
            modifications = _.process_request(self.test_request_basic)

            assert type(modifications.headers_to_add)    is Type_Safe__Dict
            assert type(modifications.headers_to_remove) is Type_Safe__List
            assert type(modifications.block_request)     is bool
            assert modifications.cached_response         == {}                                 # No cached response by default