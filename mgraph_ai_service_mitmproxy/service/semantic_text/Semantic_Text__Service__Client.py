# ═══════════════════════════════════════════════════════════════════════════════
# Semantic_Text__Service__Client
# Stateless facade for Semantic Text Service operations
# Config is stored in registry, looked up at request time
# ═══════════════════════════════════════════════════════════════════════════════

from osbot_utils.decorators.methods.cache_on_self                                                               import cache_on_self
from osbot_utils.type_safe.Type_Safe                                                                            import Type_Safe
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                                                  import type_safe
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client__Requests                 import Semantic_Text__Service__Client__Requests
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Response   import Schema__Semantic_Text__Transformation__Response
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Request    import Schema__Semantic_Text__Transformation__Request


class Semantic_Text__Service__Client(Type_Safe):                                # Stateless facade - config in registry

    @cache_on_self
    def requests(self) -> Semantic_Text__Service__Client__Requests:             # Create transport with service_type set
        requests              = Semantic_Text__Service__Client__Requests()
        requests.service_type = Semantic_Text__Service__Client                  # Self-reference for registry lookup
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
    # Transform Text
    # ───────────────────────────────────────────────────────────────────────────

    @type_safe
    def transform_text(self, request: Schema__Semantic_Text__Transformation__Request
                      ) -> Schema__Semantic_Text__Transformation__Response:

        endpoint_path = "/text-transformation/transform"
        payload       = request.json()

        try:
            result = self.requests().execute(method = "POST"       ,
                                             path   = endpoint_path,
                                             body   = payload      )
            if result.status_code == 200 and result.json():
                return Schema__Semantic_Text__Transformation__Response.from_json(result.json())
            else:
                return Schema__Semantic_Text__Transformation__Response(
                    success       = False                                       ,
                    error_message = f"Request failed with status {result.status_code}"
                )

        except Exception as e:
            return Schema__Semantic_Text__Transformation__Response(
                success       = False                               ,
                error_message = f"Unexpected error: {str(e)}"
            )
