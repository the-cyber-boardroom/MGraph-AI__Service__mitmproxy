from osbot_fast_api.api.Fast_API_Routes                import Fast_API_Routes
from mgraph_ai_service_base.service.info.Info__Service import Info__Service
from mgraph_ai_service_base.utils.Version              import version__mgraph_ai_service_base

ROUTES_PATHS__INFO = ['/info/version', '/info/status']

class Routes__Info(Fast_API_Routes):
    tag = 'info'
    info_service: Info__Service

    def version(self):                                          # Get service version
        return {'version': version__mgraph_ai_service_base}

    def status(self):                                           # Get service status information
        return self.info_service.status()

    def setup_routes(self):
        self.add_route_get(self.version)
        self.add_route_get(self.status)