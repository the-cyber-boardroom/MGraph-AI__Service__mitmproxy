"""
FastAPI Interceptor for Mitmproxy
Proper async implementation that works with mitmproxy's event loop
"""

from mitmproxy import http
import json
import asyncio
from datetime import datetime
import os

# For HTTP calls, we'll use mitmproxy's built-in async support with urllib
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

# Configuration - will be set via environment or config
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://host.docker.internal:10016")
REQUEST_ENDPOINT = "/proxy/process-request"
RESPONSE_ENDPOINT = "/proxy/process-response"
TIMEOUT = 0.5  # Reduced timeout for faster fallback
FASTAPI_API_KEY = os.getenv("FASTAPI_API_KEY", "your-secret-key-here")

# Stats tracking
request_count = 0
response_count = 0
errors_count = 0

# Thread pool for non-blocking HTTP calls
executor = ThreadPoolExecutor(max_workers=10)

def call_fastapi_sync(endpoint: str, data: dict) -> dict:
    """Synchronous FastAPI call for use in thread pool"""
    url = f"{FASTAPI_BASE_URL}{endpoint}"

    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers={
            'Content-Type': 'application/json',
            'x-api-key': FASTAPI_API_KEY  # Add this line
        })

        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            if response.status == 200:
                response_data = response.read()
                return json.loads(response_data)
    except Exception as e:
        # Silent fail - we'll use fallback
        return None


async def call_fastapi_async(endpoint: str, data: dict) -> dict:
    """Async wrapper that runs sync call in thread pool"""
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(executor, call_fastapi_sync, endpoint, data)
        return result
    except Exception:
        return None


async def request(flow: http.HTTPFlow) -> None:
    """
    Async request handler - mitmproxy will await this
    """
    global request_count, errors_count
    request_count += 1

    print(f"[REQUEST #{request_count}] {flow.request.method} {flow.request.pretty_host}{flow.request.path}")

    # Always add basic tracking headers immediately
    flow.request.headers["X-Proxy-Request-Count"] = str(request_count)

    # Prepare request data for FastAPI
    request_data = {
        "method": flow.request.method,
        "host": flow.request.pretty_host,
        "path": flow.request.path,
        "headers": dict(flow.request.headers),
        "stats": {
            "request_count": request_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    # Call FastAPI service asynchronously
    modifications = await call_fastapi_async(REQUEST_ENDPOINT, request_data)

    if modifications:
        # Apply header modifications from FastAPI
        if "headers_to_add" in modifications:
            for key, value in modifications["headers_to_add"].items():
                flow.request.headers[key] = str(value)

        if "headers_to_remove" in modifications:
            for key in modifications["headers_to_remove"]:
                if key in flow.request.headers:
                    del flow.request.headers[key]

        # Check if request should be blocked
        if modifications.get("block_request"):
            flow.response = http.Response.make(
                modifications.get("block_status", 403),
                modifications.get("block_message", "Blocked by proxy").encode(),
                {"Content-Type": "text/plain"}
            )
            print(f"  ! Blocked request")

        flow.request.headers["X-Proxy-Status"] = "fastapi-connected"
        print(f"  ✓ Modified via FastAPI")
    else:
        # Fallback - FastAPI unavailable
        flow.request.headers["X-Proxy-Status"] = "fastapi-unavailable"
        flow.request.headers["X-Proxy-Fallback"] = "true"
        errors_count += 1
        print(f"  ⚠ Fallback mode")


async def response(flow: http.HTTPFlow) -> None:
    """
    Async response handler - mitmproxy will await this
    """
    global response_count, errors_count
    response_count += 1

    print(f"[RESPONSE #{response_count}] {flow.response.status_code} from {flow.request.pretty_host}")

    # Always add basic tracking headers immediately
    flow.response.headers["X-Proxy-Response-Count"] = str(response_count)

    # Prepare response data for FastAPI
    response_data = {
        "request": {
            "method": flow.request.method,
            "host": flow.request.pretty_host,
            "path": flow.request.path,
        },
        "response": {
            "status_code": flow.response.status_code,
            "headers": dict(flow.response.headers),
        },
        "stats": {
            "response_count": response_count,
            "request_count": request_count,
            "errors_count": errors_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    # Call FastAPI service asynchronously
    modifications = await call_fastapi_async(RESPONSE_ENDPOINT, response_data)

    if modifications:
        # Apply header modifications from FastAPI
        if "headers_to_add" in modifications:
            for key, value in modifications["headers_to_add"].items():
                flow.response.headers[key] = str(value)

        if "headers_to_remove" in modifications:
            for key in modifications["headers_to_remove"]:
                if key in flow.response.headers:
                    del flow.response.headers[key]

        # Add statistics headers
        if modifications.get("include_stats"):
            stats = modifications.get("stats", {})
            flow.response.headers["X-Proxy-Stats"] = json.dumps(stats)

        flow.response.headers["X-Proxy-Status"] = "fastapi-connected"
        print(f"  ✓ Modified via FastAPI")
    else:
        # Fallback - FastAPI unavailable
        flow.response.headers["X-Proxy-Status"] = "fastapi-unavailable"
        flow.response.headers["X-Proxy-Fallback"] = "true"
        errors_count += 1
        print(f"  ⚠ Fallback mode")


def done():
    """Cleanup when mitmproxy shuts down"""
    executor.shutdown(wait=False)
    print("FastAPI Interceptor shutting down")


print("=" * 60)
print("FastAPI Interceptor Loaded! (Async Version)")
print(f"Delegating to: {FASTAPI_BASE_URL}")
print(f"Timeout: {TIMEOUT}s, Workers: 10")
print("=" * 60)