# ═══════════════════════════════════════════════════════════════════════════════
# Semantic_Text__Service__Client__Requests
# Transport layer for Semantic Text Service - extends generic Fast_API__Client__Requests
# ═══════════════════════════════════════════════════════════════════════════════

from osbot_fast_api.services.registry.Fast_API__Client__Requests import Fast_API__Client__Requests


class Semantic_Text__Service__Client__Requests(Fast_API__Client__Requests):     # Semantic Text Service-specific transport
    pass                                                                        # service_type set at runtime
