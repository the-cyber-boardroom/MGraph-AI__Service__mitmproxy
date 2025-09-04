from unittest import TestCase

from mgraph_ai_service_mitmproxy.service.mitmproxy.Mitmproxy__EC2 import Mitmproxy__EC2
from osbot_utils.utils.Dev import pprint


class test_Mitmproxy__EC2(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mitmproxy_ec2 = Mitmproxy__EC2()

    def test_amis(self):
        with self.mitmproxy_ec2 as _:

            result = _.amis()
            assert type(result) == list
            #pprint(result)


