from unittest                                                                           import TestCase
from mgraph_ai_service_cache_client.client.cache_service.register_cache_service         import register_cache_service__in_memory
from osbot_fast_api.services.registry.Fast_API__Service__Registry                       import fast_api__service__registry
from osbot_utils.testing.__                                                             import __, __SKIP__
from osbot_utils.testing.__helpers                                                      import obj
from osbot_utils.utils.Json                                                             import str_to_json
from mgraph_ai_service_mitmproxy.service.html.client.register_html_service              import register_html_service__in_memory
from mgraph_ai_service_mitmproxy.service.semantic_text.register_semantic_text_service   import register_semantic_text_service__in_memory
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs                                  import setup__service_fast_api_test_objs, TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__Proxy__HTML_Transformation__client(TestCase):               # Test HTML transformation via FastAPI TestClient


    @classmethod
    def setUpClass(cls):

        fast_api__service__registry.configs__save()
        register_cache_service__in_memory        ()
        register_html_service__in_memory         ()
        register_semantic_text_service__in_memory()

        cls.test_objs = setup__service_fast_api_test_objs()
        cls.client    = cls.test_objs.fast_api__client
        cls.app       = cls.test_objs.fast_api__app

        cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE            # Set authentication

        cls.test_request_body = { 'method'       : 'GET'        ,     # Basic request body template
                                  'host'         : 'example.com',
                                  'path'         : '/test'      ,
                                  'original_path': '/test'      ,
                                  'headers'      : {}           ,
                                  'stats'        : {}           ,
                                  'version'      : 'v1.0.0'     }

    @classmethod
    def tearDownClass(cls):
        fast_api__service__registry.configs__restore()

    def test__health_check(self):                                               # Verify API is accessible
        response = self.client.get('/info/health')
        assert response.status_code == 200
        assert response.json()       == {'status': 'ok'}

    def test__process_response__no_html_transformation(self):                          # Test response processing WITHOUT mitm-mode cookie
        response_body = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/test'                              ,
                                        'headers' : {}                                   },   # No mitm-mode cookie
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body>Original content</body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code         == 200
        result = response.json()

        assert 'headers_to_add'             in result
        assert 'headers_to_remove'          in result
        assert 'modified_body'              in result
        assert result['modified_body']      is None                                       # No transformation

        assert obj(result) == __( headers_to_add         = __( x_proxy_service        = 'mgraph-proxy'           ,
                                                               x_proxy_version        = '1.0.0'                  ,
                                                               x_request_id           = __SKIP__                 ,
                                                               x_processed_at         = __SKIP__                 ,
                                                               x_original_host        = 'example.com'           ,
                                                               x_original_path        = '/test'                 ) ,
                                   headers_to_remove     = []                                                    ,
                                   cached_response       = __()                                                  ,
                                   block_request         = False                                                 ,
                                   block_status          = 403                                                   ,
                                   block_message         = 'Blocked by proxy'                                    ,
                                   include_stats         = False                                                 ,
                                   stats                 = __()                                                  ,
                                   modified_body         = None                                                  ,
                                   override_response     = False                                                 ,
                                   override_status       = None                                                  ,
                                   override_content_type = None                                                  )


    def test__process_response__with_mode_off(self):                           # Test response with mitm-mode=off cookie
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test',
                'headers' : {'cookie': 'mitm-mode=off'}                         # Explicit OFF mode
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body>Content</body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is None                                  # OFF mode = no transformation
        assert 'x-proxy-service'       in result['headers_to_add']

    def test__process_response__with_mode_hashes(self):                        # Test HTML transformation with mitm-mode=hashes
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test-with-mode-hashes',
                'headers' : {'cookie': 'mitm-mode=hashes'}                      # HASHES mode
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Test content here</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is not None                              # Transformation applied
        assert '<html>'                in result['modified_body']               # Still HTML
        assert 'Test content here'     not in result['modified_body']           # Original text replaced
        assert obj(result) == __( headers_to_add         = __(   x_proxy_service        = 'mgraph-proxy'           ,
                                                                 x_proxy_version        = '1.0.0'                  ,
                                                                 x_request_id           = __SKIP__                 ,
                                                                 x_processed_at         = __SKIP__                 ,
                                                                 x_original_host        = 'example.com'            ,
                                                                 x_original_path        = '/test-with-mode-hashes'                  ,
                                                                 x_proxy_cookie_summary = ("{'show_command': None, "
                                                                                            "'inject_command': None, "
                                                                                            "'replace_command': None, "
                                                                                            "'debug_enabled': False, "
                                                                                            "'rating': None, "
                                                                                            "'model_override': None, "
                                                                                            "'cache_enabled': False, "
                                                                                            "'is_wcf_command': False, "
                                                                                            "'all_proxy_cookies': {'mitm-mode': 'hashes'}}") ,
                                                                 x_proxy_transformation = 'hashes'                   ,
                                                                 x_proxy_cache          = 'miss'                     ,
                                                                 x_html_service_time    = __SKIP__                   ,
                                                                 content_type           = 'text/html'                ),
                                    headers_to_remove      = []                                                      ,
                                    cached_response        = __()                                                    ,
                                    block_request          = False                                                   ,
                                    block_status           = 403                                                     ,
                                    block_message          = 'Blocked by proxy'                                      ,
                                    include_stats          = False                                                   ,
                                    stats                  = __()                                                    ,
                                    modified_body          = ('<!DOCTYPE html>\n'
                                                              '<html>\n'
                                                              '    <body>\n'
                                                              '        <p>56947f3c4f</p>\n'
                                                              '    </body>\n'
                                                              '</html>')                                           ,
                                    override_response      = False                                                 ,
                                    override_status        = None                                                  ,
                                    override_content_type  = None                                                  )


    def test__process_response__with_mode_xxx(self):                           # Test HTML transformation with mitm-mode=xxx
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example-2.com',
                'path'    : '/secret-2',
                'headers' : {'cookie': 'mitm-mode=xxx'}                         # XXX mode
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Secret text here!</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body']  is not None
        assert '<html>'                 in result['modified_body']               # HTML structure preserved
        assert 'Secret text'            not in result['modified_body']           # Text replaced
        assert 'xxx'                    in result['modified_body']               # Contains xxx
        assert 'x-proxy-transformation' in result['headers_to_add']
        assert result['headers_to_add']['x-proxy-transformation'] == 'xxx'
        assert obj(result)              == __( headers_to_add         = __(  x_proxy_service        = 'mgraph-proxy'           ,
                                                                             x_proxy_version        = '1.0.0'                  ,
                                                                             x_request_id           = __SKIP__                 ,
                                                                             x_processed_at         = __SKIP__                 ,
                                                                             x_original_host        = 'example-2.com'            ,
                                                                             x_original_path        = '/secret-2'                ,
                                                                             x_proxy_cookie_summary = ("{'show_command': None, "
                                                                                                        "'inject_command': None, "
                                                                                                        "'replace_command': None, "
                                                                                                        "'debug_enabled': False, "
                                                                                                        "'rating': None, "
                                                                                                        "'model_override': None, "
                                                                                                        "'cache_enabled': False, "
                                                                                                        "'is_wcf_command': False, "
                                                                                                        "'all_proxy_cookies': {'mitm-mode': 'xxx'}}") ,
                                                                             x_proxy_transformation = 'xxx'                    ,
                                                                             x_proxy_cache          = 'miss'                   ,
                                                                             x_html_service_time    = __SKIP__                 ,
                                                                             content_type           = 'text/html'              ) ,
                                                headers_to_remove      = []                                                    ,
                                                cached_response        = __()                                                  ,
                                                block_request          = False                                                 ,
                                                block_status           = 403                                                   ,
                                                block_message          = 'Blocked by proxy'                                    ,
                                                include_stats          = False                                                 ,
                                                stats                  = __()                                                  ,
                                                modified_body          = ('<!DOCTYPE html>\n'
                                                                          '<html>\n'
                                                                          '    <body>\n'
                                                                          '        <p>xxxxxx xxxx xxxx!</p>\n'
                                                                          '    </body>\n'
                                                                          '</html>')                                           ,
                                                override_response      = False                                                 ,
                                                override_status        = None                                                  ,
                                                override_content_type  = None                                                  )


    def test__process_response__with_mode_ratings(self):                       # Test HTML transformation with mitm-mode=ratings
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/content',
                'headers' : {'cookie': 'mitm-mode=ratings'}                     # RATINGS mode
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Content for rating</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body']  is None

    def test__process_response__with_mode_roundtrip(self):                     # Test HTML transformation with mitm-mode=roundtrip
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/roundtrip',
                'headers' : {'cookie': 'mitm-mode=roundtrip'}                   # ROUNDTRIP mode
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><head><title>Test</title></head><body><p>Content</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is not None
        assert '<html>'                in result['modified_body']
        #assert '<title>Test</title>'   in result['modified_body']               # Content preserved
        assert result['headers_to_add']['x-proxy-transformation'] == 'roundtrip'

        assert obj(result)              == __( headers_to_add         = __(  x_proxy_service        = 'mgraph-proxy'           ,
                                                                             x_proxy_version        = '1.0.0'                  ,
                                                                             x_request_id           = __SKIP__                 ,
                                                                             x_processed_at         = __SKIP__                 ,
                                                                             x_original_host        = 'example.com'            ,
                                                                             x_original_path        = '/roundtrip'             ,
                                                                             x_proxy_cookie_summary = ("{'show_command': None, "
                                                                                                        "'inject_command': None, "
                                                                                                        "'replace_command': None, "
                                                                                                        "'debug_enabled': False, "
                                                                                                        "'rating': None, "
                                                                                                        "'model_override': None, "
                                                                                                        "'cache_enabled': False, "
                                                                                                        "'is_wcf_command': False, "
                                                                                                        "'all_proxy_cookies': {'mitm-mode': 'roundtrip'}}") ,
                                                                             x_proxy_transformation = 'roundtrip'              ,
                                                                             x_proxy_cache          = 'miss'                   ,
                                                                             x_html_service_time    = __SKIP__                 ,
                                                                             content_type           = 'text/html'              ) ,
                                                headers_to_remove      = []                                                    ,
                                                cached_response        = __()                                                  ,
                                                block_request          = False                                                 ,
                                                block_status           = 403                                                   ,
                                                block_message          = 'Blocked by proxy'                                    ,
                                                include_stats          = False                                                 ,
                                                stats                  = __()                                                  ,
                                                modified_body          = ('<!DOCTYPE html>\n'
                                                                          '<html>\n'
                                                                          '    <head>\n'
                                                                          '        <title>xxxx</title>\n'
                                                                          '    </head>\n'
                                                                          '    <body>\n'
                                                                          '        <p>xxxxxxx</p>\n'
                                                                          '    </body>\n'
                                                                          '</html>')                                           ,
                                                override_response      = False                                                 ,
                                                override_status        = None                                                  ,
                                                override_content_type  = None                                                  )


    def test__process_response__non_html_content(self):                        # Test that non-HTML content is NOT transformed
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'api.example.com',
                'path'    : '/api/data',
                'headers' : {'cookie': 'mitm-mode=hashes'}                      # Mode enabled
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'application/json'},           # JSON not HTML
                'content_type': 'application/json',
                'body'        : '{"data": "value"}'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is None                                  # JSON not transformed
        assert 'x-html-transformation-mode' not in result['headers_to_add']     # No transformation headers

    def test__process_response__empty_body(self):                              # Test handling of empty response body
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/empty',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 204,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : ''                                              # Empty body
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is None                                  # Empty body not transformed
        assert 'x-html-transformation-mode' not in result['headers_to_add']

    def test__process_response__transformation_headers(self):                  # Test all transformation headers are present
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/test-headers',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Header test</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        headers = result['headers_to_add']

        assert headers['x-proxy-transformation' ] == 'hashes'
        assert headers['x-proxy-cache'          ] in ['hit', 'miss']
        assert headers['content-type'           ] == 'text/html'

    def test__bug__process_response__with_multiple_cookies(self):                   # Test HTML transformation works with other cookies

        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/multi-cookie',
                'headers' : {'cookie': 'mitm-mode=hashes; mitm-debug=true; session=abc123'}  # Multiple cookies
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Multi-cookie test</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'   ] is not None                              # Transformation still works
        assert 'x-proxy-transformation'   in result['headers_to_add']
        assert 'x-proxy-cookie-summary'   in result['headers_to_add']         # Cookie summary present

        assert obj(result) == __( headers_to_add           = __( x_proxy_service        = 'mgraph-proxy'           ,
                                                                 x_proxy_version        = '1.0.0'                  ,
                                                                 x_request_id           = __SKIP__                 ,
                                                                 x_processed_at         = __SKIP__                 ,
                                                                 x_original_host        = 'example.com'            ,
                                                                 x_original_path        = '/multi-cookie'          ,
                                                                 x_proxy_cookie_summary = ("{'show_command': None, "
                                                                                            "'inject_command': None, "
                                                                                            "'replace_command': None, "
                                                                                            "'debug_enabled': True, "
                                                                                            "'rating': None, "
                                                                                            "'model_override': None, "
                                                                                            "'cache_enabled': False, "
                                                                                            "'is_wcf_command': False, "
                                                                                            "'all_proxy_cookies': {"
                                                                                            "'mitm-mode': 'hashes', "
                                                                                            "'mitm-debug': 'true'}}") ,
                                                                 x_debug_banner_injected = 'true'                  ,
                                                                 x_proxy_transformation  = 'hashes'                ,
                                                                 x_proxy_cache           = 'miss'                  ,
                                                                 x_html_service_time     = __SKIP__                ,
                                                                 content_type            = 'text/html'            ) ,
                                    headers_to_remove      = []                                                    ,
                                    cached_response        = __()                                                  ,
                                    block_request          = False                                                 ,
                                    block_status           = 403                                                   ,
                                    block_message          = 'Blocked by proxy'                                    ,
                                    include_stats          = False                                                 ,
                                    stats                  = __()                                                  ,
                                    modified_body          = ('<!DOCTYPE html>\n'
                                                              '<html>\n'
                                                              '    <body>\n'
                                                              '        <p>0d896ebead</p>\n'
                                                              '    </body>\n'
                                                              '</html>')                                           ,
                                    override_response      = False                                                 ,
                                    override_status        = None                                                  ,
                                    override_content_type  = None                                                  )


        print()
        cookie_summary = result['headers_to_add']['x-proxy-cookie-summary']
        assert cookie_summary == ("{'show_command': None, 'inject_command': None, 'replace_command': None, "
                                  "'debug_enabled': True, 'rating': None, 'model_override': None, "
                                  "'cache_enabled': False, 'is_wcf_command': False, 'all_proxy_cookies': "
                                  "{'mitm-mode': 'hashes', 'mitm-debug': 'true'}}")

        assert str_to_json(cookie_summary) == {}        # BUG: cookie_summary is not serialising ok
        # cookie_summary = str_to_json(result['headers_to_add']['x-proxy-cookie-summary'])
        # assert 'transformation_mode' in cookie_summary or 'mode' in cookie_summary  # Mode extracted from cookie

    def test__process_response__cache_miss_then_hit(self):                     # Test cache behavior across multiple calls
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/cache-test-client',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Cache test content</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        # First call - cache miss
        response_1 = self.client.post('/proxy/process-response', json=response_body)
        assert response_1.status_code == 200
        result_1 = response_1.json()
        assert result_1['headers_to_add']['x-proxy-cache'] == 'miss'
        transformed_body_1 = result_1['modified_body']

        # Second call - cache hit
        response_2 = self.client.post('/proxy/process-response', json=response_body)
        assert response_2.status_code == 200
        result_2 = response_2.json()
        assert result_2['headers_to_add']['x-proxy-cache'] == 'hit'
        transformed_body_2 = result_2['modified_body']

        assert transformed_body_2 == transformed_body_1                         # Same transformed content

    def test__process_response__with_mode_min_rating(self):                    # Test HTML transformation with mitm-mode=min-rating
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/filtered',
                'headers' : {'cookie': 'mitm-mode=min-rating:0.7'}              # MIN_RATING mode with value
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Content to filter by rating</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()
        assert result['modified_body'] is None                                   # todo: add this mode

        #assert result['modified_body'] is not None                              # Transformation applied
        #assert 'x-html-transformation-mode' in result['headers_to_add']
        # Mode might be min-rating or min_rating depending on implementation
        #assert 'min' in result['headers_to_add']['x-html-transformation-mode'].lower()

    def test__process_response__large_html_body(self):                         # Test transformation of large HTML content
        large_html = '<html><body>' + '<p>Large content paragraph.</p>' * 100 + '</body></html>'

        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/large',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : large_html
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body'] is not None                              # Large content transformed
        assert len(result['modified_body']) > 0                                 # Has content
        assert 'x-proxy-transformation' in result['headers_to_add']

    def test__bug__process_response__stats_incremented(self):                       # Test that stats are properly updated
        # Get initial stats
        stats_response = self.client.get('/proxy/get-proxy-stats')
        assert stats_response.status_code == 200
        initial_stats = stats_response.json()
        initial_modifications = initial_stats.get('content_modifications', 0)

        # Process response with transformation
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/stats-increment',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Stats test</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        transform_response = self.client.post('/proxy/process-response', json=response_body)
        assert transform_response.status_code == 200

        # Get final stats
        final_stats_response = self.client.get('/proxy/get-proxy-stats')
        assert final_stats_response.status_code == 200
        final_stats = final_stats_response.json()
        final_modifications = final_stats.get('content_modifications', 0)

        assert final_modifications == initial_modifications  == 0               # BUG: stats are not being updated
        #assert final_modifications > initial_modifications                      # Stats incremented

    def test__process_response__with_special_html_chars(self):                 # Test transformation of HTML with special characters
        response_body = {
            'request': {
                'method'  : 'GET',
                'host'    : 'example.com',
                'path'    : '/special',
                'headers' : {'cookie': 'mitm-mode=hashes'}
            },
            'response': {
                'status_code' : 200,
                'headers'     : {'content-type': 'text/html; charset=utf-8'},
                'content_type': 'text/html; charset=utf-8',
                'body'        : '<html><body><p>Content with &amp; &lt; &gt; "quotes"</p></body></html>'
            },
            'stats'  : {},
            'version': 'v1.0.0'
        }

        response = self.client.post('/proxy/process-response', json=response_body)

        assert response.status_code == 200
        result = response.json()

        assert result['modified_body']  is not None                              # Transformation handles entities
        assert '<html>'                 in result['modified_body']
        assert 'x-proxy-transformation' in result['headers_to_add']