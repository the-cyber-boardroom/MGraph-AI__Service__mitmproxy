#!/bin/bash
#
# Builds and starts a local mitmproxy Docker container wired up to the local
# FastAPI service (started separately with ./scripts/run-locally.sh)
#
# Usage:
#   ./scripts/run-mitmproxy-locally.sh           # build + start the container
#   ./scripts/run-mitmproxy-locally.sh cleanup   # stop and remove it
#
# Once running:
#   - HTTP/HTTPS proxy : localhost:8080  (auth: PROXY_AUTH_USER / PROXY_AUTH_PASS from .build.env)
#   - mitmweb UI       : localhost:8081
#   - CA certificate   : browse to http://mitm.it via the proxy to install it in Firefox

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

BUILD_ENV_FILE="tests/integration/service/mitmproxy/.build.env"
DEV_TEST_FILE="tests/integration/service/mitmproxy/test_Mitmproxy__Create__Docker_Container__Development.py"
DEV_TEST_CLASS="test_Mitmproxy__Create__Docker_Container__Development"

if [ "$1" == "cleanup" ]; then
    echo "→ Stopping and removing the development mitmproxy container..."
    pytest "${DEV_TEST_FILE}::${DEV_TEST_CLASS}::test_cleanup_development_containers" -s
    exit 0
fi

if ! command -v docker > /dev/null 2>&1; then
    echo "❌ docker not found - install Docker and make sure it is running"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "❌ docker daemon is not running - start Docker first"
    exit 1
fi

if [ ! -f "$BUILD_ENV_FILE" ]; then
    echo "❌ $BUILD_ENV_FILE not found"
    echo "   Create it from the example and edit the values:"
    echo "       cp ${BUILD_ENV_FILE}.example ${BUILD_ENV_FILE}"
    exit 1
fi

echo "→ Building and starting the mitmproxy container (proxy: localhost:8080, web UI: localhost:8081)..."
pytest "${DEV_TEST_FILE}::${DEV_TEST_CLASS}::test_create_persistent_container_for_development" -s

echo ""
echo "============================================================"
echo "Firefox setup"
echo "============================================================"
echo "1. Settings → Network Settings → Manual proxy configuration"
echo "     HTTP Proxy: localhost   Port: 8080"
echo "     ✓ Also use this proxy for HTTPS"
echo "2. When prompted, log in with PROXY_AUTH_USER / PROXY_AUTH_PASS from $BUILD_ENV_FILE"
echo "3. Install the mitmproxy CA: browse to http://mitm.it and follow the Firefox steps"
echo "4. Make sure the FastAPI service is running: ./scripts/run-locally.sh"
echo "5. Enable a transformation via cookie, e.g. mitm-mode=hashes"
echo "   (see http://localhost:10016/docs and the console at http://localhost:10016/console)"
