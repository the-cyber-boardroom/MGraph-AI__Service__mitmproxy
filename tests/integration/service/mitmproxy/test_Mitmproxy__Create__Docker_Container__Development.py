import pytest
from unittest import TestCase
from osbot_docker.apis.API_Docker import API_Docker
from osbot_utils.utils.Dev import pprint
from osbot_utils.utils.Files import path_combine, file_exists, file_write
import mgraph_ai_service_mitmproxy
from mgraph_ai_service_mitmproxy.service.mitmproxy.Mitmproxy__Create__Docker_Container import Mitmproxy__Create__Docker_Container


class test_Mitmproxy__Create__Docker_Container__Development(TestCase):
    """
    Development test for creating a persistent mitmproxy container.
    This test creates a container that persists after test completion for development purposes.

    To run this test:
        pytest tests/integration/service/mitmproxy/test_Mitmproxy__Create__Docker_Container__Development::test_create_persistent_container_for_development -s

    To clean up containers created by this test:
        pytest tests/integration/service/mitmproxy/test_Mitmproxy__Create__Docker_Container__Development::test_Mitmproxy__Create__Docker_Container__Development::test_cleanup_development_containers -s
    """

    DEVELOPMENT_IMAGE_NAME     = "mitmproxy-dev-persistent"
    DEVELOPMENT_CONTAINER_NAME = "mitmproxy-dev-persistent"
    DEVELOPMENT_PROXY_PORT     = 8080
    DEVELOPMENT_WEB_PORT       = 8081

    @classmethod
    def setUpClass(cls):
        #pytest.skip("Manual execution only - remove this skip to run")
        cls.api_docker = API_Docker()

    def test_create_persistent_container_for_development(self):
        """
        Creates a persistent mitmproxy container for development.
        Container will continue running after test completes.
        """
        print("\n" + "="*60)
        print("Creating Persistent Mitmproxy Container for Development")
        print("="*60)

        # Setup paths for existing certificates
        certs_backup_path = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy-certs-backup.tar.gz')
        cert_pem_path     = path_combine(mgraph_ai_service_mitmproxy.path,'../_ec2_files/mitmproxy-ca-cert.pem')

        # Verify certificates exist
        if file_exists(certs_backup_path):
            print(f"✓ Found certificate backup: {certs_backup_path}")
        if file_exists(cert_pem_path):
            print(f"✓ Found certificate PEM: {cert_pem_path}")

        # Create mitmproxy instance with fixed name for easy identification
        mitmproxy_docker = Mitmproxy__Create__Docker_Container(build_image_name  = self.DEVELOPMENT_IMAGE_NAME    ,
                                                               container_name    = self.DEVELOPMENT_CONTAINER_NAME,
                                                               proxy_port        = self.DEVELOPMENT_PROXY_PORT    ,
                                                               web_port          = self.DEVELOPMENT_WEB_PORT      ,
                                                               certificates_path = certs_backup_path              )

        # Check if container already exists
        existing_containers = mitmproxy_docker.api_docker.containers_all__by_name()
        if self.DEVELOPMENT_CONTAINER_NAME in existing_containers:
            print(f"\n⚠️  Container '{self.DEVELOPMENT_CONTAINER_NAME}' already exists!")
            container = existing_containers[self.DEVELOPMENT_CONTAINER_NAME]

            if container.status() == 'running':
                print(f"✓ Container is already running")
            else:
                print(f"→ Starting existing container...")
                container.start()
                print(f"✓ Container started")

            mitmproxy_docker.container = container
        else:
            # Create new container with custom script AND certificates
            print("\n→ Creating container with certificates...")
            container = mitmproxy_docker.create_container(with_custom_script=True,
                                                          with_certificates=True)

            assert container is not None
            print(f"✓ Container created: {container.short_id()}")

            print("\n→ Starting container...")
            started = mitmproxy_docker.start(wait_for_ready=True)
            assert started is True
            print("✓ Container started successfully with your existing certificates!")

        # Display connection information
        print("\n" + "="*60)
        print("Container Information")
        print("="*60)
        print(f"Name:        {self.DEVELOPMENT_CONTAINER_NAME}")
        print(f"Status:      {mitmproxy_docker.container.status()}")
        print(f"Container ID: {mitmproxy_docker.container.short_id()}")
        print(f"\nProxy Endpoints:")
        print(f"  HTTP/HTTPS Proxy: http://localhost:{self.DEVELOPMENT_PROXY_PORT}")
        print(f"  Web Interface:    http://localhost:{self.DEVELOPMENT_WEB_PORT}")

        # Test proxy connection
        print("\n→ Testing proxy connection...")
        if mitmproxy_docker.test_proxy_connection():
            print("✓ Proxy is working correctly with custom headers!")
        else:
            print("⚠️  Proxy is running but custom headers might not be configured")

        # Show sample curl commands
        print("\n" + "="*60)
        print("Test Commands")
        print("="*60)
        print("\n1. Test proxy with curl:")
        print(f"   curl -x http://localhost:{self.DEVELOPMENT_PROXY_PORT} https://httpbin.org/headers")

        print("\n2. Test with Python requests:")
        print(f"""\
import requests
proxies = {{
   'http': 'http://localhost:{self.DEVELOPMENT_PROXY_PORT}',
   'https': 'http://localhost:{self.DEVELOPMENT_PROXY_PORT}'
}}
response = requests.get('https://httpbin.org/headers', proxies=proxies, verify=False)
print(response.json())""")

        print("\n3. View mitmproxy web interface:")
        print(f"   Open browser: http://localhost:{self.DEVELOPMENT_WEB_PORT}")

        print("\n4. View container logs:")
        print(f"   docker logs {self.DEVELOPMENT_CONTAINER_NAME}")

        print("\n5. Execute commands in container:")
        print(f"   docker exec -it {self.DEVELOPMENT_CONTAINER_NAME} /bin/sh")

        # Create development script template
        self._create_development_script_template()

        print("\n" + "="*60)
        print("✓ Development container is ready!")
        print(f"⚠️  Container '{self.DEVELOPMENT_CONTAINER_NAME}' will continue running")
        print("   To stop: Run test_cleanup_development_containers")
        print("="*60 + "\n")

    def test_cleanup_development_containers(self):
        """
        Cleans up development containers created by this test.
        Run this when you're done with development.
        """
        print("\n" + "="*60)
        print("Cleaning Up Development Containers")
        print("="*60)

        mitmproxy_docker = Mitmproxy__Create__Docker_Container()

        # Find all development containers
        dev_containers = []
        for container in mitmproxy_docker.api_docker.containers_all():
            if container.name() == self.DEVELOPMENT_CONTAINER_NAME or \
               container.name().startswith('mitmproxy-dev-'):
                dev_containers.append(container)

        if not dev_containers:
            print("✓ No development containers found to clean up")
            return

        print(f"\nFound {len(dev_containers)} development container(s):")
        for container in dev_containers:
            print(f"  - {container.name()} ({container.short_id()}) - Status: {container.status()}")

        # Clean up each container
        for container in dev_containers:
            print(f"\n→ Cleaning up {container.name()}...")

            if container.status() == 'running':
                print("  → Stopping container...")
                container.stop()
                print("  ✓ Stopped")

            print("  → Removing container...")
            container.delete()
            print("  ✓ Removed")

        # Clean up custom images
        print("\n→ Cleaning up custom mitmproxy images...")
        api_docker = API_Docker()
        cleaned_images = []

        for image in api_docker.images():
            # Check for both custom and dev images
            if (image.image_name.startswith('mitmproxy-custom-') or
                image.image_name.startswith('mitmproxy-dev-') or
                image.image_name == self.DEVELOPMENT_IMAGE_NAME):
                print(f"  → Removing image: {image.image_name}")
                image.delete()
                cleaned_images.append(image.image_name)
                print(f"  ✓ Removed")

        if cleaned_images:
            print(f"\n✓ Cleaned up {len(cleaned_images)} custom image(s)")
        else:
            print("\n✓ No custom images to clean up")

        print("\n" + "="*60)
        print("✓ Cleanup complete!")
        print("="*60 + "\n")

    def test_show_running_mitmproxy_containers(self):
        """
        Shows all running mitmproxy containers for debugging.
        """
        print("\n" + "="*60)
        print("Running Mitmproxy Containers")
        print("="*60)

        mitmproxy_docker = Mitmproxy__Create__Docker_Container()
        containers = mitmproxy_docker.containers_all_mitmproxy()

        if not containers:
            print("\n✓ No mitmproxy containers are currently running")
        else:
            print(f"\nFound {len(containers)} mitmproxy container(s):")
            for container in containers:
                info = container.info()
                ports = container.ports()

                print(f"\n  Container: {container.name()}")
                print(f"    ID:     {container.short_id()}")
                print(f"    Status: {container.status()}")
                print(f"    Image:  {info.get('Config', {}).get('Image', 'unknown')}")

                if ports:
                    print(f"    Ports:")
                    for container_port, host_ports in ports.items():
                        if host_ports:
                            for host_port in host_ports:
                                print(f"      - {container_port} → localhost:{host_port.get('HostPort')}")

                # Show recent logs
                logs = container.logs(tail=5)
                if logs:
                    print(f"    Recent logs:")
                    for line in logs.split('\n')[-5:]:
                        if line.strip():
                            print(f"      {line[:100]}")


    def _create_development_script_template(self):
        """
        Creates a template script for developing mitmproxy interceptors.
        """
        script_path = path_combine(
            mgraph_ai_service_mitmproxy.path,
            '../_ec2_files/development_interceptor.py'
        )

        if file_exists(script_path):
            print(f"\n✓ Development script already exists: {script_path}")
            return

        template = '''"""
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
'''

        file_write(script_path, template)
        print(f"\n✓ Created development script template: {script_path}")
        print("  You can now modify this script and reload it in the container")


    def test_create_container(self):
        self.test_cleanup()
        self.test_create_persistent_container_for_development()


    def test_cleanup(self):
        try:
            self.test_cleanup_development_containers()
        except:
            pass
        self.test_cleanup_development_containers()