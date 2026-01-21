from unittest                                                               import TestCase
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__Dict       import Type_Safe__Dict
from mgraph_ai_service_mitmproxy.schemas.debug.Schema__Debug__Params        import Schema__Debug__Params
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Request__Info        import Schema__Request__Info
from mgraph_ai_service_mitmproxy.service.request.Proxy__Request__Service    import Proxy__Request__Service


class test_Request__Proxy__Request__Service(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = Proxy__Request__Service()

    def test__init__(self):                                        # Test initialization
        with self.service as _:
            assert type(_) is Proxy__Request__Service
            assert _.query_parser is not None
            assert _.url_builder is not None

    def test_parse_request_info__basic(self):                     # Test basic request parsing
        request_info = self.service.parse_request_info( method       = 'GET',
                                                        host         = 'example.com',
                                                        port         = 443,
                                                        path         = '/api/test',
                                                        scheme       = 'https',
                                                        headers      = {'User-Agent': 'Test/1.0'},
                                                        query_string = 'key=value'              )

        assert type(request_info) is Schema__Request__Info
        assert request_info.method == 'GET'
        assert request_info.host == 'example.com'
        assert request_info.port == 443
        assert request_info.path == '/api/test'
        assert request_info.scheme == 'https'
        assert request_info.query_params == {'key': 'value'}
        assert request_info.user_agent == 'Test/1.0'

    def test_parse_request_info__no_query(self):                  # Test without query string
        request_info = self.service.parse_request_info(
            method  = 'GET',
            host    = 'example.com',
            port    = 443,
            path    = '/test',
            scheme  = 'https',
            headers = {}
        )

        assert request_info.query_params == {}

    def test_parse_request_info__extracts_headers(self):          # Test header extraction
        request_info = self.service.parse_request_info(
            method  = 'POST',
            host    = 'api.example.com',
            port    = 443,
            path    = '/data',
            scheme  = 'https',
            headers = {
                'content-type': 'application/json',
                'User-Agent': 'Mozilla/5.0',
                'Origin': 'https://frontend.com'
            }
        )

        assert request_info.content_type == 'application/json'
        assert request_info.user_agent == 'Mozilla/5.0'
        assert request_info.origin == 'https://frontend.com'

    def test_parse_debug_params(self):                            # Test debug param parsing
        request_info = self.service.parse_request_info(
            method       = 'GET',
            host         = 'example.com',
            port         = 443,
            path         = '/test',
            scheme       = 'https',
            headers      = {},
            query_string = 'show=url-to-html&debug=true'
        )

        debug_params = self.service.parse_debug_params(request_info)

        assert type(debug_params) is Schema__Debug__Params
        assert debug_params.show_value == 'url-to-html'
        assert debug_params.debug_enabled is True

    def test_extract_request_data(self):                          # Test complete data extraction
        data = self.service.extract_request_data(
            method       = 'GET',
            host         = 'example.com',
            port         = 443,
            path         = '/api/users',
            scheme       = 'https',
            headers      = {'Authorization': 'Bearer token'},
            query_string = 'page=1&limit=10'
        )

        assert type(data) is dict
        assert data['method'] == 'GET'
        assert data['host'] == 'example.com'
        assert data['path'] == '/api/users'
        assert data['url'] == 'https://example.com/api/users?page=1&limit=10'
        assert data['query_params'] == {'page': '1', 'limit': '10'}

    def test_extract_debug_params(self):                          # Test debug param extraction
        debug_params = self.service.extract_debug_params(
            method       = 'GET',
            host         = 'example.com',
            port         = 443,
            path         = '/test',
            scheme       = 'https',
            headers      = {},
            query_string = 'show=response-data&other=value'
        )

        assert type(debug_params) is Type_Safe__Dict
        assert debug_params == {'show': 'response-data'}
        assert 'other' not in debug_params

    def test_extract_debug_params__no_debug(self):                # Test with no debug params
        debug_params = self.service.extract_debug_params(
            method       = 'GET',
            host         = 'example.com',
            port         = 443,
            path         = '/test',
            scheme       = 'https',
            headers      = {},
            query_string = 'search=test&page=1'
        )

        assert debug_params == {}

    def test_should_process_debug_commands__true(self):           # Test debug detection
        result = self.service.should_process_debug_commands(
            'show=url-to-html&other=value'
        )

        assert result is True

    def test_should_process_debug_commands__false(self):          # Test no debug detection
        result = self.service.should_process_debug_commands(
            'search=test&page=1'
        )

        assert result is False

    def test_should_process_debug_commands__no_query(self):       # Test with no query
        result = self.service.should_process_debug_commands(None)

        assert result is False

    def test_clean_url_for_backend__remove_debug(self):           # Test URL cleaning
        url = 'https://example.com/api/test?show=url-to-html&debug=true&key=value'

        cleaned = self.service.clean_url_for_backend(url, remove_debug=True)

        assert 'show=' not in cleaned
        assert 'debug=' not in cleaned
        assert 'key=value' in cleaned

    def test_clean_url_for_backend__keep_debug(self):             # Test keep debug params
        url = 'https://example.com/test?show=url-to-html&key=value'

        cleaned = self.service.clean_url_for_backend(url, remove_debug=False)

        assert cleaned == url

    def test_clean_url_for_backend__no_query(self):               # Test URL with no query
        url = 'https://example.com/test'

        cleaned = self.service.clean_url_for_backend(url, remove_debug=True)

        assert cleaned == url

    def test_clean_url_for_backend__only_debug_params(self):      # Test URL with only debug params
        url = 'https://example.com/test?show=url-to-html&debug=true'

        cleaned = self.service.clean_url_for_backend(url, remove_debug=True)

        assert cleaned == 'https://example.com/test'
        assert '?' not in cleaned