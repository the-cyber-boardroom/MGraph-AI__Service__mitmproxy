from mgraph_ai_service_html_graph.client.register_html_graph_service import register_html_graph_service__in_memory

from mgraph_ai_service_cache_client.client.cache_service.register_cache_service import register_cache_service__in_memory
from osbot_fast_api.core_routes.registry.Routes__Service__Registry import Routes__Service__Registry

import mgraph_ai_service_mitmproxy__console
from osbot_fast_api.api.decorators.route_path                   import route_path
from osbot_fast_api.api.routes.Routes__Set_Cookie               import Routes__Set_Cookie
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API    import Serverless__Fast_API
from starlette.responses                                        import RedirectResponse
from starlette.staticfiles                                      import StaticFiles
from mgraph_ai_service_mitmproxy.config                         import FAST_API__TITLE, MITMPROXY__SERVICE__WEB_CONSOLE__PATH, MITMPROXY__SERVICE__WEB_CONSOLE__MAJOR__VERSION, MITMPROXY__SERVICE__WEB_CONSOLE__LATEST__VERSION, MITMPROXY__SERVICE__WEB_CONSOLE__ROUTE__START_PAGE
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Cache  import Routes__Cache
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Proxy  import Routes__Proxy
from mgraph_ai_service_mitmproxy.utils.Version                  import version__mgraph_ai_service_mitmproxy
from osbot_fast_api_serverless.fast_api.routes.Routes__Info     import Routes__Info

class Mitmproxy__Service__Fast_API(Serverless__Fast_API):
    run_in_memory : bool = True                                 # todo: find a better place to put this option

    def setup(self):
        with self.config as _:
            _.name           = FAST_API__TITLE
            _.version        =  version__mgraph_ai_service_mitmproxy
            #_.enable_api_key = False                       # LEGACY
            _.enable_api_key = True                                     # todo: update proxy to support this auth

        self.setup_web_console()

        self.setup__in_memory__support()
        return super().setup()

    def setup__in_memory__support(self):
        if self.run_in_memory:
            register_cache_service__in_memory()
            register_html_graph_service__in_memory()



    def setup_routes(self):
        self.add_routes(Routes__Proxy            )
        self.add_routes(Routes__Cache            )
        self.add_routes(Routes__Info             )
        self.add_routes(Routes__Set_Cookie       )
        self.add_routes(Routes__Service__Registry)


    # todo: refactor to separate class (focused on setting up this static route)
    def setup_web_console(self):


        path_static_folder  = mgraph_ai_service_mitmproxy__console.path
        path_name           = MITMPROXY__SERVICE__WEB_CONSOLE__PATH
        path_static         = f"/{path_name}"

        major_version       = MITMPROXY__SERVICE__WEB_CONSOLE__MAJOR__VERSION
        latest_version      = MITMPROXY__SERVICE__WEB_CONSOLE__LATEST__VERSION
        start_page          = MITMPROXY__SERVICE__WEB_CONSOLE__ROUTE__START_PAGE

        path_latest_version = f"/{path_name}/{major_version}/{latest_version}/{start_page}.html"
        self.app().mount(path_static, StaticFiles(directory=path_static_folder), name=path_name)


        @route_path(path=f'/{MITMPROXY__SERVICE__WEB_CONSOLE__PATH}')
        def redirect_to_latest():
            return RedirectResponse(url=path_latest_version)

        self.add_route_get(redirect_to_latest)        


