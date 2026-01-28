# ═══════════════════════════════════════════════════════════════════════════════
# HTML__Service__Client__Requests
# Transport layer for HTML Service - extends generic Fast_API__Client__Requests
# ═══════════════════════════════════════════════════════════════════════════════

from osbot_fast_api.services.registry.Fast_API__Client__Requests import Fast_API__Client__Requests


class HTML__Service__Client__Requests(Fast_API__Client__Requests):              # HTML Service-specific transport
    pass                                                                        # service_type set at runtime
