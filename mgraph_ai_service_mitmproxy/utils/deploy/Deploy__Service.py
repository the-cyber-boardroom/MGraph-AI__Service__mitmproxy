import mgraph_ai_service_mitmproxy__admin_ui
import mgraph_ai_service_mitmproxy__console
from osbot_utils.utils.Env                                          import get_env
from osbot_fast_api_serverless.deploy.Deploy__Serverless__Fast_API  import Deploy__Serverless__Fast_API
from mgraph_ai_service_mitmproxy.config                             import SERVICE_NAME, LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS
from mgraph_ai_service_mitmproxy.fast_api.lambda_handler            import run

class Deploy__Service(Deploy__Serverless__Fast_API):

    def deploy_lambda(self):
        with super().deploy_lambda() as _:
            # Add any service-specific environment variables here
            # Example: _.set_env_variable('BASE_API_KEY', get_env('BASE_API_KEY'))
            # _.set_env_variable('AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL' , get_env('AUTH__TARGET_SERVER__CACHE_SERVICE__BASE_URL' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME' , get_env('AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_NAME' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE', get_env('AUTH__TARGET_SERVER__CACHE_SERVICE__KEY_VALUE' ))
            #
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL'  , get_env('AUTH__TARGET_SERVER__HTML_SERVICE__BASE_URL'  ))
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_SERVICE__KEY_NAME'  , get_env('AUTH__TARGET_SERVER__HTML_SERVICE__KEY_NAME'  ))
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_SERVICE__KEY_VALUE' , get_env('AUTH__TARGET_SERVER__HTML_SERVICE__KEY_VALUE' ))
            #
            # _.set_env_variable('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL'  , get_env('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__BASE_URL' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_NAME'  , get_env('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_NAME' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_VALUE' , get_env('AUTH__TARGET_SERVER__SEMANTIC_TEXT_SERVICE__KEY_VALUE' ))
            #
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__BASE_URL'  , get_env('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__BASE_URL' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__KEY_NAME'  , get_env('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__KEY_NAME' ))
            # _.set_env_variable('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__KEY_VALUE' , get_env('AUTH__TARGET_SERVER__HTML_GRAPH_SERVICE__KEY_VALUE' ))

            # todo: add the AWS Comprehend vars here
            # _.set_env_variable('WCF_SERVICE__AUTH__API_KEY__NAME'             , get_env('WCF_SERVICE__AUTH__API_KEY__NAME'  ))
            # _.set_env_variable('WCF_SERVICE__AUTH__API_KEY__VALUE'            , get_env('WCF_SERVICE__AUTH__API_KEY__VALUE' ))

            _.set_env_variable('AUTH__SERVICE__AWS__COMPREHEND__BASE_URL'            , get_env('AUTH__SERVICE__AWS__COMPREHEND__BASE_URL'  ))
            _.set_env_variable('AUTH__SERVICE__AWS__COMPREHEND__KEY_NAME'            , get_env('AUTH__SERVICE__AWS__COMPREHEND__KEY_NAME' ))
            _.set_env_variable('AUTH__SERVICE__AWS__COMPREHEND__KEY_VALUE'           , get_env('AUTH__SERVICE__AWS__COMPREHEND__KEY_VALUE'  ))




            _.add_folder(mgraph_ai_service_mitmproxy__admin_ui.path)
            _.add_folder(mgraph_ai_service_mitmproxy__console.path)
            return _

    def handler(self):
        return run

    def lambda_dependencies(self):
        return LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS

    def lambda_name(self):
        return SERVICE_NAME