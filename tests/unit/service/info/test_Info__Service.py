from unittest                                              import TestCase

from osbot_utils.helpers.Timestamp_Now import Timestamp_Now

from mgraph_ai_service_base.service.info.Info__Service                  import Info__Service
from mgraph_ai_service_base.service.info.schemas.Schema__Service_Status import Schema__Service_Status, Enum__Service_Status
from mgraph_ai_service_base.utils.Version                               import version__mgraph_ai_service_base


class test_Info__Service(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info_service = Info__Service()

    def test___init__(self):
        with self.info_service as _:
            assert type(_) == Info__Service

    def test_status(self):
        with self.info_service.status() as _:
            assert type(_)      == Schema__Service_Status
            assert _.service    == 'mgraph_ai_service_base'
            assert _.status     == Enum__Service_Status.operational
            assert _.version    == version__mgraph_ai_service_base
            assert _.timestamp  <= Timestamp_Now()
            assert _.environment == self.info_service.environment()