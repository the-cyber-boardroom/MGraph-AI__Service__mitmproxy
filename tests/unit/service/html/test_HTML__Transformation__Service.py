from unittest                                                                       import TestCase

from mgraph_ai_service_cache_client.client.cache_service.register_cache_service import register_cache_service__in_memory
from osbot_utils.helpers.duration.decorators.print_duration                         import print_duration
from osbot_utils.testing.Pytest import skip_if_in_github_action
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html           import Safe_Str__Html
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__Dict               import Type_Safe__Dict
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Transformation__Step_1  import Schema__HTML__Transformation__Step_1
from mgraph_ai_service_mitmproxy.schemas.html.safe_dict.Safe_Dict__Hash__To__Text   import Safe_Dict__Hash__To__Text
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                import Proxy__Cache__Service
from osbot_utils.testing.__                                                         import __, __SKIP__, __LESS_THAN__
from osbot_utils.testing.Temp_Env_Vars                                              import Temp_Env_Vars
from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.utils.Http                                                         import GET_json
from osbot_utils.utils.Objects                                                      import base_classes
from mgraph_ai_service_mitmproxy.service.html.HTML__Transformation__Service         import HTML__Transformation__Service
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode       import Enum__HTML__Transformation_Mode
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Transformation__Result  import Schema__HTML__Transformation__Result
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs                              import (get__cache_service__fast_api_server,
                                                                                           get__html_service__fast_api_server,
                                                                                           get__semantic_text_service__fast_api_server)


class test_HTML__Transformation__Service(TestCase):

    @classmethod
    def setUpClass(cls):                                                            # ONE-TIME setup: start all services
        with print_duration(action_name='start 3 FastAPI servers'):

            register_cache_service__in_memory()                         # todo: add in memory cache support to the other services (used below)

            with get__html_service__fast_api_server() as _:
                cls.html_service_server   = _.fast_api_server
                cls.html_service_base_url = _.server_url

            # with get__cache_service__fast_api_server() as _:
            #     cls.cache_service_server   = _.fast_api_server
            #     cls.cache_service_base_url = _.server_url

            with get__semantic_text_service__fast_api_server() as _:              # NEW: Semantic Text Service
                cls.semantic_text_service_server   = _.fast_api_server
                cls.semantic_text_service_base_url = _.server_url

            cls.html_service_server.start()                                         # Start all servers
            #cls.cache_service_server.start()
            cls.semantic_text_service_server.start()

            env_vars = { 'AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL'         : cls.html_service_base_url          ,
                         #'AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL'        : cls.cache_service_base_url         ,
                         'AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL': cls.semantic_text_service_base_url }
            cls.temp_env_vars = Temp_Env_Vars(env_vars=env_vars).set_vars()
            cls.html_transformation_service = HTML__Transformation__Service().setup()

    @classmethod
    def tearDownClass(cls):                                                         # Stop all servers
        cls.html_service_server.stop()
        #cls.cache_service_server.stop()
        cls.semantic_text_service_server.stop()                                     # NEW
        cls.temp_env_vars.restore_vars()

    def test__fast_api__servers(self):                                              # Verify all servers running
        assert GET_json(self.html_service_base_url          + '/info/health') == {'status': 'ok'}
        #assert GET_json(self.cache_service_base_url         + '/info/health') == {'status': 'ok'}
        assert GET_json(self.semantic_text_service_base_url + '/info/health') == {'status': 'ok'}  # NEW

        with self.html_transformation_service as _:
            assert type(_                      ) is HTML__Transformation__Service
            assert type(_.cache_service        ) is Proxy__Cache__Service
            assert _.semantic_text_client       is not None                         # NEW

        #assert self.html_service_server.port != self.cache_service_server        .port      # make sure all ports are different
        assert self.html_service_server.port != self.semantic_text_service_server.port


    def test__init__(self):                                                         # Test auto-initialization
        with HTML__Transformation__Service() as _:
            assert type(_)                  is HTML__Transformation__Service
            assert base_classes(_)          == [Type_Safe, object]
            assert _.html_service_client    is None
            assert _.semantic_text_client   is None                                 # NEW
            assert _.cache_service          is None

    def test_setup(self):                                                           # Test setup method with real services
        with self.html_transformation_service as _:
            assert _.html_service_client                        is not None
            assert _.semantic_text_client                       is not None         # NEW
            assert _.cache_service                              is not None
            assert _.html_service_client.base_url               == self.html_service_base_url
            assert _.semantic_text_client.server_base_url()     == self.semantic_text_service_base_url  # NEW
            #assert _.cache_service.cache_config.base_url        == self.cache_service_base_url
            #assert _.cache_service.cache_client.config.base_url == self.cache_service_base_url

    def test_transform_html__mode_off(self):                                        # Test transformation with OFF mode (passthrough)
        with HTML__Transformation__Service() as _:
            source_html = "<html><body>Original</body></html>"

            result = _.transform_html(
                source_html = source_html,
                target_url  = "https://example.com",
                mode        = Enum__HTML__Transformation_Mode.OFF
            )

            assert type(result)                  is Schema__HTML__Transformation__Result
            assert result.transformed_html       == source_html                     # Unchanged
            assert result.transformation_mode    == Enum__HTML__Transformation_Mode.OFF
            assert result.cache_hit              is False
            assert result.transformation_time_ms == 0.0
            assert result.obj()                  == __(
                transformed_html       = '<html><body>Original</body></html>',
                transformation_mode    = 'off',
                content_type           = 'text/html',
                cache_hit              = False,
                transformation_time_ms = 0.0
            )

    def test_transform_html__mode_xxx__with_semantic_text_service(self):            # NEW: Test XXX transformation via semantic-text
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Test content</p></body></html>"

            result = _.transform_html(source_html = source_html,
                                      target_url  = "https://example.com/xxx-test",
                                      mode        = Enum__HTML__Transformation_Mode.XXX)

            assert type(result)               is Schema__HTML__Transformation__Result

            assert result.transformed_html    != source_html                        # Should be transformed
            assert result.transformation_mode == Enum__HTML__Transformation_Mode.XXX
            assert result.content_type        == "text/html"
            assert "xxx" in result.transformed_html.lower()                         # Should contain masked text

            assert result.obj() == __(transformed_html        = '<!DOCTYPE html>\n'
                                                                '<html>\n'
                                                                '    <body>\n'
                                                                '        <p>xxxx xxxxxxx</p>\n'
                                                                '    </body>\n'
                                                                '</html>',
                                       transformation_mode    = 'xxx',
                                       content_type           = 'text/html',
                                       cache_hit              = False,
                                       transformation_time_ms = __LESS_THAN__(100))     # should execute fast (locally in dev laptop this is ~10ms)

    def test_transform_html__mode_hashes__with_semantic_text_service(self):         # NEW: Test HASHES transformation
        with self.html_transformation_service as _:
            source_html = """<!DOCTYPE html>
<html>
    <body>
        <nav>
            <ul>
                <li>
                    <a href="/">Home</a>
                </li>
                <li>
                    <a href="/about">About</a>
                </li>
            </ul>
        </nav>
        <main>
            <article>
                <h1>Welcome</h1>
                <p>This is <strong>bold</strong> and <em>italic</em> text.</p>
            </article>
        </main>
    </body>
</html>"""

            result = _.transform_html(
                source_html = source_html,
                target_url  = "https://example.com/hashes-test",
                mode        = Enum__HTML__Transformation_Mode.HASHES
            )

            assert type(result)               is Schema__HTML__Transformation__Result
            assert result.transformation_mode == Enum__HTML__Transformation_Mode.HASHES
            assert result.transformed_html    != source_html

            # Verify structure is preserved (HTML tags intact)
            assert "<html>" in result.transformed_html
            assert "<body>" in result.transformed_html
            assert "<nav>" in result.transformed_html
            assert "<h1>" in result.transformed_html

            assert result.obj() == __(transformed_html           = '<!DOCTYPE html>\n'
                                                                    '<html>\n'
                                                                    '    <body>\n'
                                                                    '        <nav>\n'
                                                                    '            <ul>\n'
                                                                    '                <li>\n'
                                                                    '                    <a href="/">8cf04a9734</a>\n'
                                                                    '                </li>\n'
                                                                    '                <li>\n'
                                                                    '                    <a href="/about">8f7f4c1ce7</a>\n'
                                                                    '                </li>\n'
                                                                    '            </ul>\n'
                                                                    '        </nav>\n'
                                                                    '        <main>\n'
                                                                    '            <article>\n'
                                                                    '                <h1>83218ac34c</h1>\n'
                                                                    '                '
                                                                    '<p>8b50059a92<strong>69dcab4a73</strong>0060636b44<em>030c5b6d1e</em>2d99d326cd</p>\n'
                                                                    '            </article>\n'
                                                                    '        </main>\n'
                                                                    '    </body>\n'
                                                                    '</html>'                     ,
                                          transformation_mode    = 'hashes'                 ,
                                          content_type           = 'text/html'              ,
                                          cache_hit              = False                    ,
                                          transformation_time_ms = __LESS_THAN__(100)     )


    def test_transform_html__caching__with_semantic_text(self):                     # NEW: Test caching with semantic-text transformations
        skip_if_in_github_action()                                                  # not working in GH action due to lack of credentials to access cache service
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Cache test</p></body></html>"
            target_url  = "https://example.com/cache-test"
            mode        = Enum__HTML__Transformation_Mode.XXX

            result_1 = _.transform_html(                                            # First call - cache MISS
                source_html = source_html,
                target_url  = target_url,
                mode        = mode
            )

            result_2 = _.transform_html(                                            # Second call - cache HIT
                source_html = source_html,
                target_url  = target_url,
                mode        = mode
            )

            assert result_1.cache_hit               is False                                      # First call misses
            assert result_2.cache_hit               is True                                       # Second call hits
            assert result_1.transformed_html        == result_2.transformed_html           # Same output
            assert result_2.transformation_time_ms  == 0.0                           # Cache hit has no transformation time
            assert result_1.obj()                   == __(transformed_html='<!DOCTYPE html>\n'
                                                                            '<html>\n'
                                                                            '    <body>\n'
                                                                            '        <p>xxxxx xxxx</p>\n'
                                                                            '    </body>\n'
                                                                            '</html>',
                                                           transformation_mode='xxx',
                                                           content_type='text/html',
                                                           cache_hit=False,
                                                           transformation_time_ms=__SKIP__)
            assert result_1.obj().diff(result_2.obj()) == __(cache_hit              = __(actual=False   , expected=True),
                                                             transformation_time_ms = __(actual=__SKIP__, expected=0.0 ))


    def test__step_1__get_hash_mapping(self):                                       # NEW: Test Step 1 (HTML → Hash Mapping)
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Test content!</p></body></html>"

            html_transformation__step_1 = _._step_1__get_hash_mapping(source_html)

            with html_transformation__step_1 as _:
                assert type(_) is Schema__HTML__Transformation__Step_1
                assert _.obj() == __(html_dict=__(tag='html',
                                                  attrs=__(),
                                                  nodes=[__(tag='body',
                                                            attrs=__(),
                                                            nodes=[__(tag='p',
                                                                      attrs=__(),
                                                                      nodes=[__(type='TEXT',
                                                                                data='9b68eca2b0')])])]),
                                     hash_mapping=__(_9b68eca2b0='Test content!'))


    def test__step_2__transform_mapping(self):                                      # NEW: Test Step 2 (Transform via Semantic Text)
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Test content</p></body></html>"

            html_transformation__step_1 = _._step_1__get_hash_mapping(source_html)
            hash_mapping                = html_transformation__step_1.hash_mapping
            transformed_mapping         = _._step_2__transform_mapping(hash_mapping = hash_mapping                       ,
                                                                       mode         = Enum__HTML__Transformation_Mode.XXX)

            assert type(transformed_mapping) is Safe_Dict__Hash__To__Text
            assert len(transformed_mapping) == len(hash_mapping)                    # Same keys

            # Verify transformation occurred
            for hash_key in hash_mapping.keys():
                assert hash_key in transformed_mapping                              # Same keys preserved
                # Values should be different (transformed)
                if hash_mapping[hash_key].strip():                                  # Only check non-empty text
                    assert transformed_mapping[hash_key] != hash_mapping[hash_key]

            assert transformed_mapping.obj() == __(_8bfa8e0684='xxxx xxxxxxx')

    def test__step_3__reconstruct_html(self):                                       # NEW: Test Step 3 (Hash Mapping → HTML)
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Test content</p></body></html>"

            html_transformation__step_1 = _._step_1__get_hash_mapping(source_html)
            hash_mapping                = html_transformation__step_1.hash_mapping
            html_dict                   = html_transformation__step_1.html_dict

            reconstructed_html = _._step_3__reconstruct_html(html_dict          = html_dict,
                                                             transformed_mapping = hash_mapping)                                  # Use original mapping (should roundtrip)


            assert type(reconstructed_html) is Safe_Str__Html
            assert len(reconstructed_html)  > 0
            assert "<html>" in reconstructed_html.lower()
            assert "<body>" in reconstructed_html.lower()
            assert "<p>"    in reconstructed_html.lower()
            assert reconstructed_html == """\
<!DOCTYPE html>
<html>
    <body>
        <p>Test content</p>
    </body>
</html>"""

    def test__bug__transform_html__multiple_modes__with_semantic_text(self):              # Test multiple transformation modes
        with self.html_transformation_service as _:
            source_html = "<html><body><p>Test content for modes</p></body></html>"

            modes_to_test = [
                Enum__HTML__Transformation_Mode.XXX           ,                     # Semantic-text modes
                Enum__HTML__Transformation_Mode.HASHES        ,
                Enum__HTML__Transformation_Mode.ABCDE_BY_SIZE ,
            ]

            results = Type_Safe__Dict(
                expected_key_type   = Enum__HTML__Transformation_Mode,
                expected_value_type = Schema__HTML__Transformation__Result
            )

            for mode in modes_to_test:
                result = _.transform_html(
                    source_html = source_html,
                    target_url  = f"https://example.com/mode-{mode.value}",
                    mode        = mode
                )

                results[mode] = result
                assert result.transformation_mode == mode                           # Correct mode
                assert result.transformed_html    != ""                             # Has content

            # Verify different modes produce different results
            xxx_result       = results[Enum__HTML__Transformation_Mode.XXX           ].transformed_html
            hashes_result    = results[Enum__HTML__Transformation_Mode.HASHES        ].transformed_html
            abcde_result      = results[Enum__HTML__Transformation_Mode.ABCDE_BY_SIZE].transformed_html

            assert xxx_result       != hashes_result                                # Different transformations
            #assert xxx_result       != abcde_result                                # todo: look into this (shouldn't they be different?)
            assert hashes_result    != abcde_result
