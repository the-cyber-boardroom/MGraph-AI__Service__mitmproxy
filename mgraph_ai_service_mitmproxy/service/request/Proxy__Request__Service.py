from osbot_utils.type_safe.Type_Safe                                           import Type_Safe
from mgraph_ai_service_mitmproxy.schemas.debug.Schema__Debug__Params           import Schema__Debug__Params
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Request__Info           import Schema__Request__Info
from typing                                                                    import Dict, Optional
from mgraph_ai_service_mitmproxy.service.request.Proxy__Query__Parser__Service import Proxy__Query__Parser__Service
from mgraph_ai_service_mitmproxy.service.request.Proxy__URL__Builder__Service  import Proxy__URL__Builder__Service

# NOTE this is NOT the main entry point from the Mitmproxy

# todo: fix duplicate name with proxy/Proxy__Request__Service
class Proxy__Request__Service(Type_Safe):                        # Main request processing service
    query_parser  : Proxy__Query__Parser__Service                # Query string parser
    url_builder   : Proxy__URL__Builder__Service                 # URL builder

    def parse_request_info(self,
                          method        : str,                   # HTTP method
                          host          : str,                   # Host header
                          port          : int,                   # Port number
                          path          : str,                   # Request path
                          scheme        : str,                   # http or https
                          headers       : Dict[str, str],        # Request headers
                          query_string  : Optional[str] = None   # Query string
                          ) -> Schema__Request__Info:            # Parsed request info
        """Parse request information into structured format"""
        # Parse query parameters
        query_params = {}
        if query_string:
            query_params = self.query_parser.parse_query_string(query_string)

        # Build complete URL
        url = self.url_builder.build_url(
            scheme       = scheme,
            host         = host,
            port         = port,
            path         = path,
            query_params = query_params if query_params else None
        )

        # Extract specific headers
        content_type = None
        user_agent = None
        origin = None

        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower == 'content-type':
                content_type = value
            elif key_lower == 'user-agent':
                user_agent = value
            elif key_lower == 'origin':
                origin = value

        return Schema__Request__Info(
            method       = method,
            host         = host,
            port         = port,
            path         = path,
            url          = url,
            scheme       = scheme,
            headers      = headers.copy(),
            query_params = query_params,
            content_type = content_type,
            user_agent   = user_agent,
            origin       = origin
        )

    def parse_debug_params(self, request_info : Schema__Request__Info                     # Request info with query params
                            ) -> Schema__Debug__Params:                                   # Parsed debug params
        return Schema__Debug__Params.from_query_params(request_info.query_params)         # Parse debug parameters from request

    def extract_request_data(self, method       : str,                  # HTTP method
                                   host         : str,                  # Host
                                   port         : int,                  # Port
                                   path         : str,                  # Path
                                   scheme       : str,                  # Scheme
                                   headers      : Dict[str, str],       # Headers
                                   query_string : Optional[str] = None  # Query string
                              ) -> Dict:                                # Request data dict
        """
        Main entry point: Extract complete request data

        Returns a dictionary suitable for Schema__Proxy__Response_Data.request
        """
        # Parse request info
        request_info = self.parse_request_info(
            method       = method,
            host         = host,
            port         = port,
            path         = path,
            scheme       = scheme,
            headers      = headers,
            query_string = query_string
        )

        # Convert to dict
        return request_info.to_dict()

    def extract_debug_params(self,
                            method       : str,                  # HTTP method
                            host         : str,                  # Host
                            port         : int,                  # Port
                            path         : str,                  # Path
                            scheme       : str,                  # Scheme
                            headers      : Dict[str, str],       # Headers
                            query_string : Optional[str] = None  # Query string
                            ) -> Dict[str, str]:                 # Debug params dict
        """
        Main entry point: Extract debug parameters

        Returns a dictionary suitable for Schema__Proxy__Response_Data.debug_params
        """
        # Parse request info
        request_info = self.parse_request_info(
            method       = method,
            host         = host,
            port         = port,
            path         = path,
            scheme       = scheme,
            headers      = headers,
            query_string = query_string
        )

        # Parse debug params
        debug_params = self.parse_debug_params(request_info)

        # Return as dict
        return debug_params.to_dict()

    def should_process_debug_commands(self,
                                     query_string : Optional[str]  # Query string
                                     ) -> bool:                  # Whether to process debug
        """Quick check if request has debug parameters"""
        if not query_string:
            return False

        query_params = self.query_parser.parse_query_string(query_string)
        return self.query_parser.has_debug_params(query_params)

    def clean_url_for_backend(self,
                             url          : str,                 # Original URL
                             remove_debug : bool = True          # Remove debug params
                             ) -> str:                           # Cleaned URL
        """
        Clean URL for backend request (optionally remove debug params)

        This is useful when proxying to backend - you may want to remove
        debug parameters so they don't affect backend processing.
        """
        if not remove_debug:
            return url

        # Parse URL
        base_url = self.url_builder.extract_base_url(url)

        if '?' not in url:
            return url

        # Extract query params
        query_params = self.query_parser.parse_url_query(url)

        # Remove debug params
        debug_keys = ['show', 'inject', 'replace', 'debug', 'inject_debug']
        cleaned_params = {k: v for k, v in query_params.items() if k not in debug_keys}

        # Rebuild URL
        if cleaned_params:
            query_string = self.query_parser.build_query_string(cleaned_params)
            return f"{base_url}?{query_string}"

        return base_url