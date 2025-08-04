from osbot_utils.type_safe.Type_Safe import Type_Safe
from mgraph_ai_service_base.utils.Version import version__mgraph_ai_service_base

class Info__Service(Type_Safe):

    def get_status(self):                               # Get current service status
        return { "service"    : "mgraph-ai-service-base",       # todo change this to use Type_Safe class
                 "version"    : version__mgraph_ai_service_base,
                 "status"     : "operational",
                 "environment": self._get_environment(),
                 "timestamp"  : self._get_timestamp()
        }

    def _get_environment(self):                             # todo: rename method
        """Determine current environment"""
        import os
        if os.getenv('AWS_REGION'):
            return "aws-lambda"
        return "local"

    def _get_timestamp(self):                             # todo : use osbot-utils method
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"