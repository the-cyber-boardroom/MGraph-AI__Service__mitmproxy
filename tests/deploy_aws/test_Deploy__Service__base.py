import pytest
from osbot_utils.utils.Env import in_github_action, load_dotenv
from osbot_utils.utils.Misc                                         import list_set
from osbot_fast_api_serverless.deploy.Deploy__Serverless__Fast_API  import DEFAULT__ERROR_MESSAGE__WHEN_FAST_API_IS_OK
from mgraph_ai_service_mitmproxy.config                             import LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS
from mgraph_ai_service_mitmproxy.utils.deploy.Deploy__Service       import Deploy__Service


class test_Deploy__Service__base():     # Base class for deployment tests - override stage in subclasses

    stage: str = None  # Must be set by subclass

    @classmethod
    def setUpClass(cls):
        if cls.stage is None:
            pytest.skip("Can't run when 'stage' class variable is not set")

        cls.deploy_fast_api = Deploy__Service(stage=cls.stage)

        with cls.deploy_fast_api as _:
            if _.aws_config.aws_configured() is False:
                pytest.skip("this test needs valid AWS credentials")

    def test_1__check_stages(self):
        assert self.deploy_fast_api.stage == self.stage

    def test_2__upload_dependencies(self):
        upload_results = self.deploy_fast_api.upload_lambda_dependencies_to_s3()
        assert list_set(upload_results) == sorted(LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS)

    def test_3__create(self):
        assert self.deploy_fast_api.create() is True
        self.test_3_1__update_lambda_runtime__to_3_13()             # todo: add support to OSBot_AWS lambda deploy methods for configuring the version of the python runtime

    def test_3_1__update_lambda_runtime__to_3_13(self):
        self.deploy_fast_api.lambda_function().configuration_update(Runtime='python3.13')
        self.deploy_fast_api.lambda_function().wait_for_function_update_to_complete()

    def test_4__invoke(self):
        assert self.deploy_fast_api.invoke().get('errorMessage') == DEFAULT__ERROR_MESSAGE__WHEN_FAST_API_IS_OK

    def test_5__invoke__function_url(self):
        if in_github_action():
            pytest.skip("this check is not working on GitHub Actions (auth tokens are not correctly set)") # todo: figure out why they are not test
        with self.deploy_fast_api as _:
            if _.api_key__name() and _.api_key__value():
                #version = {'version': version__mgraph_ai_service_mitmproxy}
                assert self.deploy_fast_api.invoke__function_url('/info/health') == {'status': 'ok'}
            else:
                pytest.skip("Can't invoke function_url, since no Auth info was found")

    # def test_6__delete(self):
    #     assert self.deploy_fast_api.delete() is True









