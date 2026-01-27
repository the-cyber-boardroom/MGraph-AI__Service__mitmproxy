from unittest                                                          import TestCase
from osbot_utils.testing.__                                            import __
from osbot_utils.testing.__helpers                                     import obj
from osbot_utils.utils.Env                                             import in_github_action, load_dotenv
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Cache         import Routes__Cache
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service   import Proxy__Cache__Service

class test_Routes__Cache(TestCase):

    @classmethod
    def setUpClass(cls) -> None:                                                                # Setup cache service and test infrastructure
        #load_dotenv()
        cls.routes_cache = Routes__Cache()

    def test_setUpClass(self):
        with self.routes_cache as _:
            assert type(_)               is Routes__Cache
            assert type(_.cache_service) is Proxy__Cache__Service
            assert _.tag                 == 'cache'

    def test_health(self):             # /cache/health endpoint logic
        with self.routes_cache as _:
            # if in_github_action():
            #     status = 'disabled'
            #     enabled = False
            # else:
            #     status = 'ok'
            #     enabled = True

            status = 'ok'
            enabled = True
            result = _.health()
            assert type(result) is dict
            assert obj(result) == __(status     = status                       ,
                                     enabled    = enabled                      ,
                                     base_url   = 'https://cache.dev.mgraph.ai',
                                     namespace  = 'wcf-results'                )

    def test__stats(self):              # Test /cache/stats endpoint logic
        with self.routes_cache as _:
            if in_github_action():
                enabled = False
            else:
                enabled = True
            result = _.stats()
            assert type(result) is dict
            assert obj(result)  == __(enabled                    = enabled,
                                     hit_rate                    = 0.0   ,
                                     cache_hits                  = 0     ,
                                     cache_misses                = 0     ,
                                     wcf_calls_saved             = 0     ,
                                     total_pages_cached          = 0     ,
                                     avg_cache_hit_time_ms       = 0.0   ,
                                     avg_cache_miss_time_ms      = 0.0   ,
                                     avg_wcf_call_time_ms        = 0.0   ,
                                     estimated_time_saved_seconds= 0.0   )

    def test_config(self):                     # Test /cache/config endpoint logic
        with self.routes_cache as _:                                        # at the moment the auth is not configure in GH actions
            if in_github_action():
                auth_configured = False
                enabled         = False
            else:
                auth_configured = False
                enabled         = True
            result = _.config()
            assert obj(result) == __(enabled         = enabled                       ,
                                     auth_configured = auth_configured               ,
                                     base_url        = 'https://cache.dev.mgraph.ai' ,
                                     namespace       = 'wcf-results'                 ,
                                     timeout         = 30                            ,
                                     strategy        = 'key_based'                   ,
                                     data_file_id    ='latest'                       ,
                                     cache_metadata  = True                          ,
                                     track_stats     = True                          )

