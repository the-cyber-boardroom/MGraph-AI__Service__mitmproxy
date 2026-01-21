# ═══════════════════════════════════════════════════════════════════════════════
# HTML Graph Service Client Test Objects
# Sets up in-memory HTML Graph service for integration testing without mocks
# ═══════════════════════════════════════════════════════════════════════════════

from fastapi                                                                        import FastAPI
from mgraph_ai_service_cache_client.schemas.consts.consts__Cache_Client             import ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE
from mgraph_ai_service_html_graph.fast_api.Html_Graph__Service__Fast_API            import Html_Graph__Service__Fast_API
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API__Config                import Serverless__Fast_API__Config
from starlette.testclient                                                           import TestClient
from osbot_utils.type_safe.Type_Safe                                                import Type_Safe
from osbot_utils.type_safe.primitives.domains.identifiers.Random_Guid               import Random_Guid
from osbot_utils.utils.Env                                                          import set_env, load_dotenv, get_env, unload_dotenv
from osbot_fast_api.api.Fast_API                                                    import (ENV_VAR__FAST_API__AUTH__API_KEY__NAME ,
                                                                                            ENV_VAR__FAST_API__AUTH__API_KEY__VALUE)


TEST_API_KEY__NAME  = 'key-used-in-pytest'
TEST_API_KEY__VALUE = Random_Guid()


class Html_Graph__Client__Test_Objs(Type_Safe):                                     # Test objects for HTML Graph client testing
    fast_api         : Html_Graph__Service__Fast_API    = None                      # In-memory FastAPI service
    fast_api__app    : FastAPI                          = None                      # FastAPI application instance
    fast_api__client : TestClient                       = None                      # Test client for requests
    setup_completed  : bool                             = False                     # Setup state flag


html_graph_client_test_objs = Html_Graph__Client__Test_Objs()                       # Singleton test objects


def setup__html_graph_client__test_objs() -> Html_Graph__Client__Test_Objs:         # Initialize test objects
    with html_graph_client_test_objs as _:
        if _.setup_completed is False:
            service_config     = Serverless__Fast_API__Config(enable_api_key=False)
            _.fast_api         = Html_Graph__Service__Fast_API(config=service_config).setup()
            _.fast_api__app    = _.fast_api.app()
            _.fast_api__client = _.fast_api.client()
            _.setup_completed  = True

            set_env(ENV_VAR__FAST_API__AUTH__API_KEY__NAME , TEST_API_KEY__NAME )
            set_env(ENV_VAR__FAST_API__AUTH__API_KEY__VALUE, TEST_API_KEY__VALUE)

    return html_graph_client_test_objs

def load_local_dotenv(dot_env_file):
    load_dotenv(dotenv_path=dot_env_file, override=True)
    if get_env(ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE):
        return True
    else:
        return False

def unload_local_dotenv(dot_env_file):
    unload_dotenv(dotenv_path=dot_env_file)
    if get_env(ENV_VAR__URL__TARGET_SERVER__CACHE_SERVICE):
        return False
    else:
        return True
