from osbot_aws.aws.ec2.EC2 import EC2
from osbot_aws.aws.ec2.EC2_Instance     import EC2_Instance
from osbot_utils.type_safe.Type_Safe    import Type_Safe
from osbot_utils.utils.Dev              import pprint
from osbot_utils.utils.Env              import get_env
from osbot_utils.utils.Files            import path_combine, file_exists
from osbot_utils.utils.Misc import wait_for, random_uuid_short
from osbot_utils.utils.Status           import status_error

import mgraph_ai_service_mitmproxy

DEFAULT__AWS__UBUNTU_LINUX_AMI  = 'ami-046c2381f11878233'
DEFAULT__AWS__INSTANCE_TYPE     = 't2.micro'
class Create_EC2_Instance__Mitmproxy(Type_Safe):
    ec2 : EC2

    def create_kwargs(self, image_id=None):
        instance_type        = DEFAULT__AWS__INSTANCE_TYPE
        spot_instance        = True
        security_group_id    = get_env('EC2_TESTS__SECURITY_GROUP_ID'     )
        ssh_key_name         = get_env('EC2_TESTS__PATH_SSH_KEY_FILE_NAME')

        return  dict(image_id             = image_id or  DEFAULT__AWS__UBUNTU_LINUX_AMI,
                     key_name             = ssh_key_name                               ,
                     security_group_id    = security_group_id                          ,
                     instance_type        = instance_type                              ,
                     spot_instance        = spot_instance                              )

    def create_ec2_instance(self, image_id=None, instance_name=None):
        try:
            ec2_instance = EC2_Instance()
            ec2_instance.create_kwargs = self.create_kwargs(image_id=image_id)
            return ec2_instance.create(instance_name=instance_name)
        except Exception as e:
            return status_error(message='failed to create EC2 instance',
                                error=str(e))

    def ec2_instance(self, instance_id):
        return EC2_Instance(instance_id=instance_id)

    def ec2_instance_ssh(self, instance_id):
        with self.ec2_instance(instance_id) as _:
            _.wait_for_ssh()
            ssh_key_file = get_env('EC2_TESTS__PATH_SSH_KEY_FILE', '')
            ssh_key_user = get_env('EC2_TESTS__PATH_SSH_KEY_USER')
            return _.ssh(ssh_key_file=ssh_key_file, ssh_key_user=ssh_key_user)

    def ec2_install_mitmproxy(self, instance_id):
        self.wait_for_ssh(instance_id)
        file_mitmproxy__certs              = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy-certs-backup.tar.gz'         )
        file_mitmproxy__service            = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy.service'                   )
        file_mitmproxy__add_header         = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/add_header.py'                   )

        #assert file_exists(file_mitmproxy__service)


        # with self.ec2_instance(instance_id) as _:
        #     pprint(_.info())
        with self.ec2_instance_ssh(instance_id) as _:
            _.ssh_execute().print_after_exec = True
            _.exec('sudo apt-get update'                                       )
            _.exec('sudo apt install -y python3-pip'                           )
            _.exec('sudo apt install mitmproxy -y'                             )
            _.exec('mitmproxy --version')

            _.scp().copy_file_to_host(file_mitmproxy__certs  , '.'                                      )

            _.exec("tar -xzf mitmproxy-certs-backup.tar.gz")

            _.scp().copy_file_to_host(file_mitmproxy__add_header  , '.' )
            _.scp().copy_file_to_host(file_mitmproxy__service     , '.' )
            _.exec('sudo cp ./mitmproxy.service /etc/systemd/system/mitmproxy.service')


            _.exec('sudo systemctl daemon-reload')
            _.exec('sudo systemctl enable mitmproxy')
            _.exec('sudo systemctl start mitmproxy')
            _.exec('sudo systemctl status mitmproxy')

    def ec2_update_service_files(self, instance_id):
        file_mitmproxy__service            = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/mitmproxy.service' )
        file_mitmproxy__add_header         = path_combine(mgraph_ai_service_mitmproxy.path, '../_ec2_files/add_header.py'     )
        with self.ec2_instance_ssh(instance_id) as _:
            _.ssh_execute().print_after_exec = True
            _.scp().copy_file_to_host(file_mitmproxy__add_header  , '.' )
            _.scp().copy_file_to_host(file_mitmproxy__service     , '.' )
            _.exec('sudo cp ./mitmproxy.service /etc/systemd/system/mitmproxy.service')
            _.exec('sudo systemctl daemon-reload')
            _.exec('sudo systemctl restart mitmproxy')

    def ec2__create_ami(self, instance_id):
        ami_name = f'osbot-ami-{instance_id}-{random_uuid_short()}'
        return self.ec2.create_image(instance_id=instance_id, name=ami_name)


    def wait_for_ssh(self,instance_id, max_tries=20, delay=1):
        with self.ec2_instance_ssh(instance_id=instance_id) as _:
            print("SSH port is open, now going to wait until we can ssh into it")
            for i in range(0, max_tries):
                response = _.exec('pwd')
                if "System is booting up. " in response.get('stderr'):
                    print(f"[{i}  System is booting up. Going to wait for {delay} second(s)")
                    wait_for(delay)
                else:
                    if response.get('stdout') == '/home/ubuntu\n':
                        print(f"[{i}  System has completed booted up :) ")
                        return
                    pprint(response)
                    raise Exception(f"Something really weird happened since the 'pwd' response from  {instance_id} was not expected: { response.get('stdout') }")
        raise Exception(f"it was not possible to execute ssh commands in the instance {instance_id}")
