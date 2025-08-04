from osbot_fast_api.api.Fast_API_Routes import Fast_API_Routes

ROUTES_PATHS__HEALTH = ['/health/status', '/health/details']

class Routes__Health(Fast_API_Routes):
    tag = 'health'

    def status(self):
        """Basic health check endpoint"""
        return {"status": "healthy", "service": "mgraph-ai-service-base"}

    def details(self):
        """Detailed health check with component status"""
        return {
            "status": "healthy",
            "service": "mgraph-ai-service-base",
            "components": {
                "api": "operational",
                "dependencies": "operational"
            },
            "timestamp": self._get_timestamp()
        }

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def setup_routes(self):
        self.add_route_get(self.status )
        self.add_route_get(self.details)