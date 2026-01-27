from osbot_utils.type_safe.Type_Safe                                                 import Type_Safe
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Request_Data           import Schema__Proxy__Request_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Response_Data          import Schema__Proxy__Response_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications          import Schema__Proxy__Modifications
from mgraph_ai_service_mitmproxy.service.proxy.response.Proxy__Response__Service     import Proxy__Response__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Stats__Service                 import Proxy__Stats__Service
from mgraph_ai_service_mitmproxy.service.proxy.request.Proxy__Request__Service       import Proxy__Request__Service
from mgraph_ai_service_mitmproxy.service.admin.Proxy__Admin__Service                 import Proxy__Admin__Service
from typing                                                                          import Dict, Any

class Proxy__Service(Type_Safe):                                      # Main proxy service orchestration
    stats_service    : Proxy__Stats__Service                          # Statistics tracking
    request_service  : Proxy__Request__Service      = None            # Request processing
    response_service : Proxy__Response__Service     = None            # Response processing
    admin_service    : Proxy__Admin__Service        = None            # Admin page generation

    def setup(self):
        self.admin_service    = Proxy__Admin__Service   ().setup()
        self.response_service = Proxy__Response__Service().setup()
        self.request_service  = Proxy__Request__Service ().setup()
        return self

    def process_request(self, request_data : Schema__Proxy__Request_Data  # Process incoming request
                         ) -> Schema__Proxy__Modifications:
        self.log_request(request_data)
        return self.request_service.process_request(request_data)

    def process_response(self, response_data : Schema__Proxy__Response_Data  # Process incoming response
                         ) -> Schema__Proxy__Modifications:
        self.log_response(response_data)
        processing_result = self.response_service.process_response(response_data)           # Convert processing result to modifications

        return processing_result.modifications

        if type(processing_result) is Type_Safe:                # todo: handle bug that happened here (when using the simulate-ui)
            return processing_result.modifications
        else:
            return None

    def get_stats(self) -> Dict[str, Any]:                           # Get current statistics
        return self.stats_service.get_stats()

    def reset_stats(self) -> Dict[str, Any]:                         # Reset statistics
        return self.stats_service.reset_stats()


    def log_request(self, request_data : Schema__Proxy__Request_Data   # Log incoming request
                     ) -> None:                                        # No return value
        is_admin     = request_data.path.startswith('/mitm-proxy')
        admin_emoji  = '🔧 ' if is_admin else ''
        host         = request_data.host
        path         = request_data.path
        method_emoji = self._get_method_emoji(request_data.method)

        print(f"➡️ {admin_emoji:2} {method_emoji:2} {request_data.method:<6} {host:<30} {path}")



    def log_response(self, response_data : Schema__Proxy__Response_Data  # Log outgoing response
                      ) -> None:                                         # No return value
        status       = response_data.response.get('status_code', 0)
        host         = response_data.request.get('host', '')
        path         = response_data.request.get('path', '')
        status_emoji = self._get_status_emoji(status)
        print(f"⬅️ {status_emoji:2} ___{status:<} {host:<30} {path}")



    def _get_method_emoji(self, method: str) -> str:                 # Get emoji for HTTP method
        method_emojis = { 'GET'    : '📥' ,
                          'POST'   : '📮' ,
                          'PUT'    : '✏️' ,
                          'DELETE' : '🗑️' ,
                          'PATCH'  : '🔧' ,
                          'OPTIONS': '❓' }
        return method_emojis.get(method.upper(), '📨')

    def _get_status_emoji(self, status: int) -> str:                 # Get emoji for status code
        if   200 <= status < 300:   return '✅'
        elif 300 <= status < 400:   return '↪️'
        elif 400 <= status < 500:   return '⚠️'
        elif 500 <= status < 600:   return '❌'
        else:                       return '❔'