# ═══════════════════════════════════════════════════════════════════════════════
# HTML Graph Cache Handler
# Handles cache operations for mitm-mode=cache
# File: mgraph_ai_service_mitmproxy/service/html_graph/HTML_Graph__Cache__Handler.py
# ═══════════════════════════════════════════════════════════════════════════════

from typing                                                                                     import Dict, Any
from datetime                                                                                   import datetime
from mgraph_ai_service_html_graph.client.Html_Graph__Service__Client                            import Html_Graph__Service__Client
from osbot_utils.type_safe.Type_Safe                                                            import Type_Safe
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                        import Safe_Str__Url
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                  import type_safe
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode                   import Enum__HTML__Transformation_Mode


class HTML_Graph__Cache__Handler(Type_Safe):                                    # Handles HTML Graph cache operations
    html_graph_client : Html_Graph__Service__Client                       # HTML Graph API client

    @type_safe
    def construct_url(self, scheme : str,                                  # Build full URL from components
                            host   : str,
                            path   : str
                       ) -> Safe_Str__Url:
        return f"{scheme}://{host}{path}"

    @type_safe
    def get_mode_from_cookies(self, cookies: Dict[str, str]                     # Extract mitm-mode from cookies dict
                               ) -> Enum__HTML__Transformation_Mode:
        mode_value = cookies.get("mitm-mode", "off")
        return Enum__HTML__Transformation_Mode.from_cookie_value(mode_value)

    @type_safe
    def is_cache_mode(self, cookies: Dict[str, str]) -> bool:                   # Check if mitm-mode=cache
        mode = self.get_mode_from_cookies(cookies)
        return mode == Enum__HTML__Transformation_Mode.CACHE

    @type_safe
    def check_cache(self, request_data: dict                                    # Check HTML Graph for cached response
                     ) -> dict:                                                 # Returns cached_response dict or None
        scheme = request_data.get("scheme", "https")
        host   = request_data.get("host", "")
        path   = request_data.get("path", "/")

        url = self.construct_url(scheme = scheme,
                                 host   = host  ,
                                 path   = path )

        print(f"    🔄 mitm-mode=cache: Checking HTML Graph cache for {host}{path}")

        result = self.html_graph_client.load_html(url)

        if result.success and result.found:
            print(f"      ✅ HTML Graph HIT - serving {result.char_count} chars from cache")
            cached_response =  {"status_code": 200                                         ,
                                "body"       : str(result.html)                            ,
                                "headers"    : {"content-type"      : "text/html; charset=utf-8"    ,
                                                "x-cache-source"    : "html-graph"                  ,
                                                "x-cache-key"       : str(result.cache_key)         ,
                                                "x-cache-id"        : str(result.cache_id)          ,
                                                "x-cache-chars"     : str(result.char_count)        ,
                                                "x-cache-timestamp" : datetime.utcnow().isoformat() }}
            return {"cached_response": cached_response}

        if result.success and not result.found:
            print(f"      ❌ HTML Graph MISS - will fetch from origin and store")
        else:
            print(f"      ⚠️  HTML Graph error: {result.error}")

        return None

    @type_safe
    def store_html(self, response_data: dict                                    # Store HTML in HTML Graph after cache miss
                    ) -> Dict[str, str]:                                        # Returns headers to add to response
        response = response_data.get("response", {})
        request  = response_data.get("request", {})

        content_type = response.get("content_type", "")
        if "text/html" not in content_type.lower():
            print(f"    ⏭️  Skipping HTML Graph store - not HTML: {content_type}")
            return {"x-html-graph-skipped": "not-html"}

        html_body = response.get("body", "")
        if not html_body:
            print(f"    ⏭️  Skipping HTML Graph store - empty body")
            return {"x-html-graph-skipped": "empty-body"}

        scheme = request.get("scheme", "https")
        host   = request.get("host", "")
        path   = request.get("path", "/")

        url = self.construct_url(scheme = scheme,
                                 host   = host  ,
                                 path   = path  )

        print(f"    📦 Storing in HTML Graph: {host}{path}")

        result = self.html_graph_client.store_html(url=url, html=html_body)

        if result.success:
            print(f"      ✅ Stored {result.char_count} chars")
            return {"x-html-graph-stored"    : "true"                ,
                    "x-html-graph-cache-key" : str(result.cache_key) ,
                    "x-html-graph-cache-id"  : str(result.cache_id)  ,
                    "x-html-graph-chars"     : str(result.char_count)}
        else:
            print(f"      ⚠️  Store failed: {result.error}")
            return {"x-html-graph-stored": "false"                      ,
                    "x-html-graph-error" : str(result.error) or "unknown"}