from unittest                                                         import TestCase
from fastapi                                                          import FastAPI
from osbot_fast_api.api.Fast_API                                      import ENV_VAR__FAST_API__AUTH__API_KEY__NAME, ENV_VAR__FAST_API__AUTH__API_KEY__VALUE
from osbot_local_stack.local_stack.Local_Stack                        import Local_Stack
from osbot_utils.utils.Env                                            import get_env
from starlette.testclient                                             import TestClient
from osbot_fast_api_serverless.utils.testing.skip_tests               import skip__if_not__in_github_actions
from mgraph_ai_service_mitmproxy.fast_api.Service__Fast_API                import Service__Fast_API
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Info              import ROUTES_PATHS__INFO, ROUTES_INFO__HEALTH__RETURN_VALUE
from tests.unit.Service__Fast_API__Test_Objs                          import setup__service_fast_api_test_objs, Service__Fast_API__Test_Objs, TEST_API_KEY__NAME


class test_Service__Fast_API__client(TestCase):

    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.service_fast_api_test_objs         = _
            cls.fast_api                           = cls.service_fast_api_test_objs.fast_api
            cls.client                             = cls.service_fast_api_test_objs.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = ''

    def test__init__(self):
        with self.service_fast_api_test_objs as _:
            assert type(_)                  is Service__Fast_API__Test_Objs
            assert type(_.fast_api        ) is Service__Fast_API
            assert type(_.fast_api__app   ) is FastAPI
            assert type(_.fast_api__client) is TestClient
            assert type(_.local_stack     ) is Local_Stack
            assert self.fast_api            == _.fast_api
            assert self.client              == _.fast_api__client

    def test__client__auth(self):
        path                = '/info/health'
        auth_key_name       = get_env(ENV_VAR__FAST_API__AUTH__API_KEY__NAME )
        auth_key_value      = get_env(ENV_VAR__FAST_API__AUTH__API_KEY__VALUE)
        headers             = {auth_key_name: auth_key_value}

        response__no_auth   = self.client.get(url=path, headers={})
        response__with_auth = self.client.get(url=path, headers=headers)

        assert response__no_auth.status_code == 401
        assert response__no_auth.json()      == { 'data'   : None,
                                                  'error'  : None,
                                                  'message': 'Client API key is missing, you need to set it on a header or cookie',
                                                  'status' : 'error'}

        assert auth_key_name                 is not None
        assert auth_key_value                is not None
        assert response__with_auth.json()    == ROUTES_INFO__HEALTH__RETURN_VALUE

    def test__check_if_local_stack_is_setup(self):
        skip__if_not__in_github_actions()
        with self.service_fast_api_test_objs.local_stack as _:
            assert _.is_local_stack_configured_and_available() is True

    def test__config_fast_api_routes(self):
        assert self.fast_api.routes_paths() == sorted(ROUTES_PATHS__INFO)