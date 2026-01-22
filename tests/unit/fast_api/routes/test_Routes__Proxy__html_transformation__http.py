import requests
from unittest                                                   import TestCase
from osbot_fast_api.api.schemas.consts.consts__Fast_API         import ENV_VAR__FAST_API__AUTH__API_KEY__NAME, ENV_VAR__FAST_API__AUTH__API_KEY__VALUE
from osbot_utils.helpers.duration.decorators.print_duration     import print_duration
from osbot_utils.testing.__                                     import __, __SKIP__
from osbot_utils.testing.Temp_Env_Vars                          import Temp_Env_Vars
from osbot_utils.testing.__helpers                              import obj
from osbot_utils.utils.Http                                     import GET_json
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs          import (get__cache_service__fast_api_server,
                                                                        get__html_service__fast_api_server,
                                                                        get__mitmproxy_service__fast_api_server, TEST_API_KEY__NAME, TEST_API_KEY__VALUE)


class test_Routes__Proxy__html_transformation__http(TestCase):                 # Test HTML transformation workflow via HTTP requests

    @classmethod
    def setUpClass(cls):                                                        # ONE-TIME setup: start HTML, Cache, and Mitmproxy services
        #pytest.skip("race condition with the other FAST API servers")           # todo: figure out why this runs when execute directly but fails when all executed
        with print_duration(action_name='setUpClass'):
            with get__html_service__fast_api_server() as _:
                cls.html_service_server   = _.fast_api_server
                cls.html_service_base_url = _.server_url

            with get__cache_service__fast_api_server() as _:
                cls.cache_service_server   = _.fast_api_server
                cls.cache_service_base_url = _.server_url

            env_vars = { 'AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL' : cls.html_service_base_url  ,
                         'AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL': cls.cache_service_base_url ,
                         ENV_VAR__FAST_API__AUTH__API_KEY__NAME        : TEST_API_KEY__NAME         ,
                         ENV_VAR__FAST_API__AUTH__API_KEY__VALUE       : TEST_API_KEY__VALUE        }
            cls.temp_env_vars = Temp_Env_Vars(env_vars=env_vars).set_vars()

            with get__mitmproxy_service__fast_api_server() as _:
                cls.mitmproxy_service_server   = _.fast_api_server
                cls.mitmproxy_service_base_url = _.server_url



            cls.html_service_server     .start()
            cls.cache_service_server    .start()
            cls.mitmproxy_service_server.start()

    @classmethod
    def tearDownClass(cls):                                                     # Stop all servers
        with print_duration(action_name='tearDownClass'):
            cls.html_service_server     .stop()
            cls.cache_service_server    .stop()
            cls.mitmproxy_service_server.stop()
            cls.temp_env_vars.restore_vars()

    def auth_headers(self):
        return {TEST_API_KEY__NAME: TEST_API_KEY__VALUE}

    def test__fast_api__servers(self):                                          # Verify all servers running
        assert GET_json(self.html_service_base_url      + '/info/health', headers=self.auth_headers()) == {'status': 'ok'}
        assert GET_json(self.cache_service_base_url     + '/info/health', headers=self.auth_headers()) == {'status': 'ok'}
        assert GET_json(self.mitmproxy_service_base_url + '/info/health', headers=self.auth_headers()) == {'status': 'ok'}

    def test__process_response__no_html_transformation(self):                  # Test response processing WITHOUT mitm-mode cookie via HTTP
        request_body = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/test'                              ,
                                        'headers' : {}                                   },   # No mitm-mode cookie
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body>Original content</body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = requests.post(self.mitmproxy_service_base_url + '/proxy/process-response',
                                 headers=self.auth_headers(),
                                 json=request_body)
        result   = response.json()

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

    def test__process_response__with_mode_off(self):                           # Test response with mitm-mode=off cookie via HTTP
        request_body  = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/test'                              ,
                                        'headers' : {'cookie': 'mitm-mode=off'}          },   # Explicit OFF mode
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body>Content</body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = requests.post(self.mitmproxy_service_base_url + '/proxy/process-response', headers=self.auth_headers() , json=request_body)
        result   = response.json()

        assert result['modified_body'] is None                                  # OFF mode = no transformation
        assert 'x-proxy-service'       in result['headers_to_add']
        assert result['headers_to_add']['x-proxy-cookie-summary'] is not None   # Cookie summary present

    def test__process_response__with_mode_hashes(self):                        # Test HTML transformation with mitm-mode=hashes via HTTP
        request_body  = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/test-with-hashes-http'             ,
                                        'headers' : {'cookie': 'mitm-mode=hashes'}       },   # HASHES mode
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body><p>Test content</p></body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = requests.post(self.mitmproxy_service_base_url + '/proxy/process-response', headers=self.auth_headers(), json=request_body)
        result   = response.json()


        assert result['modified_body']  is not None                             # Transformation applied
        assert '<html>'                 in result['modified_body']              # Still HTML
        assert 'Test content'           not in result['modified_body']          # Original text replaced with hash
        assert len(result['modified_body']) > 0                                 # Has content
        assert 'x-proxy-transformation' in result['headers_to_add']             # Transformation headers added
        assert result['headers_to_add']['x-proxy-transformation'] == 'hashes'

        assert obj(result) == __(   headers_to_add         = __( x_proxy_service        = 'mgraph-proxy'           ,
                                                                 x_proxy_version        = '1.0.0'                  ,
                                                                 x_request_id           = __SKIP__                 ,
                                                                 x_processed_at         = __SKIP__                 ,
                                                                 x_original_host        = 'example.com'            ,
                                                                 x_original_path        = '/test-with-hashes-http' ,
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
                                                              '        <p>8bfa8e0684</p>\n'
                                                              '    </body>\n'
                                                              '</html>')                                           ,
                                    override_response      = False                                                 ,
                                    override_status        = None                                                  ,
                                    override_content_type  = None                                                  )

    def test__process_response__with_mode_xxx(self):                           # Test HTML transformation with mitm-mode=xxx via HTTP
        response_body = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/secret-with-xxx-http'              ,
                                        'headers' : {'cookie': 'mitm-mode=xxx'}          },   # XXX mode
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body><h1>Secret</h1><p>Data</p></body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = requests.post(self.mitmproxy_service_base_url + '/proxy/process-response', headers=self.auth_headers() , json=response_body)
        result   = response.json()


        assert result['modified_body']  is not None                             # Transformation applied
        assert '<html>'                 in result['modified_body']              # Still HTML
        assert 'Secret'                 not in result['modified_body']          # Original text replaced
        assert 'Data'                   not in result['modified_body']          # Original text replaced
        assert 'xxx'                    in result['modified_body']              # Replaced with xxx
        assert 'x-proxy-transformation' in result['headers_to_add']
        assert result['headers_to_add']['x-proxy-transformation'] == 'xxx'
        assert obj(result)              == __(headers_to_add = __(    x_proxy_service          = 'mgraph-proxy'            ,
                                                                      x_proxy_version          = '1.0.0'                   ,
                                                                      x_request_id             = __SKIP__                  ,
                                                                      x_processed_at           = __SKIP__                  ,
                                                                      x_original_host          = 'example.com'            ,
                                                                      x_original_path          = '/secret-with-xxx-http'  ,
                                                                      x_proxy_cookie_summary   = "{'show_command': None, "
                                                                                                 "'inject_command': None, "
                                                                                                 "'replace_command': None, "
                                                                                                 "'debug_enabled': False, "
                                                                                                 "'rating': None, "
                                                                                                 "'model_override': None, "
                                                                                                 "'cache_enabled': False, "
                                                                                                 "'is_wcf_command': False, "
                                                                                                 "'all_proxy_cookies': "
                                                                                                 "{'mitm-mode': 'xxx'}}"   ,
                                                                      x_proxy_transformation   = 'xxx'                    ,
                                                                      x_proxy_cache            = 'miss'                   ,
                                                                      x_html_service_time      = __SKIP__                  ,
                                                                      content_type             = 'text/html'               ),
                                                headers_to_remove     = []                                                 ,
                                                cached_response       = __()                                               ,
                                                block_request         = False                                              ,
                                                block_status          = 403                                                ,
                                                block_message         = 'Blocked by proxy'                                 ,
                                                include_stats         = False                                              ,
                                                stats                 = __()                                               ,
                                                modified_body         = '<!DOCTYPE html>\n'
                                                                        '<html>\n'
                                                                        '    <body>\n'
                                                                        '        <h1>xxxxxx</h1>\n'
                                                                        '        <p>xxxx</p>\n'
                                                                        '    </body>\n'
                                                                        '</html>'                                         ,
                                                override_response     = False                                              ,
                                                override_status       = None                                               ,
                                                override_content_type = None)


    def test__process_response__with_mode_ratings(self):                       # Test HTML transformation with mitm-mode=ratings via HTTP
        response_body = { 'request' : { 'method'  : 'GET'                                ,
                                        'host'    : 'example.com'                        ,
                                        'path'    : '/ratings'                           ,
                                        'headers' : {'cookie': 'mitm-mode=ratings'}      },   # RATINGS mode
                          'response': { 'status_code' : 200                              ,
                                        'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
                                        'content_type': 'text/html; charset=utf-8'       ,
                                        'body'        : '<html><body><p>Content to rate</p></body></html>' },
                          'stats'   : {}                                                 ,
                          'version' : 'v1.0.0'                                           }

        response = requests.post(self.mitmproxy_service_base_url + '/proxy/process-response', headers=self.auth_headers() , json=response_body)
        result   = response.json()


        assert result['modified_body']  is None                                 # No ransformation applied
        #assert '<html>'                 in result['modified_body']
        #assert result['headers_to_add']['x-proxy-transformation'] == 'ratings'

    # todo: wire the tests below (which are more generic and not mitm-mode specific)

    # def test__process_response__with_show_command(self):                       # Test HTML transformation with mitm-show=url-to-html-hashes via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/show-test'                         ,
    #                                     'headers' : {'cookie': 'mitm-show=url-to-html-hashes'} },   # SHOW command
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>Test</p></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-transformation' in result['headers_to_add']
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     assert "'show_command': 'url-to-html-hashes'" in result['headers_to_add']['x-proxy-cookie-summary']
    # #
    # def test__process_response__with_inject_command(self):                     # Test HTML transformation with mitm-inject=debug-panel via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/inject-test'                       ,
    #                                     'headers' : {'cookie': 'mitm-inject=debug-panel'} },   # INJECT command
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>Test</p></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     assert "'inject_command': 'debug-panel'" in result['headers_to_add']['x-proxy-cookie-summary']
    #
    # def test__process_response__with_cache_enabled(self):                      # Test HTML transformation with caching enabled via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/cache-test'                        ,
    #                                     'headers' : {'cookie': 'mitm-mode=hashes; mitm-cache=true'} },  # Cache enabled
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>Cached content</p></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-cache'          in result['headers_to_add']             # Cache header present
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     assert "'cache_enabled': True"  in result['headers_to_add']['x-proxy-cookie-summary']
    #
    # def test__process_response__with_rating_filter(self):                      # Test HTML transformation with rating filter via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/rating-filter'                     ,
    #                                     'headers' : {'cookie': 'mitm-mode=ratings; mitm-rating=0.5'} },  # Rating filter
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>High quality</p><span>Low quality</span></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     assert "'rating': 0.5"          in result['headers_to_add']['x-proxy-cookie-summary']
    #
    # def test__process_response__with_debug_enabled(self):                      # Test HTML transformation with debug enabled via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/debug-test'                        ,
    #                                     'headers' : {'cookie': 'mitm-mode=hashes; mitm-debug=true'} },  # Debug enabled
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>Debug content</p></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     assert "'debug_enabled': True"  in result['headers_to_add']['x-proxy-cookie-summary']
    #
    # def test__process_response__non_html_content(self):                        # Test response processing with non-HTML content via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/data.json'                         ,
    #                                     'headers' : {'cookie': 'mitm-mode=hashes'}       },   # Transformation requested
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'application/json'} ,
    #                                     'content_type': 'application/json'               ,
    #                                     'body'        : '{"key": "value"}'               },   # JSON content
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body'] is None                                  # No transformation on non-HTML
    #
    # def test__process_response__empty_body(self):                              # Test response processing with empty body via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/empty'                             ,
    #                                     'headers' : {'cookie': 'mitm-mode=hashes'}       },
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : ''                               },   # Empty body
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert 'modified_body'     in result
    #     assert 'headers_to_add'    in result
    #
    # def test__process_response__with_multiple_cookies(self):                   # Test response with multiple proxy cookies via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                ,
    #                                     'host'    : 'example.com'                        ,
    #                                     'path'    : '/multi'                             ,
    #                                     'headers' : {'cookie': 'mitm-mode=hashes; mitm-debug=true; mitm-cache=true; mitm-rating=0.7'} },
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {'content-type': 'text/html; charset=utf-8'} ,
    #                                     'content_type': 'text/html; charset=utf-8'       ,
    #                                     'body'        : '<html><body><p>Multi test</p></body></html>' },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #
    #     assert result['modified_body']  is not None                             # Transformation applied
    #     assert 'x-proxy-cookie-summary' in result['headers_to_add']
    #     cookie_summary = result['headers_to_add']['x-proxy-cookie-summary']
    #     assert "'debug_enabled': True"  in cookie_summary
    #     assert "'cache_enabled': True"  in cookie_summary
    #     assert "'rating': 0.7"          in cookie_summary
    #
    # def test__process_response__error_handling(self):                          # Test error handling with invalid request via HTTP
    #     response_body = { 'request' : { 'method'  : 'GET'                                },   # Missing required fields
    #                       'response': { 'status_code' : 200                              ,
    #                                     'headers'     : {}                               ,
    #                                     'body'        : '<html></html>'                  },
    #                       'stats'   : {}                                                 ,
    #                       'version' : 'v1.0.0'                                           }
    #
    #     try:
    #         result = POST_json(self.mitmproxy_service_base_url + '/proxy/process-response', response_body)
    #         # If no error, verify we still get a valid response structure
    #         assert 'headers_to_add' in result or 'error' in result
    #     except Exception as e:
    #         # Expected to fail validation
    #         assert True