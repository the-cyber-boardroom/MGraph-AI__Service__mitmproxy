from unittest                                import TestCase
from tests.unit.Service__Fast_API__Test_Objs import TEST_API_KEY__NAME, TEST_API_KEY__VALUE, setup__service_fast_api_test_objs


class test_Routes__Health__client(TestCase):
    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

    def test__health(self):
        result = self.client.get('/health/status')
        assert result.status_code == 200
        assert result.json() == {"status": "healthy", "service": "mgraph_ai_service_base"}

    def test__health_detailed(self):
        result = self.client.get('/health/details')
        assert result.status_code == 200
        response = result.json()
        assert response['status']  == "healthy"
        assert response['service'] == "mgraph_ai_service_base"