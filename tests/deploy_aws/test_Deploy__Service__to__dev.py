from unittest                                    import TestCase
# from osbot_utils.utils.Dev                       import pprint
# from osbot_utils.utils.Env                       import load_dotenv
# from osbot_utils.utils.Files                     import path_combine, file_exists

from tests.deploy_aws.test_Deploy__Service__base import test_Deploy__Service__base

class test_Deploy__Service__to__dev(test_Deploy__Service__base, TestCase):
    stage = 'dev'

    # @classmethod
    # def setUpClass(cls):
    #     dot_env_file = path_combine(__file__, "../.deploy.env")
    #     assert file_exists(dot_env_file)
    #     load_dotenv(dotenv_path=dot_env_file)
    #     super().setUpClass()
    #
    # def test_2__upload_dependencies(self):
    #     upload_results = self.deploy_fast_api.upload_lambda_dependencies_to_s3()
    #     pprint(upload_results)