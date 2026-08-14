from osbot_utils.type_safe.Type_Safe                                                                      import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_UInt                                                     import Safe_UInt
from mgraph_ai_service_mitmproxy.service.proxy.inject.schemas.Enum__Inject__Script__Load__Status         import Enum__Inject__Script__Load__Status


class Schema__Inject__Script__Load__Result(Type_Safe):
    status     : Enum__Inject__Script__Load__Status = Enum__Inject__Script__Load__Status.ERROR
    script     : str                                 = ''
    attempts   : Safe_UInt                           = Safe_UInt(0)
    error_type : str                                 = ''
