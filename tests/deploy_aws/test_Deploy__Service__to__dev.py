import pytest
from unittest                                                           import TestCase
from osbot_utils.utils.Misc                                             import list_set
from osbot_fast_api_serverless.deploy.Deploy__Serverless__Fast_API      import DEFAULT__ERROR_MESSAGE__WHEN_FAST_API_IS_OK
from mgraph_ai_service_base.config                                      import LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS
from mgraph_ai_service_base.utils.Version                               import version__mgraph_ai_service_base
from mgraph_ai_service_base.utils.deploy.Deploy__Service                import Deploy__Service


class test_Deploy__Service__to__dev(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.deploy_fast_api__dev = Deploy__Service(stage='dev')

        with cls.deploy_fast_api__dev as _:
            if _.aws_config.aws_configured() is False:
                pytest.skip("this test needs valid AWS credentials")

    def test_1__check_stages(self):
        assert self.deploy_fast_api__dev.stage == 'dev'

    def test_2__upload_dependencies(self):
        upload_results = self.deploy_fast_api__dev.upload_lambda_dependencies_to_s3()
        assert list_set(upload_results) == LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS

    def test_3__create(self):
        assert self.deploy_fast_api__dev.create() is True

    def test_4__invoke(self):
        assert self.deploy_fast_api__dev.invoke().get('errorMessage') == DEFAULT__ERROR_MESSAGE__WHEN_FAST_API_IS_OK

    def test_5__invoke__function_url(self):
        version = {'version': version__mgraph_ai_service_base}
        assert self.deploy_fast_api__dev.invoke__function_url('/info/version') == version

    # def test_6__delete(self):
    #     assert self.deploy_fast_api__dev.delete() is True
