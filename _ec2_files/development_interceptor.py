"""
Development Interceptor Script for Mitmproxy
Created for testing and development purposes
"""

from mitmproxy import http

# Global state for development
request_counter = 0
response_counter = 0

def request(flow: http.HTTPFlow) -> None:
    """
    Called for each HTTP request
    """
    global request_counter
    request_counter += 1
    
    # Add development headers
    flow.request.headers["X-Dev-Request-Count"] = str(request_counter)
    flow.request.headers["X-Dev-Interceptor"] = "development-v1"
    
    # Log request details
    print(f"[REQUEST #{request_counter}] {flow.request.method} {flow.request.pretty_host}{flow.request.path}")
    
    # Example: Modify requests to specific hosts
    if "httpbin.org" in flow.request.pretty_host:
        flow.request.headers["X-Special-Site"] = "httpbin-intercepted"
        print(f"  → Added special header for httpbin.org")
    
    # Example: Block requests to certain paths
    if "/blocked" in flow.request.path:
        flow.response = http.Response.make(
            403,  # status code
            b"Blocked by development interceptor",  # content
            {"Content-Type": "text/plain"}
        )
        print(f"  → Blocked request to {flow.request.path}")
    
    # Example: Redirect requests
    if flow.request.path == "/redirect-me":
        flow.request.host = "httpbin.org"
        flow.request.path = "/get"
        print(f"  → Redirected to httpbin.org/get")


def response(flow: http.HTTPFlow) -> None:
    """
    Called for each HTTP response
    """
    global response_counter
    response_counter += 1
    
    # Add development headers to response
    flow.response.headers["X-Dev-Response-Count"] = str(response_counter)
    flow.response.headers["X-Dev-Modified"] = "true"
    
    # Log response details
    print(f"[RESPONSE #{response_counter}] {flow.response.status_code} from {flow.request.pretty_host}")
    
    # Example: Modify JSON responses
    if "application/json" in flow.response.headers.get("content-type", ""):
        try:
            import json
            data = json.loads(flow.response.text)
            data["_intercepted"] = True
            data["_interceptor_version"] = "development-v1"
            flow.response.text = json.dumps(data)
            print(f"  → Modified JSON response")
        except:
            pass  # Not valid JSON or other error
    
    # Example: Add CORS headers
    if "httpbin.org" in flow.request.pretty_host:
        flow.response.headers["Access-Control-Allow-Origin"] = "*"
        flow.response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        print(f"  → Added CORS headers")
    
    # Example: Cache control
    if flow.request.path.endswith((".jpg", ".png", ".gif")):
        flow.response.headers["Cache-Control"] = "max-age=3600"
        print(f"  → Added cache control for image")


def websocket_message(flow):
    """
    Called for WebSocket messages (if needed)
    """
    # Get the latest message
    message = flow.messages[-1]
    
    # Log WebSocket activity
    print(f"[WEBSOCKET] {'Sent' if message.from_client else 'Received'}: {message.content[:100]}")
    
    # Modify messages if needed
    if message.from_client and "ping" in message.content:
        message.content = message.content.replace("ping", "pong")
        print(f"  → Modified ping to pong")


# Additional hooks available:
# - clientconnect, clientdisconnect
# - serverconnect, serverdisconnect  
# - tcp_message
# - error

print("=" * 60)
print("Development Interceptor Loaded!")
print(f"Monitoring requests and responses...")
print("=" * 60)
