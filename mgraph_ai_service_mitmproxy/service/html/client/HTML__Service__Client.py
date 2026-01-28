# ═══════════════════════════════════════════════════════════════════════════════
# HTML__Service__Client
# Stateless facade for HTML Service operations
# Config is stored in registry, looked up at request time
# ═══════════════════════════════════════════════════════════════════════════════

import json
from osbot_utils.decorators.methods.cache_on_self                                       import cache_on_self
from osbot_utils.type_safe.Type_Safe                                                    import Type_Safe
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Service__Request            import Schema__HTML__Service__Request
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Service__Response           import Schema__HTML__Service__Response
from mgraph_ai_service_mitmproxy.schemas.html.Schema__Hashes__To__Html__Request         import Schema__Hashes__To__Html__Request
from mgraph_ai_service_mitmproxy.schemas.html.Schema__Html__To__Dict__Hashes__Request   import Schema__Html__To__Dict__Hashes__Request
from mgraph_ai_service_mitmproxy.schemas.html.Schema__Html__To__Dict__Hashes__Response  import Schema__Html__To__Dict__Hashes__Response
from mgraph_ai_service_mitmproxy.service.html.client.HTML__Service__Client__Requests    import HTML__Service__Client__Requests


class HTML__Service__Client(Type_Safe):                                         # Stateless facade - config in registry

    @cache_on_self
    def requests(self) -> HTML__Service__Client__Requests:                      # Create transport with service_type set
        requests              = HTML__Service__Client__Requests()
        requests.service_type = HTML__Service__Client                           # Self-reference for registry lookup
        return requests

    # ───────────────────────────────────────────────────────────────────────────
    # Health Check
    # ───────────────────────────────────────────────────────────────────────────

    def health(self) -> bool:                                                   # Check service health
        try:
            result = self.requests().execute(method="GET", path="/info/health")
            if result.status_code == 200:
                data = result.json() or {}
                return data.get('status') == 'ok'
            return False
        except:
            return False

    # ───────────────────────────────────────────────────────────────────────────
    # Transform HTML
    # ───────────────────────────────────────────────────────────────────────────

    def transform_html(self, request: Schema__HTML__Service__Request            # Transform HTML using specified mode
                      ) -> Schema__HTML__Service__Response:

        endpoint_path = request.transformation_mode.to_endpoint_path()

        if not endpoint_path:
            return Schema__HTML__Service__Response(
                status_code   = 400                                             ,
                content_type  = "text/plain"                                    ,
                body          = ""                                              ,
                headers       = {}                                              ,
                success       = False                                           ,
                error_message = f"Invalid transformation mode: {request.transformation_mode}"
            )

        payload = request.to_json_payload()

        try:
            result = self.requests().execute(method = "POST"       ,
                                             path   = endpoint_path,
                                             body   = payload      )

            return self._build_response(result)

        except Exception as e:
            error_type = type(e).__name__
            if 'Timeout' in error_type:
                return Schema__HTML__Service__Response(
                    status_code   = 504                                         ,
                    content_type  = "text/plain"                                ,
                    body          = ""                                          ,
                    headers       = {}                                          ,
                    success       = False                                       ,
                    error_message = f"HTML Service timeout: {str(e)}"
                )
            elif 'Request' in error_type:
                return Schema__HTML__Service__Response(
                    status_code   = 502                                         ,
                    content_type  = "text/plain"                                ,
                    body          = ""                                          ,
                    headers       = {}                                          ,
                    success       = False                                       ,
                    error_message = f"HTML Service request failed: {str(e)}"
                )
            else:
                return Schema__HTML__Service__Response(
                    status_code   = 500                                         ,
                    content_type  = "text/plain"                                ,
                    body          = ""                                          ,
                    headers       = {}                                          ,
                    success       = False                                       ,
                    error_message = f"Unexpected error: {str(e)}"
                )

    # ───────────────────────────────────────────────────────────────────────────
    # Get Dict Hashes
    # ───────────────────────────────────────────────────────────────────────────

    def get_dict_hashes(self, request: Schema__Html__To__Dict__Hashes__Request
                       ) -> Schema__Html__To__Dict__Hashes__Response:

        endpoint_path = "/html/to/dict/hashes"
        payload       = request.json()

        try:
            result = self.requests().execute(method = "POST"       ,
                                             path   = endpoint_path,
                                             body   = payload      )

            if result.status_code == 200:
                return Schema__Html__To__Dict__Hashes__Response.from_json(result.json())
            else:
                return self._empty_dict_hashes_response()

        except Exception as e:
            print(f"Error calling get_dict_hashes: {e}")
            return self._empty_dict_hashes_response()

    # ───────────────────────────────────────────────────────────────────────────
    # Reconstruct from Hashes
    # ───────────────────────────────────────────────────────────────────────────

    def reconstruct_from_hashes(self, request: Schema__Hashes__To__Html__Request
                               ) -> Schema__HTML__Service__Response:

        endpoint_path = "/hashes/to/html"
        payload       = request.json()

        try:
            result = self.requests().execute(method = "POST"       ,
                                             path   = endpoint_path,
                                             body   = payload      )

            content_type = result.headers.get('content-type', 'text/html') if result.headers else 'text/html'
            body         = result.text if result.status_code == 200 else ""

            return Schema__HTML__Service__Response(
                status_code  = result.status_code           ,
                content_type = content_type                 ,
                body         = body                         ,
                headers      = dict(result.headers) or {}         ,
                success      = result.status_code == 200
            )

        except Exception as e:
            return Schema__HTML__Service__Response(
                status_code   = 500                                         ,
                content_type  = "text/plain"                                ,
                body          = ""                                          ,
                headers       = {}                                          ,
                success       = False                                       ,
                error_message = f"Error reconstructing HTML: {str(e)}"
            )

    # ───────────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ───────────────────────────────────────────────────────────────────────────

    def _build_response(self, result) -> Schema__HTML__Service__Response:       # Build response from raw result
        content_type = result.headers.get('content-type', 'text/plain') if result.headers else 'text/plain'

        if 'application/json' in content_type:
            try:
                body = json.dumps(result.json(), indent=2) if result.json() else result.text
            except:
                body = result.text or ""
        else:
            body = result.text or ""

        return Schema__HTML__Service__Response(status_code  = result.status_code           ,
                                               content_type = content_type                 ,
                                               body         = body                         ,
                                               headers      = dict(result.headers) or {}         ,
                                               success      = result.status_code == 200    )

    def _empty_dict_hashes_response(self) -> Schema__Html__To__Dict__Hashes__Response:
        return Schema__Html__To__Dict__Hashes__Response(
            html_dict          = {}   ,
            hash_mapping       = {}   ,
            node_count         = 0    ,
            max_depth          = 0    ,
            total_text_hashes  = 0    ,
            max_depth_reached  = False
        )
