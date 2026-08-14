from unittest                                                               import TestCase
from unittest.mock                                                          import patch
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Response_Data import Schema__Proxy__Response_Data
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Cookie__Service       import Proxy__Cookie__Service
from mgraph_ai_service_mitmproxy.service.proxy.inject.Proxy__Inject__Service import EMPTY_STUB, Proxy__Inject__Service
from mgraph_ai_service_mitmproxy.service.proxy.inject.schemas.Enum__Inject__Script__Load__Status import Enum__Inject__Script__Load__Status
from mgraph_ai_service_mitmproxy.service.proxy.inject.schemas.Schema__Inject__Script__Load__Result import Schema__Inject__Script__Load__Result
from mgraph_ai_service_mitmproxy.service.proxy.response.Proxy__Response__Service import Proxy__Response__Service


FULL_FILTER = 'window.__exampleFilter = { active: true };'


class test_Proxy__Response__Service__inject_lifecycle(TestCase):

    def setUp(self):
        self.inject_service = Proxy__Inject__Service()
        self.response_service = Proxy__Response__Service(
            cookie_service = Proxy__Cookie__Service(),
            inject_service = self.inject_service,
        )

    def response_data(self,
                      cookie      : str = '',
                      content_type: str = 'text/html; charset=utf-8',
                      host        : str = 'www.example.com',
                      status_code : int = 200
                 ) -> Schema__Proxy__Response_Data:
        headers = {}
        if cookie:
            headers['cookie'] = cookie

        return Schema__Proxy__Response_Data(
            request  = { 'method'  : 'GET'   ,
                         'scheme'  : 'https' ,
                         'host'    : host    ,
                         'port'    : 443     ,
                         'path'    : '/news' ,
                         'headers' : headers },
            response = { 'status_code' : status_code                              ,
                         'headers'     : {'content-type': content_type}           ,
                         'body'        : '<html><body>Publisher page</body></html>'},
            stats    = {},
            version  = 'v0.8.36',
        )

    def test_new_site_without_cookie__does_not_resolve_or_inject(self):
        response_data = self.response_data()

        with patch.object(self.inject_service, 'resolve_script') as resolve:
            result = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        assert result == (None, {})
        resolve.assert_not_called()

    def test_new_site_with_off_or_unrelated_cookie__does_not_resolve(self):
        for cookie in ('mitm-mode=off', 'session-id=abc'):
            with self.subTest(cookie=cookie):
                response_data = self.response_data(cookie=cookie)

                with patch.object(self.inject_service, 'resolve_script') as resolve:
                    result = self.response_service.process_html_transformation(
                        response_data   = response_data,
                        request_headers = response_data.request['headers'],
                    )

                assert result == (None, {})
                resolve.assert_not_called()

    def test_inject_cookie_on_non_html__does_not_resolve(self):
        response_data = self.response_data(
            cookie       = 'mitm-mode=inject',
            content_type = 'application/json',
        )

        with patch.object(self.inject_service, 'resolve_script') as resolve:
            result = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        assert result == (None, {}, [])
        resolve.assert_not_called()

    def test_inject_cookie_on_new_site__injects_stub(self):
        response_data = self.response_data(cookie='mitm-mode=inject')
        miss = Schema__Inject__Script__Load__Result(
            status   = Enum__Inject__Script__Load__Status.MISS,
            attempts = 1)

        with patch.object(self.inject_service, '_load_from_cache', return_value=miss), \
             patch.object(self.inject_service, '_store_to_cache', return_value=True) as store:
            modified, headers_to_add, headers_to_remove = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        store.assert_called_once_with('example.com', EMPTY_STUB)
        assert EMPTY_STUB in modified
        assert headers_to_add['x-mitm-inject']        == 'true'
        assert headers_to_add['x-mitm-inject-domain'] == 'example.com'
        assert headers_to_add['x-mitm-inject-size']   == str(len(EMPTY_STUB))
        assert len(EMPTY_STUB)                        == 68
        assert len(EMPTY_STUB.encode('utf-8'))        == 70
        assert 'content-security-policy' in headers_to_remove

    def test_stub_replaced_in_s3__next_request_injects_full_filter(self):
        response_data = self.response_data(cookie='mitm-mode=inject')
        miss = Schema__Inject__Script__Load__Result(
            status   = Enum__Inject__Script__Load__Status.MISS,
            attempts = 1)
        hit = Schema__Inject__Script__Load__Result(
            status   = Enum__Inject__Script__Load__Status.HIT,
            script   = FULL_FILTER,
            attempts = 1)

        with patch.object(
            self.inject_service,
            '_load_from_cache',
            side_effect=(miss, hit),
        ) as load, \
             patch.object(self.inject_service, '_store_to_cache', return_value=True) as store:
            first_modified, first_headers, _   = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )
            second_modified, second_headers, _ = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        assert load.call_count == 2
        store.assert_called_once_with('example.com', EMPTY_STUB)
        assert EMPTY_STUB in first_modified
        assert first_headers['x-mitm-inject-size'] == str(len(EMPTY_STUB))
        assert FULL_FILTER in second_modified
        assert EMPTY_STUB not in second_modified
        assert second_headers['x-mitm-inject-size'] == str(len(FULL_FILTER))

    def test_inject_cookie_with_two_read_errors__does_not_write_or_inject(self):
        response_data = self.response_data(cookie='mitm-mode=inject')
        error = Schema__Inject__Script__Load__Result(
            status     = Enum__Inject__Script__Load__Status.ERROR,
            attempts   = 2,
            error_type = 'TimeoutError')

        with patch.object(self.inject_service, '_load_from_cache', return_value=error), \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        assert result == (None, {}, [])
        store.assert_not_called()

    def test_bbc_without_cookie__currently_bypasses_cookie_gate(self):
        response_data = self.response_data(host='www.bbc.co.uk')

        with patch.object(self.inject_service, 'resolve_script', return_value=FULL_FILTER) as resolve:
            modified, headers_to_add, _ = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        resolve.assert_called_once_with('bbc.co.uk')
        assert FULL_FILTER in modified
        assert headers_to_add['x-mitm-inject-domain'] == 'bbc.co.uk'

    def test_inject_cookie_on_non_2xx_html__currently_injects(self):
        response_data = self.response_data(
            cookie      = 'mitm-mode=inject',
            status_code = 403,
        )

        with patch.object(self.inject_service, 'resolve_script', return_value=FULL_FILTER) as resolve:
            modified, headers_to_add, _ = self.response_service.process_html_transformation(
                response_data   = response_data,
                request_headers = response_data.request['headers'],
            )

        resolve.assert_called_once_with('example.com')
        assert FULL_FILTER in modified
        assert headers_to_add['x-mitm-inject'] == 'true'
