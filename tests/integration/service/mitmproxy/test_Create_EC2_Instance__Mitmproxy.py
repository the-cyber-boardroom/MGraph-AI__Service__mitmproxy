import pytest
from unittest                                                                     import TestCase
from osbot_aws.aws.ec2.EC2                                                        import EC2
from osbot_utils.utils.Dev                                                        import pprint
from osbot_utils.utils.Env                                                        import load_dotenv, get_env
from mgraph_ai_service_mitmproxy.service.mitmproxy.Create_EC2_Instance__Mitmproxy import Create_EC2_Instance__Mitmproxy
from mgraph_ai_service_mitmproxy.utils.Version                                    import version__mgraph_ai_service_mitmproxy


class test_Create_EC2_Instance__CBR_Website_Beta(TestCase):

    @classmethod
    def setUpClass(cls):
        pytest.skip("need manual execution")
        load_dotenv()
        cls.create_ec2_instance = Create_EC2_Instance__Mitmproxy()
        cls.security_group_id   = get_env('EC2_TESTS__SECURITY_GROUP_ID'     )
        cls.ssh_key_name        = get_env('EC2_TESTS__PATH_SSH_KEY_FILE_NAME')
        cls.instance_id         = get_env('EC2_TESTS__EC2_INSTANCE_ID'       )

    def test_create_kwargs(self):
        with self.create_ec2_instance as _:
            kwargs = self.create_ec2_instance.create_kwargs()
            assert kwargs == { 'image_id'           : 'ami-046c2381f11878233'   ,
                               'instance_type'      : 't2.micro'               ,
                               'key_name'           : self.ssh_key_name         ,
                               'security_group_id'  : self.security_group_id    ,
                               'spot_instance'      : True                      }

    #@pytest.mark.skip("this will create a new EC2 instance")
    def test_deploy_cbr_website_to_instance_id(self):
        instance_name = f'mitmproxy__{version__mgraph_ai_service_mitmproxy}'
        with self.create_ec2_instance as _:
            instance_id   = _.create_ec2_instance(instance_name=instance_name)
            pprint(instance_id)
        with EC2() as ec2:
            pprint(ec2.instances_details())
            #_.deploy_cbr_website_to_instance_id(instance_id=instance_id)

    def test_ec2_install_mitmproxy(self):
        print()
        self.create_ec2_instance.ec2_install_mitmproxy(instance_id=self.instance_id)

    def test_ec2_update_service_files(self):
        self.create_ec2_instance.ec2_update_service_files(instance_id=self.instance_id)

    def test_ec2__create_ami(self):
        result = self.create_ec2_instance.ec2__create_ami(instance_id=self.instance_id)
        print()
        print(result)
        #     _.stop()
        #     _.print_info()

