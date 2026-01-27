import time
from typing                                                                 import Optional
from osbot_utils.type_safe.Type_Safe                                        import Type_Safe
from mgraph_ai_service_mitmproxy.schemas.proxy.Enum__WCF__Command_Type      import Enum__WCF__Command_Type
from mgraph_ai_service_mitmproxy.schemas.proxy.Enum__WCF__Content_Type      import Enum__WCF__Content_Type
from mgraph_ai_service_mitmproxy.schemas.wcf.Schema__WCF__Request           import Schema__WCF__Request
from mgraph_ai_service_mitmproxy.schemas.wcf.Schema__WCF__Response          import Schema__WCF__Response
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service        import Proxy__Cache__Service
from mgraph_ai_service_mitmproxy.service.consts.consts__proxy               import DEFAULT__WCF__PROXY__TIMEOUT
from mgraph_ai_service_mitmproxy.service.wcf.WCF__Cache__Integrator         import WCF__Cache__Integrator
from mgraph_ai_service_mitmproxy.service.wcf.WCF__Command__Processor        import WCF__Command__Processor
from mgraph_ai_service_mitmproxy.service.wcf.WCF__Request__Handler          import WCF__Request__Handler


class Proxy__WCF__Service(Type_Safe):                                          # WCF service integration with cache support
    wcf_base_url     : str   = "https://dev.web-content-filtering.mgraph.ai"   # WCF service base URL
    timeout          : float = DEFAULT__WCF__PROXY__TIMEOUT                    # Request timeout in seconds
    cache_service    : Proxy__Cache__Service  = None                           # Cache integration

    request_handler  : WCF__Request__Handler                                   # Handles WCF requests
    command_processor: WCF__Command__Processor                                 # Processes show commands
    cache_integrator : WCF__Cache__Integrator = None                           # Integrates cache

    def setup(self):
        self.request_handler   = WCF__Request__Handler(wcf_base_url = self.wcf_base_url,
                                                       timeout      = self.timeout     )
        self.command_processor = WCF__Command__Processor()
        self.cache_service     = Proxy__Cache__Service()#.setup()
        self.cache_integrator  = WCF__Cache__Integrator(cache_service = self.cache_service)
        return self

    def create_request(self, command_type : Enum__WCF__Command_Type,              # Type of WCF command
                             target_url   : str,                                  # URL to process
                             rating       : Optional[float] = None,               # Optional rating parameter
                             model_to_use : Optional[str] = None                  # Optional model override
                        ) -> Schema__WCF__Request:                               # WCF request object
        return self.request_handler.create_request(command_type = command_type  ,       # Create a WCF request with authentication from environment
                                                   target_url   = target_url    ,
                                                   rating       = rating        ,
                                                   model_to_use = model_to_use  )

    def make_request(self, wcf_request: Schema__WCF__Request                # Execute WCF service request and return response
                      ) -> Schema__WCF__Response:
        return self.request_handler.make_request(wcf_request)

    def process_show_command(self, show_value : str,                               # WCF show command value
                                   target_url : str                                # Target URL to process
                              ) -> Optional[Schema__WCF__Response]:                # Process WCF show command with cache integration"""
        parsed = self.command_processor.parse_show_command(show_value)      # Parse command and extract parameters

        if not parsed:
            return None

        command_type, rating, model_to_use, modified_url_suffix = parsed

        cached_response = self.cache_integrator.try_get_cached_response(target_url   = target_url  , # Check cache first
                                                                        show_value   = show_value  ,
                                                                        command_type = command_type)
        if cached_response:
            print(f"         >>> Cached response for: {target_url}")
            return cached_response

        start_time   = time.time()                                                      # Cache miss - call WCF service
        #modified_url = target_url + modified_url_suffix                                # todo: fix this logic since modified_url_suffix is actually the extra params to send to the wcf server

        wcf_request = self.create_request(command_type = command_type,
                                          target_url   = target_url  ,
                                          rating       = rating,
                                          model_to_use = model_to_use)

        wcf_response      = self.make_request(wcf_request)
        call_duration_ms  = (time.time() - start_time) * 1000

        print(f"       WCF took {call_duration_ms/1000:.2f} seconds for {target_url}")

        self.cache_integrator.store_wcf_response(target_url       = target_url      ,      # Store successful responses in cache
                                                 show_value       = show_value      ,
                                                 wcf_response     = wcf_response    ,
                                                 call_duration_ms = call_duration_ms)

        return wcf_response

    # todo: review this method since at the moment it is only used by the tests
    def _get_content_type_for_command(self,
                                      command_type: Enum__WCF__Command_Type # Command type to map
                                      ) -> Enum__WCF__Content_Type:         # Corresponding content type
        """Map command type to content type (delegated for backward compatibility)"""
        return self.cache_integrator.get_content_type_for_command(command_type)