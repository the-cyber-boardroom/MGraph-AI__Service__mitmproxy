from unittest                                                import TestCase
from osbot_fast_api.api.Fast_API_Routes                      import Fast_API_Routes
from osbot_utils.type_safe.Type_Safe                         import Type_Safe
from osbot_utils.utils.Objects                               import base_classes
from mgraph_ai_service_base.fast_api.routes.Routes__Health   import Routes__Health


class test_Routes__Health(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.routes_health = Routes__Health()

    def test_setUpClass(self):
        with self.routes_health as _:
            assert type(_)         == Routes__Health
            assert base_classes(_) == [Fast_API_Routes, Type_Safe, object]

    def test_health(self):
        with self.routes_health as _:
            response = _.status()
            assert response == {"status": "healthy", "service": "mgraph-ai-service-base"}

    def test_health_detailed(self):
        with self.routes_health as _:
            response = _.details()
            assert response['status']  == "healthy"
            assert response['service'] == "mgraph-ai-service-base"
            assert 'components' in response
            assert 'timestamp'  in response
