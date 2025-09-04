from osbot_aws.aws.ec2.EC2           import EC2
from osbot_utils.type_safe.Type_Safe import Type_Safe

DEFAULT_UBUNTU_LINUX_AMI = "ami-046c2381f11878233"  # published on 2025-08-21, has python 3.12
class Mitmproxy__EC2(Type_Safe):
    ec2 : EC2

    def amis(self):
        return self.ec2.amis()

    def start_instance(self):
        size = 't2.micro'
