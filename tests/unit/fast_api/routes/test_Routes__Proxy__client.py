from unittest                                                           import TestCase
from osbot_utils.testing.__                                             import __, __SKIP__
from osbot_utils.type_safe.type_safe_core.collections.Type_Safe__Dict   import Type_Safe__Dict
from mgraph_ai_service_mitmproxy.fast_api.routes.Routes__Proxy          import Schema__Proxy__Response_Data, Schema__Proxy__Modifications
from tests.unit.Mitmproxy_Service__Fast_API__Test_Objs                  import setup__service_fast_api_test_objs, TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__Proxy__client(TestCase):
    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

    def test_process_response(self):
        url = 'https://docs.diniscruz.ai'

        #show = 'url-to-ratings' # 'url-to-html-dict' , 'url-to-lines' 'url-to-html-xxx'
        show    = 'url-to-html-xxx'
        cookie  = f'mitm-show={show}'
        headers = {'cookie' : cookie}
        request = {'headers': headers}                                  # these headers are in request (i.e. the data sent to the proxy) not the response (i.e. the data received from the upstream proxy)
        response_data = Schema__Proxy__Response_Data(request=request)
        response_data.request     ['url' ] = url
        response       = self.client.post('/proxy/process-response', json=response_data.json())
        response_data  = Schema__Proxy__Modifications.from_json(response.json())

        assert response_data.obj() == __(block_request         = False,
                                         block_status          = 403,
                                         block_message         = 'Blocked by proxy',
                                         include_stats         = False,
                                         modified_body         = None,
                                         override_response     = False,
                                         override_status       = None,
                                         override_content_type = None,
                                         headers_to_add        = __SKIP__,
                                         headers_to_remove     = [],
                                         cached_response       = __(),
                                         stats                 = __())
        headers_to_add = response_data.headers_to_add
        assert type(headers_to_add)              == Type_Safe__Dict
        assert headers_to_add['x-proxy-service'] == 'mgraph-proxy'
        assert headers_to_add['x-wcf-skipped'  ] == 'non-html-content'
