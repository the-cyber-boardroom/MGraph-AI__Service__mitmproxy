from http.cookies                                                                    import SimpleCookie
from osbot_utils.type_safe.Type_Safe                                                 import Type_Safe
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Request_Data           import Schema__Proxy__Request_Data
from datetime                                                                        import datetime
from typing                                                                          import Dict, Optional

class Proxy__Content__Service(Type_Safe):                            # Content processing service

    def parse_cookies(self, headers : Dict[str, str]                 # Parse cookies using Python's SimpleCookie
                      ) -> Dict[str, str]:
        cookie_header = headers.get('cookie') or headers.get('Cookie')
        if not cookie_header:
            return {}

        cookie = SimpleCookie()
        cookie.load(cookie_header)

        return {key: morsel.value for key, morsel in cookie.items()}

    def check_cached_response(self, request_data  : Schema__Proxy__Request_Data,  # Check if should return cached response
                                    total_requests: int
                              ) -> Optional[Dict]:
        cookies = self.parse_cookies(request_data.headers)

        if cookies.get('mitm-mode') == 'cache_test':
            try:
                cached_html = """
               <!DOCTYPE html>
                <html>
                <head>
                    <title>CACHED RESPONSE TEST</title>
                </head>
                <body style="background: #00ff00; padding: 40px; font-family: monospace;">
                    <h1>🎯 SUCCESS! This is a CACHED response</h1>
                    <p>This HTML was returned directly from FastAPI without hitting the upstream server!</p>
                    <ul>                                                
                        <li>Original Path: """ + (request_data.original_path or "N/A") + """</li>
                        <li>Path: """ + str(f"{request_data.path}") + """ </li>
                        <li>Request Count: """ + str(total_requests) + """</li>
                    </ul>
                </body>
                </html>
                """

                return {
                    "status_code": 200,
                    "body": cached_html,
                    "headers": {
                        "content-type": "text/html; charset=utf-8",
                        "X-Cache-Source": "fastapi-test-cache",
                        "X-Cache-Timestamp": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                print(f"Error creating cached response: {e}")
                return None

        return None