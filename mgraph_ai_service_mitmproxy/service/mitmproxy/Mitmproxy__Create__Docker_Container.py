import mgraph_ai_service_mitmproxy
from osbot_docker.apis.API_Docker                                                import API_Docker
from osbot_docker.apis.Docker_Container                                          import Docker_Container
from osbot_docker.apis.Docker_Image                                              import Docker_Image
from osbot_utils.type_safe.Type_Safe                                             import Type_Safe
from osbot_utils.type_safe.primitives.safe_uint.Safe_UInt__Port                  import Safe_UInt__Port
from osbot_utils.utils.Files                                                     import path_combine, file_exists, file_create, temp_folder
from osbot_utils.utils.Misc                                                      import random_string_short, wait_for
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Container_Name import Safe_Str__Docker__Container_Name
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Image_Name     import Safe_Str__Docker__Image_Name
from mgraph_ai_service_mitmproxy.schemas.docker.Safe_Str__Docker__Tag            import Safe_Str__Docker__Tag


class Mitmproxy__Create__Docker_Container(Type_Safe):                    # Create and manage mitmproxy Docker containers
    api_docker       : API_Docker
    container        : Docker_Container                  = None
    container_name   : Safe_Str__Docker__Container_Name  = None
    image_name       : Safe_Str__Docker__Image_Name      = "mitmproxy/mitmproxy"
    build_image_name : Safe_Str__Docker__Image_Name      = None
    image_tag        : Safe_Str__Docker__Tag             = "latest"
    proxy_port       : Safe_UInt__Port                   = 8080
    web_port         : Safe_UInt__Port                   = 8081
    certificates_path: str                               = None             # Path to certificates tar.gz or directory

    # def __enter__(self):
    #     self.setup()
    #     self.start()
    #     return self
    #
    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.stop()
    #     return False

    def __init__(self, **kwargs):                                                     # Initialize Docker API and container name
        super().__init__(**kwargs)
        if not self.container_name:
            self.container_name = f"mitmproxy-{random_string_short()}"
        if not self.build_image_name:
            self.build_image_name = f"mitmproxy-custom-{random_string_short()}"


    def build_custom_image(self, include_certificates=False):
        # Create temp directory for Docker build context
        build_context = temp_folder()

        # Path to add_header.py
        add_header_path = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/add_header.py')

        if not file_exists(add_header_path):
            return False

        # Copy add_header.py to build context
        import shutil
        shutil.copy(add_header_path, path_combine(build_context, 'add_header.py'))

        # Handle certificates if requested
        cert_commands = ""
        if include_certificates and self.certificates_path:
            if file_exists(self.certificates_path):
                # Copy certificates to build context
                if self.certificates_path.endswith('.tar.gz'):
                    shutil.copy(self.certificates_path, path_combine(build_context, 'mitmproxy-certs-backup.tar.gz'))
                    cert_commands = """\
# Copy and extract certificates
COPY mitmproxy-certs-backup.tar.gz /home/mitmproxy/
RUN cd /home/mitmproxy && \    
    mkdir ./certs && \
    tar -xzf mitmproxy-certs-backup.tar.gz -C ./certs && \
    ls -la .mitmproxy/ 
"""
                elif file_exists(path_combine(self.certificates_path, '.mitmproxy')):
                    # Copy .mitmproxy directory
                    shutil.copytree(
                        path_combine(self.certificates_path, '.mitmproxy'),
                        path_combine(build_context, '.mitmproxy')
                    )

        # Create Dockerfile - FIXED INDENTATION HERE
        confdir_setting = '"--set", "confdir=/home/mitmproxy/certs/.mitmproxy", ' if include_certificates else ''
        dockerfile_content = f"""\
FROM mitmproxy/mitmproxy:latest
    
# Copy custom script
COPY add_header.py /home/mitmproxy/add_header.py
{cert_commands}
# Set working directory
WORKDIR /home/mitmproxy

# Default command to run mitmproxy with the script
ENTRYPOINT ["mitmdump"]
CMD [{confdir_setting}"--listen-port", "8080", "--script", "/home/mitmproxy/add_header.py", "--set", "block_global=false"]
"""

        # Write Dockerfile
        dockerfile_path = path_combine(build_context, 'Dockerfile')
        file_create(dockerfile_path, dockerfile_content)

        # Build the image
        custom_image = Docker_Image(image_name = self.build_image_name,
                                  image_tag  = 'latest',
                                  api_docker = self.api_docker)

        result = custom_image.build(path=build_context)

        # Cleanup temp directory
        shutil.rmtree(build_context)

        if result.get('status') == 'ok':
            self.image_name = self.build_image_name
            return True
        from osbot_utils.utils.Dev import pprint
        pprint(result)
        return False

    def create_container(self, with_custom_script=True, with_certificates=False):                 # Create mitmproxy container
        # Set default certificates path if not specified
        if with_certificates and not self.certificates_path:
            default_cert_path = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy-certs-backup.tar.gz')
            if file_exists(default_cert_path):
                self.certificates_path = default_cert_path

        if with_custom_script or with_certificates:
            # Build custom image with add_header.py and optionally certificates
            if not self.build_custom_image(include_certificates=with_certificates):
                print("Warning: Failed to build custom image, using default")
                raise Exception("Failed to build custom image")

        # Prepare port bindings
        port_bindings = { 8080 : self.proxy_port,                        # Proxy port
                          8081 : self.web_port  }                        # Web interface port

        # Prepare volumes if using default image or need to mount certificates
        volumes = None
        command = None

        if not with_custom_script or self.image_name == "mitmproxy/mitmproxy":
            volumes = {}
            command_parts = ['mitmdump', '--listen-port', '8080', '--set', 'block_global=false']

            # Mount add_header.py if available
            add_header_path = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/add_header.py')
            if file_exists(add_header_path):
                volumes[add_header_path] = {'bind': '/home/mitmproxy/add_header.py', 'mode': 'ro'}
                command_parts.extend(['--script', '/home/mitmproxy/add_header.py'])

            # Mount certificates if requested and not in image
            if with_certificates and self.certificates_path:
                # Extract certificates first if tar.gz
                if self.certificates_path.endswith('.tar.gz'):
                    import tarfile
                    extract_path = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/')
                    with tarfile.open(self.certificates_path, 'r:gz') as tar:
                        tar.extractall(path=extract_path)

                # Mount .mitmproxy directory
                mitmproxy_dir = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/.mitmproxy')
                if file_exists(mitmproxy_dir):
                    volumes[mitmproxy_dir] = {'bind': '/home/mitmproxy/.mitmproxy', 'mode': 'ro'}
                    command_parts.extend(['--set', 'confdir=/home/mitmproxy/.mitmproxy'])

            command = ' '.join(command_parts) if command_parts else None

        # Create labels for identification
        labels = { 'service'    : 'mitmproxy'  ,
                   'managed_by' : 'mgraph_ai'  ,
                   'instance'   : self.container_name }

        # Create the container
        docker_image = Docker_Image(image_name = self.image_name,
                                   image_tag   = self.image_tag  ,
                                   api_docker  = self.api_docker )

        # Pull image if doesn't exist
        if not docker_image.exists():
            docker_image.pull()

        self.container = docker_image.create_container(command       = command              ,
                                                       name          = self.container_name  ,
                                                       volumes       = volumes              ,
                                                       port_bindings = port_bindings        ,
                                                       labels        = labels               ,
                                                       tty           = True                 )

        return self.container

    def start(self, wait_for_ready=True):                                # Start mitmproxy container
        if not self.container:
            self.create_container()

        if self.container.status() != 'running':
            self.container.start()

            if wait_for_ready:
                return self.wait_for_proxy_ready()
        return True

    def stop(self):                                                      # Stop mitmproxy container
        if self.container and self.container.exists():
            if self.container.status() == 'running':
                self.container.stop()
            return True
        return False

    def delete(self):                                                    # Delete container and custom image
        deleted_container = False
        deleted_image     = False

        if self.container:
            self.stop()
            deleted_container = self.container.delete()

        # Delete custom image if it was created
        if self.image_name and self.image_name.startswith('mitmproxy-custom-'):
            docker_image = Docker_Image(image_name = self.image_name,
                                      image_tag   = self.image_tag  ,
                                      api_docker  = self.api_docker )
            deleted_image = docker_image.delete()

        return deleted_container or deleted_image

    def logs(self):                                                      # Get container logs
        if self.container:
            return self.container.logs()
        return ""

    def exec_command(self, command):                                     # Execute command in container
        if self.container and self.container.status() == 'running':
            return self.container.exec(command)
        return None

    def wait_for_proxy_ready(self, max_attempts=30, wait_time=1):        # Wait for proxy to be ready
        for i in range(max_attempts):
            logs = self.logs()

            # Check if mitmproxy is listening
            if 'Proxy server listening' in logs or 'listening' in logs.lower():
                return True

            # Also check if we can connect to the port
            if self.test_proxy_connection():
                return True

            wait_for(wait_time)

        return False

    def test_proxy_connection(self):                                     # Test if proxy is working
        import requests

        proxy_url = f"http://localhost:{self.proxy_port}"
        proxies   = { 'http'  : proxy_url,
                      'https' : proxy_url }


        # Test request through proxy
        response = requests.get('https://httpbin.org/headers',
                              proxies = proxies              ,
                              timeout = 2                    ,
                              verify  = False                )

        # Check if our custom header was added
        headers = response.json().get('headers', {})

        # Check for custom header from add_header.py
        if 'X-Custom-Header' in headers:
            return True

        # Even without custom header, proxy is working
        return response.status_code == 200

    def get_certificates(self):                                          # Export mitmproxy certificates
        if self.container and self.container.status() == 'running':
            # mitmproxy stores certs in ~/.mitmproxy
            cert_files = [ 'mitmproxy-ca.pem'     ,
                           'mitmproxy-ca-cert.pem' ,
                           'mitmproxy-ca-cert.p12' ,
                           'mitmproxy-dhparam.pem' ]

            certificates = {}
            for cert_file in cert_files:
                cert_path = f'/home/mitmproxy/.mitmproxy/{cert_file}'
                try:
                    content = self.container.exec(f'cat {cert_path}')
                    if content:
                        certificates[cert_file] = content
                except:
                    pass

            return certificates
        return {}

    def install_certificates_locally(self):                              # Install certs for local testing
        certificates = self.get_certificates()

        if certificates:
            cert_dir  = temp_folder()
            installed = []

            for cert_name, cert_content in certificates.items():
                cert_path = path_combine(cert_dir, cert_name)
                file_create(cert_path, cert_content)
                installed.append(cert_path)

            return {'cert_dir': cert_dir, 'certificates': installed}
        return None

    def status(self):                                                    # Get container status
        if self.container:
            return self.container.status()
        return 'not created'

    def info(self):                                                      # Get container info
        if self.container:
            return self.container.info()
        return {}

    def containers_all_mitmproxy(self):                                  # Find all mitmproxy containers
        containers = []

        for container in self.api_docker.containers_all():
            labels = container.labels()
            if labels.get('service') == 'mitmproxy' and labels.get('managed_by') == 'mgraph_ai':
                containers.append(container)

        return containers

    def cleanup_all(self):                                               # Clean up all mitmproxy containers
        cleaned = []

        # Stop and remove all mitmproxy containers
        for container in self.containers_all_mitmproxy():
            container.stop()
            container.delete()
            cleaned.append(container.short_id())

        # Remove custom images
        for image in self.api_docker.images():
            if image.image_name.startswith('mitmproxy-custom-'):
                image.delete()
                cleaned.append(image.image_name)

        return cleaned