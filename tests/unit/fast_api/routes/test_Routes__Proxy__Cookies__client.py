import pytest
from unittest                                           import TestCase
from osbot_fast_api.api.schemas.consts.consts__Fast_API import ENV_VAR__FAST_API__AUTH__API_KEY__NAME, ENV_VAR__FAST_API__AUTH__API_KEY__VALUE
from osbot_utils.testing.Temp_Env_Vars                  import Temp_Env_Vars
from osbot_utils.testing.__                             import __
from osbot_utils.testing.__helpers                      import obj
from osbot_utils.utils.Json                             import str_to_json
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs  import setup__service_fast_api_test_objs, TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__Proxy__Cookies__client(TestCase):                                         # Test cookie-based proxy control via FastAPI TestClient

    @classmethod
    def setUpClass(cls):
        env_vars = { ENV_VAR__FAST_API__AUTH__API_KEY__NAME        : TEST_API_KEY__NAME         ,
                     ENV_VAR__FAST_API__AUTH__API_KEY__VALUE       : TEST_API_KEY__VALUE        }
        cls.temp_env_vars = Temp_Env_Vars(env_vars=env_vars).set_vars()

        cls.test_objs = setup__service_fast_api_test_objs()
        cls.client    = cls.test_objs.fast_api__client
        cls.app       = cls.test_objs.fast_api__app

        cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE                         # Set authentication

        cls.test_url          = 'https://example.com/test'                                    # Test target URL
        cls.test_namespace    = 'test-cookies'                                                # Test namespace
        cls.test_request_body = {                                                             # Basic request body
            'method'       : 'GET',
            'host'         : 'example.com',
            'path'         : '/test',
            'original_path': '/test',
            'headers'      : {},
            'stats'        : {},
            'version'      : 'v1.0.0'
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp_env_vars.restore_vars()

    def auth_headers(self):
        return {TEST_API_KEY__NAME: TEST_API_KEY__VALUE}

    def test__health_check(self):                                                             # Verify API is accessible
        response = self.client.get('/info/health')
        assert response.status_code == 200
        assert response.json()       == {'status': 'ok'}

    def test__process_request__no_cookies(self):                                              # Test request processing without cookies
        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=self.test_request_body)

        assert response.status_code == 200
        result = response.json()

        assert 'headers_to_add'    in result
        assert 'headers_to_remove' in result
        assert result['headers_to_add'] == {}                                                 # Upstream debug headers are opt-in (mitm-debug cookie / x-mitm-debug header)

    def test__process_request__with_show_cookie(self):                                        # Test with mitm-show cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-show=url-to-html; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        assert 'x-proxy-cookies' in result['headers_to_add']                                  # Cookie summary added
        assert 'x-debug-params'  in result['headers_to_add']                                  # Debug params from cookie

    def test__process_request__with_debug_cookie(self):                                       # Test with mitm-debug cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        assert 'x-proxy-cookies' in result['headers_to_add']
        assert 'x-debug-params'  in result['headers_to_add']

        import json
        debug_params = json.loads(result['headers_to_add']['x-debug-params'])
        assert debug_params['debug'] == 'true'

    def test__process_request__with_multiple_cookies(self):                                   # Test with multiple proxy cookies
        request_body = self.test_request_body.copy()
        request_body['headers'] = {
            'cookie': 'mitm-show=url-to-html; mitm-debug=true; mitm-inject=debug-panel; mitm-rating=0.5'
        }

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        assert 'x-proxy-cookies' in result['headers_to_add']

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['show_command']    == 'url-to-html'
        assert cookie_summary['debug_enabled']   is True
        assert cookie_summary['inject_command']  == 'debug-panel'
        assert cookie_summary['rating']          == 0.5

    def test__process_request__cookie_priority_over_query(self):                              # Test cookies override query params
        request_body = self.test_request_body.copy()
        request_body['headers']      = {'cookie': 'mitm-show=url-to-html; mitm-debug=true'}                   # Cookie value
        request_body['debug_params'] = {'show': 'url-to-text'}                               # Query param value

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        debug_params = json.loads(result['headers_to_add']['x-debug-params'])
        assert debug_params['show'] == 'url-to-html'                                          # Cookie wins

    def test__process_request__with_cache_cookie(self):                                       # Test with mitm-cache cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-cache=true; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['cache_enabled'] is True

    def test__process_request__with_rating_cookie(self):                                      # Test with mitm-rating cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-rating=0.7; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['rating'] == 0.7

    def test__process_request__with_model_cookie(self):                                       # Test with mitm-model cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-model=gpt-4; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['model_override'] == 'gpt-4'

    def test__process_request__with_replace_cookie(self):                                     # Test with mitm-replace cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-replace=Hello:Hi; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['replace_command'] == 'Hello:Hi'

    def test__process_request__with_inject_cookie(self):                                      # Test with mitm-inject cookie
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-inject=debug-panel; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['inject_command'] == 'debug-panel'

    def test__process_request__mixed_proxy_and_regular_cookies(self):                         # Test proxy cookies filtered from regular cookies
        request_body = self.test_request_body.copy()
        request_body['headers'] = {
            'cookie': 'session=abc123; mitm-show=url-to-html; user=john; mitm-debug=true; theme=dark'
        }

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        proxy_cookies  = cookie_summary['all_proxy_cookies']

        assert 'mitm-show'  in proxy_cookies
        assert 'mitm-debug' in proxy_cookies
        assert 'session'    not in proxy_cookies                                               # Regular cookie filtered
        assert 'user'       not in proxy_cookies
        assert 'theme'      not in proxy_cookies

    def test__process_request__all_wcf_commands(self):                                        # Test all WCF command types
        wcf_commands = [
            'url-to-html',
            'url-to-html-xxx',
            'url-to-html-hashes'
            'url-to-html-min-rating',
            'url-to-ratings',
            'url-to-text-nodes',
            'url-to-lines',
            'url-to-text'
        ]

        for command in wcf_commands:
            with self.subTest(command=command):
                request_body = self.test_request_body.copy()
                request_body['headers'] = {'cookie': f'mitm-show={command}; mitm-debug=true'}

                response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

                assert response.status_code == 200
                result = response.json()

                import json
                cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
                assert cookie_summary['show_command']   == command
                assert cookie_summary['is_wcf_command'] is True

    def test__process_request__debug_modes(self):                                             # Test different debug mode values
        debug_values = ['true', '1', 'yes', 'on', 'True', 'TRUE']

        for value in debug_values:
            with self.subTest(value=value):
                request_body = self.test_request_body.copy()
                request_body['headers'] = {'cookie': f'mitm-debug={value}'}

                response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

                assert response.status_code == 200
                result = response.json()

                import json
                cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
                assert cookie_summary['debug_enabled'] is True, f"Failed for value: {value}"

    def test__process_request__rating_formats(self):                                          # Test different rating formats
        rating_tests = [
            ('0.5',   0.5  ),
            ('0.75',  0.75 ),
            ('1.0',   1.0  ),
            ('0',     0.0  ),
            ('1',     1.0  ),
            ('.5',    0.5  ),
            ('0.999', 0.999)
        ]

        for value, expected in rating_tests:
            with self.subTest(value=value):
                request_body = self.test_request_body.copy()
                request_body['headers'] = {'cookie': f'mitm-rating={value}; mitm-debug=true'}

                response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

                assert response.status_code == 200
                result = response.json()

                import json
                cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
                assert cookie_summary['rating'] == expected

    def test__process_request__case_insensitive_cookie_header(self):                          # Test Cookie vs cookie header
        test_cases = [
            {'cookie': 'mitm-show=url-to-html; mitm-debug=true'},                                               # Lowercase
            {'Cookie': 'mitm-show=url-to-html; mitm-debug=true'}                                                # Uppercase
        ]

        for headers in test_cases:
            with self.subTest(header=list(headers.keys())[0]):
                request_body = self.test_request_body.copy()
                request_body['headers'] = headers

                response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

                assert response.status_code == 200
                result = response.json()
                assert 'x-proxy-cookies' in result['headers_to_add']

    def test__process_request__empty_cookie_value(self):                                      # Test empty cookie values
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': ''}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()
        assert 'x-proxy-cookies' not in result['headers_to_add']                              # No proxy cookies

    def test__process_request__malformed_cookie(self):                                        # Test malformed cookie format
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-show'}                                     # Missing value

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200                                                    # Should not crash

    def test__process_response__with_cookies(self):                                           # Test response processing with cookies
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test',
                'headers' : {'cookie': 'mitm-debug=true'}
            },
            'debug_params': {},
            'response': {
                'status_code'  : 200,
                'content_type' : 'text/html',
                'body'         : '<html></html>',
                'headers'      : {}
            },
            'stats'   : {},
            'version' : 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', headers=self.auth_headers(), json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert 'x-proxy-cookie-summary'                  in result['headers_to_add']
        assert str_to_json(result['headers_to_add']['x-proxy-cookie-summary'])      == {}           # todo BUG This should serialise to json
        assert result['headers_to_add']['x-proxy-cookie-summary'] == ("{'show_command': None, 'inject_command': None, 'replace_command': None, "    # todo: BUG This should serialise to json
                                                                         "'debug_enabled': True, 'rating': None, 'model_override': None, "
                                                                         "'cache_enabled': False, 'is_wcf_command': False, 'all_proxy_cookies': "
                                                                         "{'mitm-debug': 'true'}}")
        assert obj(str_to_json(result['headers_to_add']['x-proxy-cookie-summary'])) == __()         # todo BUG: we should have a valid json to convert


    def test__process_response__cookie_priority(self):                                        # Test cookie priority in response processing
        pytest.skip("needs fixing after adding cache support")
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test',
                'headers' : {'cookie': 'mitm-show=url-to-html; mitm-debug=true'}                               # Cookie value
            },
            'debug_params': {'show': 'url-to-text'},                                          # Query param value
            'response': {
                'status_code'  : 200,
                'content_type' : 'text/html',
                'body'         : '<html></html>',
                'headers'      : {}
            },
            'stats'   : {},
            'version' : 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', headers=self.auth_headers(), json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert 'final_headers'      not in result                           # this doesn't exist anymore
        assert 'x-proxy-cookie-summary' in result['headers_to_add']         # where this value is now here

    def test__process_response__multiple_cookies(self):                                       # Test response with multiple cookies
        pytest.skip("needs fixing after adding cache support (also find a better side than example.com since that is not being very stable)")
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test',
                'headers' : {
                    'cookie': 'mitm-show=url-to-html; mitm-debug=true; mitm-inject=debug-panel; mitm-rating=0.5'
                }
            },
            'debug_params': {},
            'response': {
                'status_code'  : 200,
                'content_type' : 'text/html',
                'body'         : '<html></html>',
                'headers'      : {}
            },
            'stats'   : {},
            'version' : 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', headers=self.auth_headers(), json=response_body)

        assert response.status_code == 200
        result = response.json()
        assert result['headers_to_add']['x-debug-mode'] == 'active'
        assert 'x-proxy-cookie-summary'    in result['headers_to_add']

    def test__process_request__performance_with_cookies(self):                                # Test multiple rapid requests with cookies
        import time

        cookie_combinations = ['mitm-show=url-to-html'                  ,
                               'mitm-debug=true'                        ,
                               'mitm-show=url-to-html; mitm-debug=true' ,
                               'mitm-show=url-to-text; mitm-rating=0.5' ,
                               'mitm-cache=true; mitm-model=gpt-4'      ]

        start_time = time.time()

        for cookies in cookie_combinations:
            request_body = self.test_request_body.copy()
            request_body['headers'] = {'cookie': cookies}

            response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)
            assert response.status_code == 200

        elapsed = time.time() - start_time
        assert elapsed < 1.0                                                                   # Should be fast

    def test__process_request__special_characters_in_values(self):                            # Test special characters in cookie values
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-replace=Hello:Hi%20There; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert cookie_summary['replace_command'] == 'Hello:Hi%20There'

    def test__process_request__unicode_in_cookies(self):                                      # Test unicode characters in cookies
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-replace=Hello:你好'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200                                                    # Should handle gracefully

    def test__process_request__very_long_cookie_value(self):                                  # Test long cookie values
        long_value = 'x' * 1000
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': f'mitm-model={long_value}; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])
        assert len(cookie_summary['model_override']) == 1000

    def test__process_request__not__auth_required(self):                                      # Confirm that auth is currently not enabled
        auth_header = self.client.headers.pop(TEST_API_KEY__NAME)                             # Remove auth temporarily

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=self.test_request_body)
        assert response.status_code != 401
        assert response.status_code == 200

        self.client.headers[TEST_API_KEY__NAME] = auth_header                                 # Restore auth

    def test__cookie_summary_structure(self):                                                 # Test cookie summary JSON structure
        request_body = self.test_request_body.copy()
        request_body['headers'] = {'cookie': 'mitm-show=url-to-html; mitm-debug=true'}

        response = self.client.post('/proxy/process-request', headers=self.auth_headers(), json=request_body)

        assert response.status_code == 200
        result = response.json()

        import json
        cookie_summary = json.loads(result['headers_to_add']['x-proxy-cookies'])

        required_fields = [
            'show_command',
            'inject_command',
            'replace_command',
            'debug_enabled',
            'rating',
            'model_override',
            'cache_enabled',
            'is_wcf_command',
            'all_proxy_cookies'
        ]

        for field in required_fields:
            assert field in cookie_summary, f"Missing field: {field}"