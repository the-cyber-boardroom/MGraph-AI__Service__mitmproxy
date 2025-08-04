from unittest                                              import TestCase
from mgraph_ai_service_base.service.info.Info__Service     import Info__Service


class test_Info__Service(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info_service = Info__Service()

    def test___init__(self):
        with self.info_service as _:
            assert type(_) == Info__Service

    def test_get_status(self):
        with self.info_service as _:
            result = _.get_status()
            assert result['service'] == 'mgraph-ai-service-base'
            assert result['status']  == 'operational'
            assert 'version'   in result
            assert 'timestamp' in result
            assert 'environment' in result