from typing import Dict, List, Any, Set
from datetime                                                                import datetime
from osbot_fast_api.api.routes.Fast_API__Routes                              import Fast_API__Routes
from osbot_utils.type_safe.Type_Safe                                         import Type_Safe
from osbot_utils.type_safe.primitives.safe_str.Safe_Str                      import Safe_Str
from osbot_utils.type_safe.primitives.safe_uint.Safe_UInt                    import Safe_UInt

TAG__ROUTES_PROXY                  = 'proxy'
ROUTES_PATHS__PROXY                = [ f'/{TAG__ROUTES_PROXY}/process-request'  ,
                                       f'/{TAG__ROUTES_PROXY}/process-response' ,
                                       f'/{TAG__ROUTES_PROXY}/get-proxy-stats'  ,
                                       f'/{TAG__ROUTES_PROXY}/reset-proxy-stats']

# Domain-specific Safe types for proxy data
class Safe_Str__HTTP_Method(Safe_Str):                                        # HTTP method validation
    max_length = 10

class Safe_Str__Host(Safe_Str):                                           # Host/domain validation
    max_length = 255

class Safe_Str__Path(Safe_Str):                                           # URL path validation
    max_length = 2048

class Safe_UInt__HTTP_Status(Safe_UInt):                                  # HTTP status codes
    min_value = 100
    max_value = 599

# Request/Response schemas using Type_Safe
class Schema__Proxy__Request_Data(Type_Safe):                             # Incoming request from mitmproxy
    method  : Safe_Str__HTTP_Method                                       # HTTP method (GET, POST, etc)
    host    : Safe_Str__Host                                              # Target host
    path    : Safe_Str__Path                                              # Request path
    headers : Dict[str, str]                                              # Request headers
    stats   : Dict[str, Any]                                              # Request statistics

class Schema__Proxy__Response_Data(Type_Safe):                            # Incoming response from mitmproxy
    request  : Dict[str, Any]                                             # Original request info
    response : Dict[str, Any]                                             # Response details
    stats    : Dict[str, Any]                                             # Response statistics

class Schema__Proxy__Modifications(Type_Safe):                            # Modifications to apply
    headers_to_add    : Dict[str, str]                                    # Headers to add
    headers_to_remove : List[str]                                         # Headers to remove
    block_request     : bool            = False                           # Whether to block request
    block_status      : Safe_UInt__HTTP_Status = 403                      # Status code if blocked
    block_message     : Safe_Str        = "Blocked by proxy"              # Block message
    include_stats     : bool            = False                           # Include stats in response
    stats             : Dict[str, Any]                                    # Statistics to include


class Routes__Proxy(Fast_API__Routes):                                    # FastAPI routes for proxy control
    tag : str = TAG__ROUTES_PROXY

    # In-memory stats tracking (in production, use Redis or similar)
    total_requests  : Safe_UInt                                         # Total requests processed
    total_responses : Safe_UInt                                         # Total responses processed
    hosts_seen      : set                                               # Unique hosts encountered
    paths_seen      : set                                               # Unique paths encountered

    def process_request(self, request_data: Schema__Proxy__Request_Data   # Incoming request data
                       ) -> Schema__Proxy__Modifications:                 # Modifications to apply
        self.total_requests += 1
        self.hosts_seen.add(request_data.host)
        self.paths_seen.add(request_data.path)

        # Create response with modifications
        modifications = Schema__Proxy__Modifications()

        # Add custom headers
        modifications.headers_to_add = {
            "X-MGraph-Proxy"          : "v1.0"                           ,
            "X-Request-ID"            : f"req-{self.total_requests}"     ,
            "X-Processed-By"          : "FastAPI-Proxy"                  ,
            "X-Processed-At"          : datetime.utcnow().isoformat()    ,
            "X-Stats-Total-Requests"  : str(self.total_requests)         ,
            "X-Stats-Unique-Hosts"    : str(len(self.hosts_seen))        ,
        }

        # Block certain paths
        if "/blocked" in request_data.path:
            modifications.block_request = True
            modifications.block_message = f"Path {request_data.path} is blocked by policy"

        # Remove sensitive headers
        for header in request_data.headers:
            if any(sensitive in header for sensitive in ["Secret", "Private", "Token"]):
                modifications.headers_to_remove.append(header)

        return modifications

    def process_response(self, response_data: Schema__Proxy__Response_Data  # Incoming response data
                        ) -> Schema__Proxy__Modifications:                  # Modifications to apply
        self.total_responses += 1

        # Create response with modifications
        modifications = Schema__Proxy__Modifications()

        # Calculate stats
        stats = { "total_requests"   : self.total_requests                               ,
                  "total_responses"  : self.total_responses                              ,
                  "unique_hosts"     : len(self.hosts_seen)                              ,
                  "unique_paths"     : len(self.paths_seen)                              ,
                  "headers_received" : len(response_data.response.get("headers", {}))    ,
                  "original_status"  : response_data.response.get("status_code")         }

        # Add headers to response
        modifications.headers_to_add = {
            "X-MGraph-Proxy"              : "v1.0"                              ,
            "X-Response-ID"               : f"resp-{self.total_responses}"      ,
            "X-Proxy-Stats-Requests"      : str(self.total_requests)            ,
            "X-Proxy-Stats-Responses"     : str(self.total_responses)           ,
            "X-Proxy-Stats-Hosts"         : str(len(self.hosts_seen))           ,
            "X-Proxy-Stats-Headers-Count" : str(stats["headers_received"])      ,
        }

        # Add CORS headers for specific hosts
        if "httpbin.org" in response_data.request.get("host", ""):
            modifications.headers_to_add["Access-Control-Allow-Origin"]  = "*"
            modifications.headers_to_add["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

        # Include detailed stats
        modifications.include_stats = True
        modifications.stats         = stats

        return modifications

    def get_proxy_stats(self) -> Dict:                                    # Get current proxy statistics
        return { "total_requests"  : self.total_requests        ,
                 "total_responses" : self.total_responses       ,
                 "unique_hosts"    : list(self.hosts_seen)      ,
                 "unique_paths"    : list(self.paths_seen)      ,
                 "hosts_count"     : len(self.hosts_seen)       ,
                 "paths_count"     : len(self.paths_seen)       }

    def reset_proxy_stats(self) -> Dict:                                  # Reset proxy statistics
        old_stats = self.get_proxy_stats()

        self.total_requests  = 0
        self.total_responses = 0
        self.hosts_seen.clear()
        self.paths_seen.clear()

        return { "message"        : "Stats reset successfully" ,
                 "previous_stats" : old_stats              }

    def setup_routes(self):                                                # Configure FastAPI routes
        self.add_route_post(self.process_request   )
        self.add_route_post(self.process_response  )
        self.add_route_get (self.get_proxy_stats   )
        self.add_route_post(self.reset_proxy_stats )