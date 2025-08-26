from unittest                                                               import TestCase
from osbot_fast_api.api.routes.Fast_API__Routes                             import Fast_API__Routes
from osbot_utils.type_safe.Type_Safe                                        import Type_Safe
from osbot_utils.utils.Misc                                                 import list_set
from osbot_utils.utils.Objects                                              import base_classes
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Info                    import Routes__Info
from mgraph_ai_service_mitmproxy.service.info.schemas.Schema__Server__Versions   import Schema__Server__Versions
from mgraph_ai_service_mitmproxy.utils.Version                                   import version__mgraph_ai_service_mitmproxy


class test_Routes__Info(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.routes_info = Routes__Info()

    def test_setUpClass(self):
        with self.routes_info as _:
            assert type(_)         == Routes__Info
            assert base_classes(_) == [Fast_API__Routes, Type_Safe, object]

    def test_versions(self):
        with self.routes_info.versions() as _:
            assert type(_) is Schema__Server__Versions
            assert list_set(_) == [ 'mgraph_ai_service_mitmproxy'   ,
                                    'osbot_aws'                ,
                                    'osbot_fast_api'           ,
                                    'osbot_fast_api_serverless',
                                    'osbot_utils'              ]
            assert _.mgraph_ai_service_mitmproxy == version__mgraph_ai_service_mitmproxy
