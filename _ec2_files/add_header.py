"""Add custom header to all requests and responses"""

x_custom_header = "MGraph-AI-Proxy v0.1"

def request(flow):
    """
    This function is called for every request
    """
    # Add a custom header to all requests
    flow.request.headers["X-Custom-Header"] = x_custom_header

    # You can add multiple headers
    flow.request.headers["X-Proxy-Time"] = "2025"

    # Conditional headers based on host
    if "httpbin.org" in flow.request.host:
        flow.request.headers["X-Special-Site"] = "httpbin-detected"

    # Log what we're doing (visible in mitmproxy console)
    print(f"Added headers to request: {flow.request.host}{flow.request.path}")


def response(flow):
    """
    This function is called for every response
    """
    # Add custom headers to all responses
    flow.response.headers["X-Proxied-By"] = x_custom_header
    flow.response.headers["X-Response-Time"] = "2025"

    # Add CORS headers if needed
    flow.response.headers["Access-Control-Expose-Headers"] = "X-Proxied-By, X-Response-Time"

    # Conditional response headers
    if "httpbin.org" in flow.request.host:
        flow.response.headers["X-Special-Response"] = "httpbin-response-modified"

    # Log what we're doing
    print(f"Added headers to response: {flow.request.host}{flow.request.path} - Status: {flow.response.status_code}")