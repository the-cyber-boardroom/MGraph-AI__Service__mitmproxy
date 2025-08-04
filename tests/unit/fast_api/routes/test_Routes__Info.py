from unittest                                              import TestCase
from osbot_fast_api.api.Fast_API_Routes                    import Fast_API_Routes
from osbot_utils.type_safe.Type_Safe                       import Type_Safe
from osbot_utils.utils.Objects                             import base_classes
from mgraph_ai_service_base.fast_api.routes.Routes__Info   import Routes__Info
from mgraph_ai_service_base.utils.Version                  import version__mgraph_ai_service_base


class test_Routes__Info(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.routes_info = Routes__Info()

    def test_setUpClass(self):
        with self.routes_info as _:
            assert type(_)         == Routes__Info
            assert base_classes(_) == [Fast_API_Routes, Type_Safe, object]

    def test_version(self):
        with self.routes_info as _:
            result = _.version()
            assert 'version' in result
            assert result['version'] == version__mgraph_ai_service_base
