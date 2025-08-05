from enum import Enum
from typing                                 import Literal
from osbot_utils.helpers.Safe_Id            import Safe_Id
from osbot_utils.helpers.Timestamp_Now      import Timestamp_Now
from osbot_utils.helpers.safe_str.Safe_Str__Version import Safe_Str__Version
from osbot_utils.type_safe.Type_Safe        import Type_Safe
from mgraph_ai_service_base.config          import SERVICE_NAME
from mgraph_ai_service_base.utils.Version   import version__mgraph_ai_service_base

class Enum__Service_Status(Enum):
    operational : str = 'operational'
    degraded    : str = 'degraded'

class Enum__Service_Environment(Enum):
    aws_lambda : str = 'aws-lambda'
    local      : str = 'local'

class Schema__Service_Status(Type_Safe):
    service     : Safe_Id                   = Safe_Id(SERVICE_NAME)
    version     : Safe_Str__Version         = version__mgraph_ai_service_base
    status      : Enum__Service_Status      = Enum__Service_Status.operational
    environment : Enum__Service_Environment = Enum__Service_Environment.local
    timestamp   : Timestamp_Now