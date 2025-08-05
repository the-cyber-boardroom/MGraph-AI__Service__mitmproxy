from osbot_utils.helpers.Safe_Id                                        import Safe_Id
from osbot_utils.type_safe.Type_Safe                                    import Type_Safe
from mgraph_ai_service_base.service.info.schemas.Schema__Service_Status import Schema__Service_Status, Enum__Service_Environment


class Info__Service(Type_Safe):

    def status(self) -> Schema__Service_Status:                               # Get current service status
        return Schema__Service_Status(environment = self.environment())

    def environment(self):                                                   # Determine current environment
        import os
        if os.getenv('AWS_REGION'):
            return Enum__Service_Environment.aws_lambda
        else:
            return Enum__Service_Environment.local