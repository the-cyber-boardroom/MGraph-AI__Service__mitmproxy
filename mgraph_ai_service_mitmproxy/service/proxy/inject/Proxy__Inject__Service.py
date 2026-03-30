"""Proxy Inject Service — generic cache-backed script injection.

Uses a single cache entry (cache_key='inject') for all inject scripts.
Each domain's script is stored as a data_key under that entry:

    cache_key: inject  →  cache_id (created once)
    data_key:  sites/{domain}/filter.js

S3 path: {namespace}/inject/data/sites/{domain}/filter.js
"""

import re
from typing                                                                          import Optional
from urllib.parse                                                                    import urlparse
from osbot_utils.type_safe.Type_Safe                                                 import Type_Safe
from osbot_utils.helpers.cache.Cache__Hash__Generator                                import Cache__Hash__Generator
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Store__Strategy import Enum__Cache__Store__Strategy
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                 import Proxy__Cache__Service


NONCE_PATTERN       = re.compile(r'<script[^>]+nonce=["\']([^"\']+)["\']', re.IGNORECASE)
INJECT_CACHE_KEY    = 'inject'                                        # Single cache_key for all inject scripts
INJECT_ENTRY_FILE   = 'inject-entry'                                  # file_id for the cache entry
INJECT_DATA_FILE_ID = 'data'                                          # data_file_id for script content
EMPTY_STUB          = '// inject script for this domain — edit this file in S3 to activate\n'


class Proxy__Inject__Service(Type_Safe):
    cache_service : Proxy__Cache__Service
    #_script_cache : dict                                              # In-memory: domain → script_code (or '')
    _cache_id     : str                   = None                      # Single cache_id for all inject scripts

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     if self._script_cache is None:
    #         self._script_cache = {}

    # ═══════════════════════════════════════════════════════════════
    # Domain extraction
    # ═══════════════════════════════════════════════════════════════

    def extract_domain(self, host: str) -> str:
        """Extract the registrable domain from a host.
        """
        host = (host or '').lower().strip()
        if not host:
            return ''

        two_part_tlds = ['.co.uk', '.com.au', '.co.nz', '.co.jp', '.org.uk', '.ac.uk']
        for tld in two_part_tlds:
            if host.endswith(tld):
                prefix = host[:-(len(tld))]
                parts = prefix.rsplit('.', 1)
                return (parts[-1] if parts else prefix) + tld

        parts = host.rsplit('.', 2)
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return host

    def data_key_for_domain(self, domain: str) -> str:
        """Build the data_key for a domain's inject script."""
        return f"sites/{domain}/filter.js"

    # ═══════════════════════════════════════════════════════════════
    # Single cache_id for all inject scripts (created once)
    # ═══════════════════════════════════════════════════════════════

    def _get_or_create_cache_id(self) -> Optional[str]:
        """Get or create the single cache_id for all inject scripts.

        Uses cache_key='inject'. Created once, cached in memory.
        """
        if self._cache_id:
            return self._cache_id

        if not self.cache_service or not self.cache_service.cache_config.enabled:
            return None

        cache_hash = Cache__Hash__Generator().from_string(INJECT_CACHE_KEY)
        namespace  = self.cache_service.cache_config.namespace
        client     = self.cache_service.cache_client

        # Try to find existing entry
        try:
            result = client.retrieve().retrieve__hash__cache_hash(cache_hash=cache_hash,
                                                                   namespace=namespace)
            if result:
                self._cache_id = result.metadata.cache_id
                return self._cache_id
        except Exception as e:
            print(f"    ⚠️ Inject cache lookup failed: {e}")

        # Not found — create entry
        try:
            import json
            entry_body = { 'type'      : 'inject-scripts'  ,
                            'cache_key' : INJECT_CACHE_KEY }

            result = client.store().store__json__cache_key(
                namespace       = namespace,
                strategy        = Enum__Cache__Store__Strategy.KEY_BASED,
                cache_key       = INJECT_CACHE_KEY,
                file_id         = INJECT_ENTRY_FILE,
                body            = entry_body,
                json_field_path = 'cache_key')

            if result:
                self._cache_id = result.cache_id
                print(f"    🆕 Created inject cache entry (cache_id: {self._cache_id})")
                return self._cache_id

        except Exception as e:
            print(f"    ⚠️ Inject cache entry creation failed: {e}")

        return None

    # ═══════════════════════════════════════════════════════════════
    # Script resolution: memory → S3 → create stub
    # ═══════════════════════════════════════════════════════════════

    def resolve_script(self, domain: str) -> str:
        """Resolve the inject script for a domain.

        Returns script code, or empty string if no script configured.
        """
        if not domain:
            return ''

        # # 1. In-memory cache
        # if domain in self._script_cache:
        #     return self._script_cache[domain]

        # 2. Load from S3
        script = self._load_from_cache(domain)

        if script is not None:
            # is_stub = self._is_stub(script)
            # self._script_cache[domain] = '' if is_stub else script

            # if is_stub:
            #     print(f"    📭 Inject script for {domain} is empty stub — pass through")
            #     return ''
            # else:
            print(f"    📦 Loaded inject script for {domain} from S3 ({len(script):,} chars)")
            return script

        # 3. Not in S3 → create empty stub
        self._store_to_cache(domain, EMPTY_STUB)
        #self._script_cache[domain] = ''
        print(f"    🆕 Created inject stub for {domain} in S3 — edit to activate")
        return EMPTY_STUB

    def _is_stub(self, script: str) -> bool:
        """Check if a script is just the empty stub."""
        stripped = script.strip()
        if not stripped:
            return True
        return all(line.strip() == '' or line.strip().startswith('//')
                   for line in stripped.split('\n'))

    def _load_from_cache(self, domain: str) -> Optional[str]:
        """Load script from S3: cache_id + data_key = sites/{domain}/filter.js"""
        cache_id = self._get_or_create_cache_id()
        if not cache_id:
            return None

        try:
            result = self.cache_service.cache_client.data().retrieve().data__string__with__id_and_key(
                cache_id     = cache_id,
                namespace    = self.cache_service.cache_config.namespace,
                data_key     = self.data_key_for_domain(domain),
                data_file_id = INJECT_DATA_FILE_ID)

            if result and result.strip():
                return result

        except Exception as e:
            print(f"    ⚠️ Cache read failed for {domain}: {e}")

        return None

    def _store_to_cache(self, domain: str, script: str) -> bool:
        """Store script to S3: cache_id + data_key = sites/{domain}/filter.js"""
        cache_id = self._get_or_create_cache_id()
        if not cache_id:
            return False

        try:
            self.cache_service.cache_client.data_store().data__store_string__with__id_and_key(
                cache_id     = cache_id,
                namespace    = self.cache_service.cache_config.namespace,
                data_key     = self.data_key_for_domain(domain),
                data_file_id = INJECT_DATA_FILE_ID,
                body         = script)
            return True

        except Exception as e:
            print(f"    ⚠️ Cache write failed for {domain}: {e}")
            return False

    # def invalidate_cache(self, domain: str = ''):
    #     """Clear in-memory caches. Call after editing a script in S3."""
    #     if domain:
    #         self._script_cache.pop(domain, None)
    #         print(f"    🗑️ Invalidated inject cache for {domain}")
    #     else:
    #         self._script_cache.clear()
    #         self._cache_id = None                                     # Also reset cache_id
    #         print(f"    🗑️ Invalidated all inject caches")

    # ═══════════════════════════════════════════════════════════════
    # CSP handling
    # ═══════════════════════════════════════════════════════════════

    def extract_nonce(self, html: str) -> str:
        match = NONCE_PATTERN.search(html)
        return match.group(1) if match else ''

    def get_csp_headers_to_remove(self) -> list:
        return ['content-security-policy',             'Content-Security-Policy',
                'content-security-policy-report-only', 'Content-Security-Policy-Report-Only']

    # ═══════════════════════════════════════════════════════════════
    # Main injection
    # ═══════════════════════════════════════════════════════════════

    def inject_script_into_html(self, html       : str,
                                      target_url : str = '',
                                      host       : str = ''
                                ) -> tuple:
        """Inject the appropriate script into an HTML response.

        Returns: (modified_html, headers_to_add, headers_to_remove)
                 or (None, {}, []) if no injection needed.
        """
        if not html:
            return (None, {}, [])

        if not host and target_url:
            host = urlparse(target_url).netloc

        domain = self.extract_domain(host)
        if not domain:
            return (None, {}, [])

        # Resolve script (memory → S3 → create stub)
        script_code = self.resolve_script(domain)
        if not script_code:
            return (None, {}, [])
        # Extract nonce and build script tag
        nonce = self.extract_nonce(html)
        nonce_attr = f' nonce="{nonce}"' if nonce else ''
        script_tag = f'<script id="mitm-inject"{nonce_attr}>\n{script_code}\n</script>'

        # Insert before </body>
        body_close = html.lower().rfind('</body>')
        if body_close >= 0:
            modified = html[:body_close] + '\n' + script_tag + '\n' + html[body_close:]
        else:
            modified = html + '\n' + script_tag

        headers_to_add = {
            'x-mitm-inject'       : 'true',
            'x-mitm-inject-domain': domain,
            'x-mitm-inject-nonce' : 'yes' if nonce else 'no',
            'x-mitm-inject-size'  : str(len(script_code)),
        }

        headers_to_remove = self.get_csp_headers_to_remove()

        print(f"    💉 Injected filter into {host} ({domain}, {len(script_code):,} chars"
              f"{', nonce: ' + nonce[:12] + '...' if nonce else ', no nonce'})")

        return (modified, headers_to_add, headers_to_remove)