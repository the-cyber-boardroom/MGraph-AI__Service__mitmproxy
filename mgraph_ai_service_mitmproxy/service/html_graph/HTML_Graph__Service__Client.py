# ═══════════════════════════════════════════════════════════════════════════════
# HTML Graph Service Client
# HTTP client for store/load operations against HTML Graph API
# Supports TestClient injection for mock-free testing
# ═══════════════════════════════════════════════════════════════════════════════

from urllib.parse                                                                            import urlparse
from typing                                                                                  import Any
from mgraph_ai_service_cache_client.schemas.cache.safe_str.Safe_Str__Cache__Namespace        import Safe_Str__Cache__Namespace
from osbot_utils.type_safe.Type_Safe                                                         import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_Float                                        import Safe_Float
from osbot_utils.type_safe.primitives.core.Safe_UInt                                         import Safe_UInt
from osbot_utils.type_safe.primitives.domains.files.safe_str.Safe_Str__File__Path import Safe_Str__File__Path
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html                    import Safe_Str__Html
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Url                     import Safe_Str__Url
from osbot_utils.type_safe.type_safe_core.decorators.type_safe                               import type_safe
from osbot_utils.utils.Env                                                                   import get_env
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.consts__html_graph               import (ENV_VAR__HTML_GRAPH__BASE_URL  ,
                                                                                                     ENV_VAR__HTML_GRAPH__NAMESPACE ,
                                                                                                     ENV_VAR__HTML_GRAPH__KEY_NAME  ,
                                                                                                     ENV_VAR__HTML_GRAPH__KEY_VALUE ,
                                                                                                     DEFAULT__HTML_GRAPH__NAMESPACE ,
                                                                                                     DEFAULT__HTML_GRAPH__TIMEOUT   )
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Store_Result import Schema__HTML_Graph__Store_Result
from mgraph_ai_service_mitmproxy.service.html_graph.schemas.Schema__HTML_Graph__Load_Result  import Schema__HTML_Graph__Load_Result


class HTML_Graph__Service__Client(Type_Safe):                                       # HTTP client for HTML Graph API
    base_url     : Safe_Str__Url                                                    # API base URL
    namespace    : Safe_Str__Cache__Namespace   = DEFAULT__HTML_GRAPH__NAMESPACE    # Cache namespace
    timeout      : Safe_Float   = DEFAULT__HTML_GRAPH__TIMEOUT                      # Request timeout seconds
    test_client  : Any          = None                                              # Optional TestClient for testing

    def setup(self) -> 'HTML_Graph__Service__Client':                           # Configure from environment
        base_url_env  = get_env(ENV_VAR__HTML_GRAPH__BASE_URL)
        namespace_env = get_env(ENV_VAR__HTML_GRAPH__NAMESPACE)

        if base_url_env:
            self.base_url = base_url_env
        if namespace_env:
            self.namespace = namespace_env

        return self

    def set_test_client(self, test_client: Any                                  # Inject TestClient for testing
                         ) -> 'HTML_Graph__Service__Client':
        self.test_client = test_client
        return self

    def get_auth_headers(self) -> dict:                                         # Build authentication headers
        key_name  = get_env(ENV_VAR__HTML_GRAPH__KEY_NAME)
        key_value = get_env(ENV_VAR__HTML_GRAPH__KEY_VALUE)

        headers = {"Content-Type": "application/json"}

        if key_name and key_value:
            headers[key_name] = key_value

        return headers

    # todo: refactor this to use the Url_to_Cache_Key class
    @type_safe
    def url_to_cache_key(self, url: Safe_Str__Url) -> Safe_Str__File__Path:            # Convert URL to cache key
        parsed = urlparse(url)
        domain = parsed.netloc

        if not domain:                                                                  # todo: see if there is a way to get here, since the Safe_Str__Url should be making sure there is a domain value
            return "unknown/root"

        path = parsed.path.strip('/')                                                   # todo: look at adding this helper methods to the Safe_Str__Url

        if not path:
            path = "root"

        return f"{domain}/{path}"

    def make_post_request(self, endpoint  : Safe_Str__Url,                      # Make POST request via requests or TestClient
                                json_data : dict
                           ) -> tuple:                                          # Returns (status_code, response_data)
        headers = self.get_auth_headers()

        if self.test_client is not None:                                        # Use TestClient for testing
            response    = self.test_client.post(str(endpoint), json=json_data, headers=headers)
            status_code = response.status_code
            try:
                data = response.json()
            except:
                data = {}
            return (status_code, data)
        else:                                                                   # Use requests for production
            import requests
            full_url = f"{self.base_url}{endpoint}"
            response = requests.post(url     = full_url            ,
                                     headers = headers             ,
                                     json    = json_data           ,
                                     timeout = float(self.timeout) )
            try:
                data = response.json()
            except:
                data = {}
            return (response.status_code, data)

    @type_safe
    def store_html(self, url  : Safe_Str__Url,                                  # Store HTML content by URL
                         html : Safe_Str__Html
                    ) -> Schema__HTML_Graph__Store_Result:                      # Store operation result

        cache_key   = self.url_to_cache_key(url)
        endpoint    = f"/flet-html-domain/html/store/{self.namespace}/key/{cache_key}"
        html_length = Safe_UInt(len(str(html)))

        print(f"    📦 HTML Graph STORE: {cache_key}")

        try:
            status_code, data = self.make_post_request(endpoint, {"html": html})

            if status_code == 200:
                print(f"    ✅ Stored {data.get('char_count', 0)} chars")
                return Schema__HTML_Graph__Store_Result(success    = data.get("success", True)             ,
                                                        cache_id   = data.get("cache_id", "")              ,
                                                        cache_key  = data.get("cache_key", str(cache_key)) ,
                                                        cache_hash = data.get("cache_hash", "")            ,
                                                        char_count = data.get("char_count", html_length)   )
            else:
                error_msg = f"HTTP {status_code}"
                print(f"    ⚠️  Store failed: {error_msg}")
                return Schema__HTML_Graph__Store_Result(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"    ⚠️  {error_msg}")
            return Schema__HTML_Graph__Store_Result(success=False, error=error_msg)

    @type_safe
    def load_html(self, url: Safe_Str__Url) -> Schema__HTML_Graph__Load_Result:      # Load HTML content by URL

        cache_key = self.url_to_cache_key(url)
        endpoint  = f"/flet-html-domain/html/load/{self.namespace}/key/{cache_key}"

        print(f"    🔍 HTML Graph LOAD: {cache_key}")

        try:
            status_code, data = self.make_post_request(endpoint, {})

            if status_code == 200:
                found = data.get("found", False)

                if found:
                    print(f"    ✅ Cache HIT: {data.get('char_count', 0)} chars")
                    return Schema__HTML_Graph__Load_Result(success    = True                                   ,
                                                           found      = True                                   ,
                                                           html       = data.get("html", "")                   ,
                                                           cache_id   = data.get("cache_id", "")               ,
                                                           cache_key  = data.get("cache_key", str(cache_key))  ,
                                                           char_count = data.get("char_count", 0)              )
                else:
                    print(f"    ❌ Cache MISS")
                    return Schema__HTML_Graph__Load_Result(success=True, found=False)
            else:
                error_msg = f"HTTP {status_code}"
                print(f"    ⚠️  Load failed: {error_msg}")
                return Schema__HTML_Graph__Load_Result(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"    ⚠️  {error_msg}")
            return Schema__HTML_Graph__Load_Result(success=False, error=error_msg)