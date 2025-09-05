# note: this needs LocalStack PRO (and we are using the community edition)

# import os
# import mgraph_ai_service_mitmproxy
# from osbot_utils.decorators.methods.cache_on_self                                 import cache_on_self
# from osbot_utils.utils.Env                                                        import get_env, set_env
# from osbot_utils.utils.Files                                                      import path_combine, file_exists, file_write, file_not_exists
# from osbot_utils.utils.Misc                                                       import wait_for
# from mgraph_ai_service_mitmproxy.service.mitmproxy.Create_EC2_Instance__Mitmproxy import Create_EC2_Instance__Mitmproxy
#
# LOCALSTACK__UBUNTU_AMI                  = 'ami-ubuntu-22.04'                              # LocalStack recognizes this
# LOCALSTACK__SSH_PORT                    = 22
# LOCAL_STACK__FOLDER__TEMP_FILES         = '../_ec2_files'
# LOCAL_STACK__SSH__KEY_FILE              = 'localstack-key-file.pem'
# LOCAL_STACK__SSH__KEY_NAME              = 'localstack-key-name'
# LOCAL_STACK__SECURITY_GROUP_NAME        = 'localstack-security-group'
# LOCAL_STACK__SECURITY_GROUP_DESCRIPTION = "LocalStack mitmproxy security group"
#
# # todo: rename the name of this class
# class LocalStack__EC2__SSH__Mitmproxy(Create_EC2_Instance__Mitmproxy):   # LocalStack v3+ implementation that creates real SSH-able EC2 instances running as Docker containers. These instances can be accessed via SSH and have mitmproxy installed just like production.
#     #local_stack : Local_Stack
#
#     # def setup(self):                                                     # Initialize LocalStack with EC2 Docker support
#     #     if not self.local_stack:
#     #         self.local_stack = Local_Stack().activate()
#     #
#     #         # Enable EC2 Docker backend in LocalStack
#     #         set_env('LOCALSTACK_EC2_BACKEND', 'docker')                  # Use Docker for EC2 instances
#     #         set_env('EC2_DOCKER_FLAGS', '--cap-add NET_ADMIN')          # Network capabilities for mitmproxy      # see if we need this
#     #
#     #     if not self.ec2:
#     #         self.ec2 = EC2()
#     #     return self
#
#
#     def create_kwargs(self, image_id=None):                                                             #  Create kwargs for LocalStack EC2 instances.
#         localstack_ami      = image_id or LOCALSTACK__UBUNTU_AMI                                        # Use LocalStack Ubuntu AMI that includes SSH server
#         localstack_key_file = self.file__local_stack__key_file()
#         if file_not_exists(localstack_key_file):
#             key_pair_result = self.ec2.key_pair_create(key_name=LOCAL_STACK__SSH__KEY_NAME) # Generate  SSH key for LocalStack
#             key_material    = key_pair_result.get('KeyMaterial')
#             file_write(path=localstack_key_file, contents=key_material)              # Save private key file for SSH access
#             os.chmod(localstack_key_file, 0o600)                                            # Set proper permissions
#
#         # Store key info for later use
#         set_env('LOCALSTACK_SSH_KEY_FILE', localstack_key_file)
#         set_env('LOCALSTACK_SSH_KEY_NAME', LOCAL_STACK__SSH__KEY_NAME)
#
#         return dict(image_id          = localstack_ami,
#                     key_name          = LOCAL_STACK__SSH__KEY_NAME,
#                     instance_type     = 't2.micro',                             # LocalStack accepts standard types
#                     security_group_id = self.create_localstack_security_group(),
#                     spot_instance     = False                                 )   # LocalStack doesn't support spot
#
#     def create_localstack_security_group(self):                         # Create a security group in LocalStack that allows SSH
#
#         sg_name        = LOCAL_STACK__SECURITY_GROUP_NAME
#         sg_description = LOCAL_STACK__SECURITY_GROUP_DESCRIPTION
#
#         if self.ec2.security_group_exists(security_group_name = sg_name) is False:
#             sg_result = self.ec2.security_group_create(security_group_name = sg_name       ,        # Create security group using EC2
#                                                         description        = sg_description)
#
#
#             sg_id = sg_result.get('data', {}).get('security_group_id')                              # Extract security_group_id from status result
#
#             for port in [22, 8080, 8081]:                                                           # # Add ssh and mitmproxy ports (Proxy and web interface)
#                 self.ec2.security_group_authorize_ingress(security_group_id = sg_id      ,
#                                                           port              = port       ,
#                                                           cidr_ip           = '0.0.0.0/0')
#         else:
#             sg_id = self.ec2.security_group(security_group_name=sg_name).get('GroupId')
#
#         return sg_id
#
#
#     def ec2_instance_ssh(self, instance_id):                            # Override for LocalStack SSH access
#         """
#         SSH into LocalStack EC2 instance running in Docker.
#         LocalStack v3+ provides SSH access to EC2 Docker containers.
#         """
#         with self.ec2_instance(instance_id) as _:
#             # Get instance details
#             instance_info = _.info()
#
#             # LocalStack instances run on localhost with mapped ports
#             ssh_host = 'localhost'                                      # LocalStack runs locally
#
#             # Get the SSH port mapping (LocalStack maps container port 22)
#             # LocalStack usually maps to a high port like 32768+
#             ssh_port = self.get_localstack_ssh_port(instance_id)
#
#             # Get SSH key created during instance launch
#             ssh_key_file = get_env('LOCALSTACK_SSH_KEY_FILE')
#             ssh_key_user = 'ubuntu'                                     # Default for Ubuntu AMI
#
#             # Create SSH connection to LocalStack container
#             ssh_execute = SSH__Execute(
#                 host         = ssh_host,
#                 port         = ssh_port,
#                 ssh_key_file = ssh_key_file,
#                 ssh_key_user = ssh_key_user
#             )
#
#             return ssh_execute
#
#     def get_localstack_ssh_port(self, instance_id):                     # Get Docker port mapping for SSH
#         """
#         Get the mapped SSH port for the LocalStack EC2 instance.
#         LocalStack maps container port 22 to a random host port.
#         """
#         import docker
#         docker_client = docker.from_env()
#
#         # LocalStack creates containers with naming pattern
#         container_name = f"localstack-ec2-{instance_id}"
#
#         try:
#             container = docker_client.containers.get(container_name)
#             # Get port mapping for SSH (22)
#             port_bindings = container.ports.get('22/tcp', [])
#             if port_bindings:
#                 return int(port_bindings[0]['HostPort'])
#         except:
#             pass
#
#         # Default fallback
#         return 2222                                                     # LocalStack default SSH port
#
#     def wait_for_ssh(self, instance_id, max_tries=20, delay=2):         # Override for LocalStack timing
#         """
#         Wait for SSH to be available in LocalStack EC2 instance.
#         LocalStack instances start much faster than real EC2.
#         """
#         print(f"Waiting for LocalStack EC2 instance {instance_id} to be SSH-ready...")
#
#         for i in range(max_tries):
#             try:
#                 with self.ec2_instance_ssh(instance_id) as ssh:
#                     response = ssh.exec('pwd')
#                     if response.get('stdout') == '/home/ubuntu\n':
#                         print(f"[{i}] LocalStack instance SSH is ready!")
#                         return True
#             except Exception as e:
#                 print(f"[{i}] Waiting for SSH... ({e})")
#                 wait_for(delay)
#
#         raise Exception(f"LocalStack EC2 instance {instance_id} SSH not ready after {max_tries} attempts")
#
#     def ec2_install_mitmproxy(self, instance_id):                       # Same as production but faster
#         """
#         Install mitmproxy on LocalStack EC2 instance.
#         This works the same as production but is much faster.
#         """
#         print(f"Installing mitmproxy on LocalStack EC2 instance {instance_id}...")
#
#         self.wait_for_ssh(instance_id)
#
#         # Get file paths
#         file_mitmproxy__certs      = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy-certs-backup.tar.gz')
#         file_mitmproxy__service    = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy.service')
#         file_mitmproxy__add_header = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/add_header.py')
#
#         with self.ec2_instance_ssh(instance_id) as ssh:
#             ssh.ssh_execute().print_after_exec = True
#
#             # Update and install packages (faster in LocalStack)
#             ssh.exec('sudo apt-get update')
#             ssh.exec('sudo apt install -y python3-pip')
#             ssh.exec('sudo apt install mitmproxy -y')
#             ssh.exec('mitmproxy --version')
#
#             # Copy certificates
#             if file_exists(file_mitmproxy__certs):
#                 ssh.scp().copy_file_to_host(file_mitmproxy__certs, '.')
#                 ssh.exec("tar -xzf mitmproxy-certs-backup.tar.gz")
#
#             # Copy configuration files
#             ssh.scp().copy_file_to_host(file_mitmproxy__add_header, '.')
#             ssh.scp().copy_file_to_host(file_mitmproxy__service, '.')
#             ssh.exec('sudo cp ./mitmproxy.service /etc/systemd/system/mitmproxy.service')
#
#             # Start service
#             ssh.exec('sudo systemctl daemon-reload')
#             ssh.exec('sudo systemctl enable mitmproxy')
#             ssh.exec('sudo systemctl start mitmproxy')
#             ssh.exec('sudo systemctl status mitmproxy')
#
#         print(f"Mitmproxy installed successfully on LocalStack instance {instance_id}")
#
#     def test_proxy_connection(self, instance_id):                       # Test mitmproxy is working
#         """Test that mitmproxy is running and accepting connections."""
#         import requests
#
#         # Get instance IP (in LocalStack it's localhost)
#         proxy_host = 'localhost'
#         proxy_port = 8080
#
#         proxies = {
#             'http' : f'http://{proxy_host}:{proxy_port}',
#             'https': f'http://{proxy_host}:{proxy_port}'
#         }
#
#         try:
#             # Test request through proxy
#             response = requests.get('http://httpbin.org/headers',
#                                   proxies=proxies,
#                                   timeout=5)
#
#             # Check if our custom header was added
#             headers = response.json().get('headers', {})
#             if 'X-Custom-Header' in headers:
#                 print(f"✓ Proxy working! Custom header: {headers['X-Custom-Header']}")
#                 return True
#             else:
#                 print("✗ Proxy responding but custom header not found")
#                 return False
#         except Exception as e:
#             print(f"✗ Proxy test failed: {e}")
#             return False
#
#     @cache_on_self
#     def folder__ec2_files(self):
#         return path_combine(mgraph_ai_service_mitmproxy.path, LOCAL_STACK__FOLDER__TEMP_FILES)
#
#     @cache_on_self
#     def file__local_stack__key_file(self):
#         return path_combine(self.folder__ec2_files(), LOCAL_STACK__SSH__KEY_FILE)
