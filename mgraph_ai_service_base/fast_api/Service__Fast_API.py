from osbot_fast_api_serverless.fast_api.Serverless__Fast_API import Serverless__Fast_API
from mgraph_ai_service_base.fast_api.routes.Routes__Health   import Routes__Health
from mgraph_ai_service_base.fast_api.routes.Routes__Info     import Routes__Info


class Service__Fast_API(Serverless__Fast_API):

    def setup_routes(self):
        self.add_routes(Routes__Health)
        self.add_routes(Routes__Info  )