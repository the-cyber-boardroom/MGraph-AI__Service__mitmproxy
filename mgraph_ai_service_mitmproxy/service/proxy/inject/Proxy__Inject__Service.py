"""Proxy Inject Service — injects client-side scripts into HTML responses.

When mitm-mode=inject, this service checks the target domain and injects
the appropriate filter script. Handles CSP nonce extraction so the injected
script is allowed by the page's Content-Security-Policy.

No cache. No S3. No pre-processing. One string insertion per response.
"""

import re
from urllib.parse                                                    import urlparse
from osbot_utils.type_safe.Type_Safe                                 import Type_Safe
from mgraph_ai_service_mitmproxy.service.proxy.inject.inject_scripts import BBC_FILTER_SCRIPT


# Domain → script mapping
# Add new sites here as they're developed
INJECT_SCRIPTS = {
    'bbc.co.uk'     : ('bbc-filter', BBC_FILTER_SCRIPT),
    'bbc.com'       : ('bbc-filter', BBC_FILTER_SCRIPT),
    'bbci.co.uk'    : ('bbc-filter', BBC_FILTER_SCRIPT),
}

# Regex to extract nonce from existing <script nonce="..."> tags
NONCE_PATTERN = re.compile(r'<script[^>]+nonce=["\']([^"\']+)["\']', re.IGNORECASE)


class Proxy__Inject__Service(Type_Safe):

    def match_domain(self, host: str) -> tuple:                       # Check if host matches any configured domain
        """Returns (script_name, script_code) or (None, None).

        Matches against the domain suffix — so 'www.bbc.co.uk',
        'news.bbc.co.uk', 'sport.bbc.co.uk' all match 'bbc.co.uk'.
        """
        host = (host or '').lower().strip()

        for domain, (name, script) in INJECT_SCRIPTS.items():
            if host == domain or host.endswith('.' + domain):
                return (name, script)

        return (None, None)

    def extract_nonce(self, html: str) -> str:                        # Extract CSP nonce from existing script tags
        """Find the nonce value used by the page's own scripts.

        BBC uses: <script nonce="7viV1sk5kLAx..." ...>
        We extract that nonce and add it to our injected script tag
        so it passes the Content-Security-Policy check.
        """
        match = NONCE_PATTERN.search(html)
        if match:
            return match.group(1)
        return ''

    def strip_csp_from_headers(self, headers: dict) -> dict:          # Build headers that neutralise CSP for inject mode
        """Return headers to remove that would block our injected script.

        This is the fallback — if nonce extraction fails or the CSP
        is configured in a way that still blocks us, removing the CSP
        header ensures the script runs.

        Since we're already modifying the page (injecting a script),
        CSP is incompatible with the proxy's purpose in inject mode.
        """
        headers_to_remove = []
        for header_name in ['content-security-policy', 'Content-Security-Policy',
                            'content-security-policy-report-only', 'Content-Security-Policy-Report-Only']:
            headers_to_remove.append(header_name)
        return headers_to_remove

    def inject_script_into_html(self, html       : str,              # Original HTML response body
                                      target_url : str = '',         # URL being proxied
                                      host       : str = ''          # Request host (e.g. www.bbc.co.uk)
                                ) -> tuple:                          # (modified_html, headers_to_add, headers_to_remove) or (None, {}, [])
        if not html:
            return (None, {}, [])

        # Extract host from target_url if not provided directly
        if not host and target_url:
            host = urlparse(target_url).netloc

        # Check if this domain has a script
        script_name, script_code = self.match_domain(host)

        if not script_code:
            return (None, {}, [])                                     # Not a matching domain — pass through

        # Extract nonce from existing page scripts
        nonce = self.extract_nonce(html)
        nonce_attr = f' nonce="{nonce}"' if nonce else ''

        script_tag = f'<script id="mitm-inject"{nonce_attr}>\n{script_code}\n</script>'

        # Insert before </body>
        body_close = html.lower().rfind('</body>')
        if body_close >= 0:
            modified = html[:body_close] + '\n' + script_tag + '\n' + html[body_close:]
        else:
            modified = html + '\n' + script_tag

        headers_to_add = { 'x-mitm-inject'       : 'true'                ,
                           'x-mitm-inject-script' : script_name           ,
                           'x-mitm-inject-domain' : host                  ,
                           'x-mitm-inject-nonce'  : 'yes' if nonce else 'no',
                           'x-mitm-inject-size'   : str(len(script_code)) }

        # Also strip CSP headers as fallback (belt and suspenders)
        headers_to_remove = self.strip_csp_from_headers(html)

        if nonce:
            print(f"    💉 Injected {script_name} into {host} (nonce: {nonce[:12]}...)")
        else:
            print(f"    💉 Injected {script_name} into {host} (no nonce found, stripping CSP)")

        return (modified, headers_to_add, headers_to_remove)
