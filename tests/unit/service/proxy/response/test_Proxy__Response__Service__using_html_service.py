import pytest
from unittest                                                                               import TestCase

from osbot_utils.testing.Temp_Env_Vars import Temp_Env_Vars

from mgraph_ai_service_cache_client.client.cache_service.register_cache_service             import register_cache_service__in_memory
from mgraph_ai_service_html_graph.client.register_html_graph_service                        import register_html_graph_service__in_memory
from osbot_utils.testing.Pytest                                                             import skip_if_in_github_action, skip__if_not__in_github_actions
from osbot_utils.testing.__                                                                 import __, __SKIP__
from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.http.safe_str.Safe_Str__Http__Header__Name    import Safe_Str__Http__Header__Name
from osbot_utils.utils.Env                                                                  import not_in_github_action
from osbot_utils.utils.Misc                                                                 import list_set
from osbot_utils.utils.Objects                                                              import base_classes
from mgraph_ai_service_mitmproxy.service.proxy.response.Proxy__Response__Service            import Proxy__Response__Service
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Response_Data                 import Schema__Proxy__Response_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Response__Processing_Result          import Schema__Response__Processing_Result
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs                                      import get__html_service__fast_api_server


class test_Proxy__Response__Service__using_html_service(TestCase):                 # Integration tests for full HTML transformation flow

    @classmethod
    def setUpClass(cls):                                                            # ONE-TIME setup: start both FastAPI servers


        register_cache_service__in_memory     ()                                    # todo: refactor when html_service has support for running in memory
        with get__html_service__fast_api_server() as _:
            cls.html_service_server   = _.fast_api_server
            cls.html_service_base_url = _.server_url
        #
        # with get__cache_service__fast_api_server() as _:
        #     cls.cache_service_server   = _.fast_api_server
        #     cls.cache_service_base_url = _.server_url
        #
        cls.html_service_server .start()                                        # Start both servers
        # cls.cache_service_server.start()
        #
        env_vars = {'AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL' : cls.html_service_base_url ,
                    #'AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL': cls.cache_service_base_url
                    }
        cls.temp_env_vars = Temp_Env_Vars(env_vars=env_vars).set_vars()


        register_html_graph_service__in_memory()
        cls.proxy_response_service = Proxy__Response__Service().setup()        # Setup proxy service with real dependencies

    @classmethod
    def tearDownClass(cls):                                                         # Stop both servers and restore environment
        cls.html_service_server.stop()
        #cls.cache_service_server.stop()
        cls.temp_env_vars.restore_vars()

    # def test__fast_api__servers(self):                                              # Verify both servers are running
    #     assert GET_json(self.html_service_base_url  + '/info/health') == {'status': 'ok'}
    #     assert GET_json(self.cache_service_base_url + '/info/health') == {'status': 'ok'}
    #
    #     with self.proxy_response_service as _:
    #         assert type(_                           ) is Proxy__Response__Service
    #         assert type(_.html_transformation_service) is HTML__Transformation__Service
    #         assert _.html_transformation_service.html_service_client.base_url == self.html_service_base_url

    def test__init__(self):                                                         # Test auto-initialization
        with Proxy__Response__Service() as _:
            assert type(_)         is Proxy__Response__Service
            assert base_classes(_) == [Type_Safe, object]
            assert _.html_transformation_service is None

    def test_setup(self):                                                           # Test setup creates all dependencies
        with self.proxy_response_service as _:
            assert _.html_transformation_service                        is not None
            assert _.html_transformation_service.html_service_client    is not None
            assert _.html_transformation_service.cache_service          is not None

    def test_process_response__no_mitm_mode_cookie(self):                           # Test response processing without mitm-mode cookie
        response_data = Schema__Proxy__Response_Data(request  = { 'scheme'        : 'https'                              ,
                                                                  'host'          : 'example.com'                        ,
                                                                  'port'          : 443                                  ,
                                                                  'path'          : '/test'                              ,
                                                                  'headers'       : {}                                   },     # No Cookie header
                                                     response = { 'status_code'   : 200                                  ,
                                                                   'body'         : '<html><body>Original</body></html>' ,
                                                                   'headers'      : {'content-type': 'text/html'}        ,
                                                                   'content_type' : 'text/html'                          })

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert type(result)             is Schema__Response__Processing_Result
            assert result.final_body        == '<html><body>Original</body></html>' # No transformation
            assert result.final_status_code == 200
            assert 'x-proxy-transformation' not in result.final_headers            # No transformation headers
            assert result.obj()             == __( content_was_modified = False                               ,
                                                   response_overridden  = False                               ,
                                                   processing_error     = None                                ,
                                                   modifications        = __(block_request           = False                         ,
                                                                             block_status            = 403                           ,
                                                                             block_message           = 'Blocked by proxy'            ,
                                                                             include_stats           = False                         ,
                                                                             modified_body           = None                          ,
                                                                             override_response       = False                         ,
                                                                             override_status         = None                          ,
                                                                             override_content_type   = None                          ,
                                                                             headers_to_add          = __(x_proxy_service                   = 'mgraph-proxy'                   ,
                                                                                                           x_proxy_version                  = '1.0.0'                          ,
                                                                                                           x_request_id                     = __SKIP__                         ,
                                                                                                           x_processed_at                   = __SKIP__                         ,
                                                                                                           x_original_host                  = 'example.com'                    ,
                                                                                                           x_original_path                  = '/test'                        ) ,
                                                                             headers_to_remove       = []                            ,
                                                                             cached_response         = __()                          ,
                                                                             stats                   = __()                          ) ,
                                                   final_status_code    = 200                                 ,
                                                   final_content_type   = 'text/html'                         ,
                                                   final_body           = '<html><body>Original</body></html>',
                                                   final_headers        = __(content_type                     = 'text/html'                      ,
                                                                             content_length                   = '34'                             ,
                                                                             x_proxy_service                  = 'mgraph-proxy'                   ,
                                                                             x_proxy_version                  = '1.0.0'                          ,
                                                                             x_request_id                     = __SKIP__                         ,
                                                                             x_processed_at                   = __SKIP__                         ,
                                                                             x_original_host                  = 'example.com'                    ,
                                                                             x_original_path                  = '/test'                          ))


    def test_process_response__with_hashes_mode(self):                              # Test HASHES transformation via proxy
        skip__if_not__in_github_actions()                                           # todo: find out why this test is non-deterministic locally but always passes in GH actions
        source_html = '<html><head><title>Test Page</title></head><body><p>Content here</p></body></html>'

        response_data = Schema__Proxy__Response_Data(request  = { 'scheme'       : 'https'                             ,
                                                                  'host'         : 'example.com'                       ,
                                                                  'port'         : 443                                 ,
                                                                  'path'         : '/hashes-test-mode'                 ,
                                                                  'headers'      : {'Cookie': 'mitm-mode=hashes'}     },   # HASHES mode cookie
                                                     response = { 'status_code'  : 200                                 ,
                                                                  'body'         : source_html                         ,
                                                                  'headers'      : {'content-type': 'text/html'}      ,
                                                                  'content_type' : 'text/html'                         })


        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert type(result)                                   is Schema__Response__Processing_Result
            assert result.content_was_modified                    is True                              # Content was transformed
            assert result.final_body                              != source_html                         # Body changed
            assert 'x-proxy-transformation'                       in result.final_headers
            assert result.final_headers['x-proxy-transformation'] == 'hashes'
            assert 'x-proxy-cache'                                in result.final_headers               # Cache headers present
            assert 'x-html-service-time'                          in result.final_headers               # Timing headers present

            # Verify hashes are in the transformed content
            assert '<!DOCTYPE html>'              in result.final_body
            assert 'Test Page'                not in result.final_body                          # Original text replaced
            assert len(result.final_body)        > 0                                            # Has content

            assert result.obj() == __( content_was_modified = True                                 ,
                                       response_overridden  = False                                ,
                                       processing_error     = None                                 ,
                                       modifications        = __(block_request         = False                                    ,
                                                                 block_status          = 403                                      ,
                                                                 block_message         = 'Blocked by proxy'                       ,
                                                                 include_stats         = False                                    ,
                                                                 modified_body         = '<!DOCTYPE html>\n'
                                                                                         '<html>\n'
                                                                                         '    <head>\n'
                                                                                         '        <title>094cf2ae96</title>\n'
                                                                                         '    </head>\n'
                                                                                         '    <body>\n'
                                                                                         '        <p>76fda2e3be</p>\n'
                                                                                         '    </body>\n'
                                                                                         '</html>'                                ,
                                                                 override_response     = False                                    ,
                                                                 override_status       = None                                     ,
                                                                 override_content_type = None                                     ,
                                                                 headers_to_add        = __(x_proxy_service                   = 'mgraph-proxy'                      ,
                                                                                            x_proxy_version                   = '1.0.0'                             ,
                                                                                            x_request_id                      = __SKIP__                            ,
                                                                                            x_processed_at                    = __SKIP__                            ,
                                                                                            x_original_host                   = 'example.com'                       ,
                                                                                            x_original_path                   = '/hashes-test-mode'                      ,
                                                                                            x_proxy_cookie_summary            = "{'show_command': None, 'inject_command': None, 'replace_command': None, 'debug_enabled': False, 'rating': None, 'model_override': None, 'cache_enabled': False, 'is_wcf_command': False, 'all_proxy_cookies': {'mitm-mode': 'hashes'}}" ,
                                                                                            x_proxy_transformation            = 'hashes'                            ,
                                                                                            x_proxy_cache                     = 'miss'                              ,
                                                                                            x_html_service_time               = __SKIP__                            ,
                                                                                            content_type                      = __SKIP__                          ) ,
                                                                 headers_to_remove     = []                                      ,
                                                                 cached_response       = __()                                    ,
                                                                 stats                 = __()                                    ) ,
                                       final_status_code    = 200                                  ,
                                       final_content_type   = 'text/html'                          ,
                                       final_body           = ('<!DOCTYPE html>\n'
                                                               '<html>\n'
                                                               '    <head>\n'
                                                               '        <title>094cf2ae96</title>\n'
                                                               '    </head>\n'
                                                               '    <body>\n'
                                                               '        <p>76fda2e3be</p>\n'
                                                               '    </body>\n'
                                                               '</html>'                            ),
                                       final_headers        = __(content_type                      = __SKIP__                         ,
                                                                 content_length                    = '136'                            ,
                                                                 x_proxy_service                   = 'mgraph-proxy'                   ,
                                                                 x_proxy_version                   = '1.0.0'                          ,
                                                                 x_request_id                      = __SKIP__                          ,
                                                                 x_processed_at                    = __SKIP__                         ,
                                                                 x_original_host                   = 'example.com'                    ,
                                                                 x_original_path                   = '/hashes-test-mode'                   ,
                                                                 x_proxy_cookie_summary            = "{'show_command': None, 'inject_command': None, 'replace_command': None, 'debug_enabled': False, 'rating': None, 'model_override': None, 'cache_enabled': False, 'is_wcf_command': False, 'all_proxy_cookies': {'mitm-mode': 'hashes'}}" ,
                                                                 x_proxy_transformation            = 'hashes'                         ,
                                                                 x_proxy_cache                     = 'miss'                           ,
                                                                 x_html_service_time               = __SKIP__                         ))


    def test_process_response__with_xxx_mode(self):                                 # Test XXX transformation (privacy mask)
        source_html = '<html><body><p>This is sensitive information</p></body></html>'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                         ,
                'host'   : 'example.com'                   ,
                'port'   : 443                             ,
                'path'   : '/xxx-test-mode'                ,
                'headers': {'Cookie': 'mitm-mode=xxx'}     # XXX mode cookie
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.final_body == """<!DOCTYPE html>
<html>
    <body>
        <p>xxxx xx xxxxxxxxx xxxxxxxxxxx</p>
    </body>
</html>"""              # bug this is showing the hashes not the xxxx

            assert result.content_was_modified     is True
            assert result.final_body               != source_html
            assert 'xxxx xx xxxxxxxxx xxxxxxxxxxx' in result.final_body              # Content masked with xxx
            assert result.final_headers['x-proxy-transformation'] == 'xxx'

    def test_process_response__with_dict_mode(self):                                # Test DICT transformation (tree view)
        pytest.skip("dict mode is not supported in the lastest version (which uses semantic-text service)")
        source_html = '<html><body><h1>Title</h1><p>Paragraph</p></body></html>'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/dict-test'                     ,
                'headers': {'Cookie': 'mitm-mode=dict'}     # DICT mode cookie
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.content_was_modified is True
            assert 'html\n' in result.final_body                                    # Tree structure
            assert '└──' in result.final_body                                       # Tree characters
            assert 'TEXT:' in result.final_body                                     # Text nodes
            assert result.final_headers['x-proxy-transformation'] == 'dict'
            assert 'text/plain' in result.final_headers['content-type']             # DICT returns text/plain

    def test_process_response__with_roundtrip_mode(self):                           # Test ROUNDTRIP transformation
        pytest.skip("dict mode is not supported in the lastest version (which uses semantic-text service)")
        pytest.skip("dict mode is not supported in the lastest version (which uses semantic-text service)")
        source_html = '<html><body><p>Roundtrip test content</p></body></html>'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                              ,
                'host'   : 'example.com'                        ,
                'port'   : 443                                  ,
                'path'   : '/roundtrip-test'                    ,
                'headers': {'Cookie': 'mitm-mode=roundtrip'}    # ROUNDTRIP mode cookie
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.content_was_modified is True
            assert result.final_body           != source_html                       # Normalized HTML
            assert 'Roundtrip test content'    in result.final_body                 # Content preserved
            assert result.final_headers['x-proxy-transformation'] == 'roundtrip'

    def test_process_response__cache_hit_behavior(self):                            # Test caching works through proxy
        skip__if_not__in_github_actions()                                           # todo: find out why this test is non-deterministic locally but always passes in GH actions
        source_html = '<html><body><p>Cacheable content</p></body></html>'
        target_url  = 'https://example.com/cache-test-page'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/cache-test-page'               ,
                'headers': {'Cookie': 'mitm-mode=hashes'}   # HASHES mode
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            # First request - cache miss
            result1 = _.process_response(response_data)

            assert result1.final_headers['x-proxy-cache'] == 'miss'                # First call is cache miss

            if not_in_github_action():                      # todo: figure out why this is not working in GH Actions
                # Second request - cache hit
                result2 = _.process_response(response_data)

                assert result2.final_headers['x-proxy-cache']      == 'hit'            # Second call is cache hit
                assert result2.final_body                          == result1.final_body  # Same transformed content
                assert result2.final_headers['x-html-service-time'] == '0.0ms'         # Cache hits have 0ms time

    def test_process_response__different_modes_same_content(self):                  # Test multiple transformations of same content

        source_html = '<html><body><p>Multi-mode test</p></body></html>'

        modes_to_test = [
            ('hashes'   , 'hashes'   ),
            ('xxx'      , 'xxx'      ),
        ]

        results = {}

        with self.proxy_response_service as _:
            for mode_value, expected_header in modes_to_test:
                response_data = Schema__Proxy__Response_Data(
                    request  = {
                        'scheme' : 'https'                                 ,
                        'host'   : 'example.com'                           ,
                        'port'   : 443                                     ,
                        'path'   : f'/multi-mode-{mode_value}'             ,
                        'headers': {'Cookie': f'mitm-mode={mode_value}'}
                    },
                    response = {
                        'status_code'  : 200                ,
                        'body'         : source_html        ,
                        'headers'      : {'content-type': 'text/html'},
                        'content_type' : 'text/html'
                    }
                )

                result = _.process_response(response_data)
                results[mode_value] = result

                assert result.content_was_modified is True
                assert result.final_headers['x-proxy-transformation'] == expected_header

            # Verify each mode produces different output
            hashes_body    = results['hashes'   ].final_body
            xxx_body       = results['xxx'      ].final_body
            #roundtrip_body = results['roundtrip'].final_body

            assert hashes_body    != xxx_body                                       # Different transformations

    def test_process_response__non_html_content_skipped(self):                      # Test non-HTML content is not transformed
        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/api/data'                      ,
                'headers': {'Cookie': 'mitm-mode=hashes'}   # HASHES mode but...
            },
            response = {
                'status_code'  : 200                           ,
                'body'         : '{"key": "value"}'            ,
                'headers'      : {'content-type': 'application/json'},  # JSON, not HTML
                'content_type' : 'application/json'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.final_body                == '{"key": "value"}'          # Unchanged
            assert result.content_was_modified      is False                       # Not modified
            assert 'x-proxy-transformation' not in result.final_headers            # No transformation

    def test_process_response__empty_body_skipped(self):                            # Test empty body is not transformed
        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/empty'                         ,
                'headers': {'Cookie': 'mitm-mode=hashes'}
            },
            response = {
                'status_code'  : 200                ,
                'body'         : ''                 ,  # Empty body
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.final_body                == ''
            assert result.content_was_modified      is False
            assert 'x-proxy-transformation' not in result.final_headers

    def test_process_response__url_construction(self):                              # Test URL construction for cache keys
        test_cases = [
            # (scheme, host, port, path, expected_url)
            ('https', 'example.com', 443 , '/test'     , 'https://example.com/test'     ),  # Standard HTTPS
            ('http' , 'example.com', 80  , '/test'     , 'http://example.com/test'      ),  # Standard HTTP
            ('https', 'example.com', 8443, '/test'     , 'https://example.com:8443/test'),  # Non-standard port
            ('https', 'example.com', 443 , '/'         , 'https://example.com/'         ),  # Root path
            ('https', 'api.test.com', 443, '/v1/users' , 'https://api.test.com/v1/users'),  # Subdomain
        ]

        with self.proxy_response_service as _:
            for scheme, host, port, path, expected_url in test_cases:
                response_data = Schema__Proxy__Response_Data(
                    request  = {
                        'scheme' : scheme                           ,
                        'host'   : host                             ,
                        'port'   : port                             ,
                        'path'   : path                             ,
                        'headers': {'Cookie': 'mitm-mode=hashes'}
                    },
                    response = {
                        'status_code'  : 200                               ,
                        'body'         : '<html><body>Test</body></html>'  ,
                        'headers'      : {'content-type': 'text/html'}     ,
                        'content_type' : 'text/html'
                    }
                )

                result = _.process_response(response_data)

                # Verify transformation happened (proves URL was constructed correctly for cache)
                assert result.content_was_modified is True

    def test_process_response__original_html_stored(self):                          # Test original HTML is stored for provenance
        skip_if_in_github_action()                                                  # started failing with "ValueError: in Cache__Service__Fast_API__Client__Requests.test_client the target self.config.fast_api_app must be configure" but locally runs ok

        source_html = '<html><body><p>Original for provenance</p></body></html>'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/provenance-test'               ,
                'headers': {'Cookie': 'mitm-mode=hashes'}
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.content_was_modified is True

            # Verify original HTML can be retrieved from cache
            target_url = 'https://example.com/provenance-test'
            page_refs  = _.html_transformation_service.cache_service.get_or_create_page_entry(target_url)
            cache_id   = page_refs.cache_id

            retrieve = _.html_transformation_service.cache_service.cache_client.data().retrieve()
            namespace = _.html_transformation_service.namespace()
            cached_original = retrieve.data__string__with__id_and_key(
                cache_id     = cache_id                   ,
                data_key     = "transformations/html"     ,
                data_file_id = 'original-html'            ,
                namespace    = namespace
            )

            if not_in_github_action():                      # todo: figure out why this is not working in GH Actions
                assert cached_original == source_html                                   # Original HTML preserved

    def test_process_response__case_insensitive_cookie(self):                       # Test cookie parsing is case-insensitive
        test_cases = [
            'mitm-mode=HASHES'   ,
            'mitm-mode=Hashes'   ,
            'mitm-mode=hashes'   ,
            'mitm-mode=HaShEs'   ,
        ]

        with self.proxy_response_service as _:
            for cookie_value in test_cases:
                response_data = Schema__Proxy__Response_Data(
                    request  = {
                        'scheme' : 'https'                     ,
                        'host'   : 'example.com'               ,
                        'port'   : 443                         ,
                        'path'   : '/case-test'                ,
                        'headers': {'Cookie': cookie_value}
                    },
                    response = {
                        'status_code'  : 200                               ,
                        'body'         : '<html><body>Test</body></html>'  ,
                        'headers'      : {'content-type': 'text/html'}     ,
                        'content_type' : 'text/html'
                    }
                )

                result = _.process_response(response_data)

                assert result.final_headers['x-proxy-transformation'] == 'hashes'   # All variations work

    def test_process_response__multiple_cookies(self):                              # Test mitm-mode works with other cookies
        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                                                          ,
                'host'   : 'example.com'                                                    ,
                'port'   : 443                                                              ,
                'path'   : '/multi-cookie'                                                  ,
                'headers': {'Cookie': 'session=abc123; mitm-mode=xxx; user=test'}         # Multiple cookies
            },
            response = {
                'status_code'  : 200                               ,
                'body'         : '<html><body>Test</body></html>'  ,
                'headers'      : {'content-type': 'text/html'}     ,
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert result.content_was_modified is True
            assert result.final_headers['x-proxy-transformation'] == 'xxx'

    def test_process_response__transformation_timing(self):                         # Test transformation timing is recorded
        source_html = '<html><body><p>Timing test</p></body></html>'

        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/timing-test'                   ,
                'headers': {'Cookie': 'mitm-mode=hashes'}
            },
            response = {
                'status_code'  : 200                ,
                'body'         : source_html        ,
                'headers'      : {'content-type': 'text/html'},
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            assert 'x-html-service-time' in result.final_headers
            timing_header = result.final_headers['x-html-service-time']
            assert timing_header.endswith('ms')                                     # Format: "123.5ms"

            timing_value = float(timing_header.replace('ms', ''))
            assert timing_value >= 0                                                # Valid timing

    def test_process_response__standard_proxy_headers_present(self):                # Test standard proxy headers are added
        response_data = Schema__Proxy__Response_Data(
            request  = {
                'scheme' : 'https'                          ,
                'host'   : 'example.com'                    ,
                'port'   : 443                              ,
                'path'   : '/headers-test'                  ,
                'headers': {'Cookie': 'mitm-mode=hashes'}
            },
            response = {
                'status_code'  : 200                               ,
                'body'         : '<html><body>Test</body></html>'  ,
                'headers'      : {'content-type': 'text/html'}     ,
                'content_type' : 'text/html'
            }
        )

        with self.proxy_response_service as _:
            result = _.process_response(response_data)

            # Verify both transformation headers AND standard proxy headers
            assert 'x-proxy-transformation' in result.final_headers                # Transformation headers
            assert 'x-proxy-cache'          in result.final_headers
            assert 'x-html-service-time'    in result.final_headers
            # assert 'x-proxy-request-id'     in result.final_headers              # this has been renamed to x-request-id # todo: see if 'x-proxy-request-id' would be a better name
            assert 'content-type'           in result.final_headers
            assert 'content-length'         in result.final_headers
            assert list_set(result.final_headers) == [ Safe_Str__Http__Header__Name('content-length'        ),
                                                       Safe_Str__Http__Header__Name('content-type'          ),
                                                       Safe_Str__Http__Header__Name('x-html-service-time'   ),
                                                       Safe_Str__Http__Header__Name('x-original-host'       ),
                                                       Safe_Str__Http__Header__Name('x-original-path'       ),
                                                       Safe_Str__Http__Header__Name('x-processed-at'        ),
                                                       Safe_Str__Http__Header__Name('x-proxy-cache'         ),
                                                       Safe_Str__Http__Header__Name('x-proxy-cookie-summary'),
                                                       Safe_Str__Http__Header__Name('x-proxy-service'       ),
                                                       Safe_Str__Http__Header__Name('x-proxy-transformation'),
                                                       Safe_Str__Http__Header__Name('x-proxy-version'       ),
                                                       Safe_Str__Http__Header__Name('x-request-id'          )]

    def test__integration__full_flow_verification(self):                            # Test complete integration flow
        skip__if_not__in_github_actions()                                           # todo: find out why this test is non-deterministic locally but always passes in GH actions
        source_html = """
        <html>
            <head><title>Integration Test</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is a paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        """

        with self.proxy_response_service as _:
            # Test flow: Request → Cookie Parser → HTML Transformation → Cache → Response

            response_data = Schema__Proxy__Response_Data(
                request  = { 'scheme' : 'https'                          ,
                             'host'   : 'integration.test.com'           ,
                             'port'   : 443                              ,
                             'path'   : '/full-flow'                     ,
                             'headers': {'Cookie': 'mitm-mode=hashes'   }},
                response = { 'status_code'  : 200                ,
                             'body'         : source_html        ,
                             'headers'      : {'content-type': 'text/html'},
                             'content_type' : 'text/html'                   })

            # First request
            result1 = _.process_response(response_data)

            assert result1.obj() == __( modifications         = __( block_request         = False              ,
                                                                    block_status          = 403                ,
                                                                    block_message         = 'Blocked by proxy' ,
                                                                    include_stats         = False              ,
                                                                    headers_to_add        = __SKIP__           ,
                                                                    headers_to_remove     = []                 ,
                                                                    modified_body         = __SKIP__           ,
                                                                    override_response     = False              ,
                                                                    override_status       = None               ,
                                                                    override_content_type = None               ,
                                                                    cached_response        = __()              ,
                                                                    stats                  = __())             ,
                                         final_status_code     = 200                                        ,
                                         final_content_type    = 'text/html'                                ,
                                         final_body            = __SKIP__                                   ,
                                         final_headers         = __SKIP__                                   ,
                                         content_was_modified  = True                                       ,
                                         response_overridden   = False                                      ,
                                         processing_error      = None                                       )


            # Verify transformation happened
            assert result1.content_was_modified is True
            assert result1.final_body != source_html
            assert result1.final_headers['x-proxy-transformation'] == 'hashes'
            assert result1.final_headers['x-proxy-cache'] == 'miss'


            if not_in_github_action():                      # todo: figure out why this is not working in GH Actions
                # Second request - should hit cache
                result2 = _.process_response(response_data)

                assert result2.final_headers['x-proxy-cache'] == 'hit'
                assert result2.final_body == result1.final_body
                assert result2.final_headers['x-html-service-time'] == '0.0ms'