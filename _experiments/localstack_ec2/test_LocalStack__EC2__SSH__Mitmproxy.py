# note: this needs LocalStack PRO (and we are using the community edition)

# from unittest                                                                            import TestCase
# import pytest
# from mgraph_ai_service_mitmproxy.service.mitmproxy.LocalStack__EC2__SSH__Mitmproxy import LocalStack__EC2__SSH__Mitmproxy, LOCAL_STACK__SECURITY_GROUP_NAME
# from osbot_aws.aws.ec2.EC2 import EC2
# from osbot_aws.testing.Temp__Random__AWS_Credentials                                      import Temp_AWS_Credentials
# from osbot_local_stack.local_stack.Local_Stack import Local_Stack
# from osbot_utils.type_safe.Type_Safe import Type_Safe
# from osbot_utils.utils.Dev import pprint
# from osbot_utils.utils.Env                                                                import get_env, set_env
# from osbot_utils.utils.Objects                                                            import base_classes
# from mgraph_ai_service_mitmproxy.service.mitmproxy.Create_EC2_Instance__Mitmproxy         import Create_EC2_Instance__Mitmproxy
# from tests.unit.Service__Fast_API__Test_Objs                                              import setup__service_fast_api_test_objs
#
#
# class test_LocalStack__EC2__SSH__Mitmproxy(TestCase):   # Test LocalStack v3+ EC2 instances with SSH support. These tests create Docker-based EC2 instances that can be accessed via SSH.
#
#
#     @classmethod
#     def setUpClass(cls):                                                # Setup LocalStack with EC2 Docker backend
#         cls.test_objs = setup__service_fast_api_test_objs()
#         cls.local_stack = cls.test_objs.local_stack
#
#         # Create service instance
#         cls.mitmproxy_localstack = LocalStack__EC2__SSH__Mitmproxy()
#
#         # Track created resources for cleanup
#         cls.created_instances = []
#         cls.created_amis = []
#
#     # @classmethod
#     # def tearDownClass(cls):                                             # Clean up all created resources
#     #     # Terminate all created instances
#     #     for instance_id in cls.created_instances:
#     #         try:
#     #             cls.localstack_ec2.ec2.instance_terminate(instance_id)
#     #             print(f"Terminated instance: {instance_id}")
#     #         except:
#     #             pass
#     #
#     #     # Deregister AMIs
#     #     for ami_id in cls.created_amis:
#     #         try:
#     #             cls.localstack_ec2.ec2.client.deregister_image(ImageId=ami_id)
#     #             print(f"Deregistered AMI: {ami_id}")
#     #         except:
#     #             pass
#
#     def test__init__(self):                                             # Test inheritance and initialization
#         with self.local_stack as _:
#             assert type(_) is Local_Stack
#             assert _.is_local_stack_configured_and_available()
#
#         with LocalStack__EC2__SSH__Mitmproxy() as _:
#             assert type(_)         is LocalStack__EC2__SSH__Mitmproxy
#             assert type(_.ec2    ) is EC2
#
#             assert base_classes(_) == [Create_EC2_Instance__Mitmproxy, Type_Safe, object]
#
#
#     def test_create_kwargs(self):
#         with self.mitmproxy_localstack as _:
#             kwargs            = _.create_kwargs()
#             security_group_id = _.ec2.security_group(security_group_name=LOCAL_STACK__SECURITY_GROUP_NAME).get('GroupId')
#             assert kwargs == { 'image_id'          : 'ami-ubuntu-22.04'   ,
#                                'instance_type'     : 't2.micro'           ,
#                                'key_name'          : 'localstack-key-name',
#                                'security_group_id' : security_group_id    ,
#                                'spot_instance'     : False                }
# #'i-8a27feae0de57d45b' , 'i-54c4f805aa4fc7b42'
#     def test_create_ec2_instance(self):                                 # Test creating SSH-able EC2 instance
#         """
#         Test creating a LocalStack EC2 instance that runs as Docker container.
#         This instance should be accessible via SSH.
#         """
#         with self.mitmproxy_localstack as _:
#             # Create instance
#             instance_name = "test-localstack-ssh"
#             result = _.create_ec2_instance(instance_name=instance_name)
#
#             # Should return instance ID
#             assert 'instance_id' in result or isinstance(result, str)
#             instance_id = result if isinstance(result, str) else result['instance_id']
#
#             self.created_instances.append(instance_id)
#
#             # Verify instance exists
#             instance_info = _.ec2.instance_details(instance_id)
#             assert instance_info is not None
#             assert instance_info.get('State', {}).get('Name') in ['pending', 'running']
#
#             # # Check Docker container was created
#             # import docker
#             # docker_client = docker.from_env()
#             # container_name = f"localstack-ec2-{instance_id}"
#             #
#             # # Container might take a moment to create
#             # import time
#             # time.sleep(2)
#             #
#             # try:
#             #     container = docker_client.containers.get(container_name)
#             #     assert container.status in ['running', 'created']
#             #     print(f"Docker container {container_name} is {container.status}")
#             # except docker.errors.NotFound:
#             #     print(f"Note: Container {container_name} not found - LocalStack might use different naming")
#
#     def test_ssh_into_instance(self):                                   # Test SSH connectivity
#         """
#         Test that we can SSH into the LocalStack EC2 instance.
#         """
#         with self.localstack_ec2 as _:
#             # Create instance
#             instance_id = _.create_ec2_instance(instance_name="test-ssh")
#             if isinstance(instance_id, dict):
#                 instance_id = instance_id['instance_id']
#             self.created_instances.append(instance_id)
#
#             # Wait for SSH
#             try:
#                 _.wait_for_ssh(instance_id, max_tries=10, delay=2)
#                 ssh_ready = True
#             except Exception as e:
#                 print(f"SSH not ready: {e}")
#                 ssh_ready = False
#
#             if ssh_ready:
#                 # Try to execute command via SSH
#                 with _.ec2_instance_ssh(instance_id) as ssh:
#                     result = ssh.exec('whoami')
#                     assert result.get('stdout', '').strip() == 'ubuntu'
#
#                     result = ssh.exec('pwd')
#                     assert '/home/ubuntu' in result.get('stdout', '')
#
#                     result = ssh.exec('uname -a')
#                     assert 'Linux' in result.get('stdout', '')
#                     print(f"SSH successful! System: {result.get('stdout', '').strip()}")
#             else:
#                 pytest.skip("LocalStack SSH not available in this environment")
#
#     def test_install_mitmproxy(self):                                   # Test full mitmproxy installation
#         """
#         Test installing mitmproxy on LocalStack EC2 instance via SSH.
#         """
#         with self.localstack_ec2 as _:
#             # Create instance
#             instance_id = _.create_ec2_instance(instance_name="test-mitmproxy-install")
#             if isinstance(instance_id, dict):
#                 instance_id = instance_id['instance_id']
#             self.created_instances.append(instance_id)
#
#             try:
#                 # Install mitmproxy
#                 _.ec2_install_mitmproxy(instance_id)
#
#                 # Verify installation
#                 with _.ec2_instance_ssh(instance_id) as ssh:
#                     # Check mitmproxy is installed
#                     result = ssh.exec('which mitmproxy')
#                     assert '/usr/bin/mitmproxy' in result.get('stdout', '')
#
#                     # Check service status
#                     result = ssh.exec('sudo systemctl status mitmproxy')
#                     output = result.get('stdout', '')
#
#                     # Service should be active or at least loaded
#                     assert 'mitmproxy.service' in output or 'active' in output.lower()
#
#                     # Check if add_header.py was copied
#                     result = ssh.exec('ls -la ~/add_header.py')
#                     assert 'add_header.py' in result.get('stdout', '')
#
#                 print("✓ Mitmproxy installation successful!")
#
#                 # Test proxy functionality
#                 proxy_works = _.test_proxy_connection(instance_id)
#                 if proxy_works:
#                     print("✓ Proxy is working with custom headers!")
#
#             except Exception as e:
#                 print(f"Installation test skipped: {e}")
#                 pytest.skip("LocalStack SSH/installation not fully supported in this environment")
#
#     def test_create_ami(self):                                          # Test AMI creation from configured instance
#         """
#         Test creating an AMI from a configured LocalStack EC2 instance.
#         """
#         with self.localstack_ec2 as _:
#             # Create and configure instance
#             instance_id = _.create_ec2_instance(instance_name="test-ami-source")
#             if isinstance(instance_id, dict):
#                 instance_id = instance_id['instance_id']
#             self.created_instances.append(instance_id)
#
#             # Create AMI
#             ami_name = f"mitmproxy-localstack-ami-test"
#             ami_id = _.ec2__create_ami(instance_id)
#
#             assert ami_id is not None
#             assert ami_id.startswith('ami-')
#             self.created_amis.append(ami_id)
#
#             # Verify AMI exists
#             amis = _.ec2.amis()
#             ami_ids = [ami.get('ImageId') for ami in amis]
#             assert ami_id in ami_ids
#
#             print(f"✓ Created AMI: {ami_id}")
#
#     def test_update_service_files(self):                                # Test updating configuration files
#         """
#         Test updating mitmproxy service files on running instance.
#         """
#         with self.localstack_ec2 as _:
#             # Create instance
#             instance_id = _.create_ec2_instance(instance_name="test-update")
#             if isinstance(instance_id, dict):
#                 instance_id = instance_id['instance_id']
#             self.created_instances.append(instance_id)
#
#             try:
#                 # Initial installation
#                 _.ec2_install_mitmproxy(instance_id)
#
#                 # Update service files
#                 _.ec2_update_service_files(instance_id)
#
#                 # Verify files were updated
#                 with _.ec2_instance_ssh(instance_id) as ssh:
#                     result = ssh.exec('sudo systemctl status mitmproxy')
#                     assert 'active' in result.get('stdout', '').lower() or 'loaded' in result.get('stdout', '')
#
#                 print("✓ Service files updated successfully!")
#
#             except Exception as e:
#                 print(f"Update test skipped: {e}")
#                 pytest.skip("LocalStack SSH not fully supported in this environment")
#
#     def test_performance_comparison(self):                              # Compare LocalStack vs Production speed
#         """
#         Document the performance benefits of LocalStack for development.
#         """
#         import time
#
#         with self.localstack_ec2 as _:
#             # Time instance creation
#             start_time = time.time()
#             instance_id = _.create_ec2_instance(instance_name="perf-test")
#             if isinstance(instance_id, dict):
#                 instance_id = instance_id['instance_id']
#             creation_time = time.time() - start_time
#             self.created_instances.append(instance_id)
#
#             print(f"\nPerformance Comparison:")
#             print(f"LocalStack instance creation: {creation_time:.2f} seconds")
#             print(f"AWS EC2 instance creation: ~60-120 seconds (typical)")
#             print(f"Speed improvement: {60/creation_time:.1f}x faster")
#
#             # LocalStack benefits:
#             benefits = {
#                 'No AWS costs'           : True,
#                 'Faster iteration'       : f"{60/creation_time:.1f}x",
#                 'No internet required'   : True,
#                 'Identical API calls'    : True,
#                 'SSH access'            : True,
#                 'Run actual commands'   : True,
#                 'Install software'      : True,
#                 'Create AMIs'           : True
#             }
#
#             print("\nLocalStack Benefits:")
#             for benefit, value in benefits.items():
#                 print(f"  ✓ {benefit}: {value}")
#
#             # Limitations
#             limitations = [
#                 "Container-based, not real VMs",
#                 "Some AWS features might not be 100% identical",
#                 "Network behavior differs from real EC2",
#                 "Performance characteristics differ"
#             ]
#
#             print("\nLocalStack Limitations:")
#             for limitation in limitations:
#                 print(f"  • {limitation}")