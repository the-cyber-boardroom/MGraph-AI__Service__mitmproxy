from unittest                                import TestCase

from mgraph_ai_service_base.utils.Version import version__mgraph_ai_service_base
from tests.unit.Service__Fast_API__Test_Objs import setup__service_fast_api_test_objs, TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__Info__client(TestCase):
    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

    def test__info_version(self):
        response = self.client.get('/info/version')
        assert response.status_code == 200
        assert response.json()      == {'version': version__mgraph_ai_service_base}

    def test__info_status(self):
        response = self.client.get('/info/status')
        result = response.json()
        assert response.status_code == 200
        assert result['service']    == 'mgraph-ai-service-core'
        assert result['status']     == 'operational'
        assert 'timestamp'          in result