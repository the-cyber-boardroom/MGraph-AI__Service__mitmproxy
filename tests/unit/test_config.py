from unittest                          import TestCase
from mgraph_ai_service_base.config     import SERVICE_NAME, LAMBDA_NAME__SERVICE__CORE


class test_config(TestCase):

    def test__config_vars(self):
        assert SERVICE_NAME                   == 'mgraph_ai_service_base'
        assert LAMBDA_NAME__SERVICE__CORE     == f'service__{SERVICE_NAME}'