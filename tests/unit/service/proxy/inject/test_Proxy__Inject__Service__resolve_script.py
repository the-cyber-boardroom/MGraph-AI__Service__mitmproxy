from unittest                                                               import TestCase
from unittest.mock                                                          import Mock, patch
from mgraph_ai_service_cache_client.schemas.cache.enums.Enum__Cache__Read__Status import Enum__Cache__Read__Status
from mgraph_ai_service_mitmproxy.service.proxy.inject.Proxy__Inject__Service import EMPTY_STUB, Proxy__Inject__Service
from mgraph_ai_service_mitmproxy.service.proxy.inject.schemas.Enum__Inject__Script__Load__Status import Enum__Inject__Script__Load__Status
from mgraph_ai_service_mitmproxy.service.proxy.inject.schemas.Schema__Inject__Script__Load__Result import Schema__Inject__Script__Load__Result


FULL_FILTER = 'window.__exampleFilter = { active: true };'
DOMAIN      = 'example.com'
CACHE_ID    = '11111111-1111-4111-8111-111111111111'


class test_Proxy__Inject__Service__resolve_script(TestCase):

    def setUp(self):
        self.inject_service = Proxy__Inject__Service()

    def load_result(self,
                    status     : Enum__Inject__Script__Load__Status,
                    script     : str = '',
                    attempts   : int = 1,
                    error_type : str = ''
               ) -> Schema__Inject__Script__Load__Result:
        return Schema__Inject__Script__Load__Result(status     = status    ,
                                                    script     = script    ,
                                                    attempts   = attempts  ,
                                                    error_type = error_type)

    def client_read_result(self,
                           status     : Enum__Cache__Read__Status,
                           value      : str = '',
                           error_type : str = '') -> Mock:
        return Mock(status=status, value=value, error_type=error_type)

    def test_existing_full_filter__returns_filter_without_write(self):
        hit = self.load_result(Enum__Inject__Script__Load__Status.HIT, script=FULL_FILTER)
        with patch.object(self.inject_service, '_load_from_cache', return_value=hit), \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == FULL_FILTER
        store.assert_not_called()

    def test_existing_stub__returns_stub_without_rewrite(self):
        hit = self.load_result(Enum__Inject__Script__Load__Status.HIT, script=EMPTY_STUB)
        with patch.object(self.inject_service, '_load_from_cache', return_value=hit), \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == EMPTY_STUB
        store.assert_not_called()

    def test_confirmed_miss__writes_and_returns_stub(self):
        miss = self.load_result(Enum__Inject__Script__Load__Status.MISS)
        with patch.object(self.inject_service, '_load_from_cache', return_value=miss), \
             patch.object(self.inject_service, '_store_to_cache', return_value=True) as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == EMPTY_STUB
        store.assert_called_once_with(DOMAIN, EMPTY_STUB)

    def test_read_error__does_not_write_or_inject(self):
        error = self.load_result(Enum__Inject__Script__Load__Status.ERROR,
                                 attempts=2, error_type='TimeoutError')
        with patch.object(self.inject_service, '_load_from_cache', return_value=error), \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == ''
        store.assert_not_called()

    def test_confirmed_miss_with_failed_store__does_not_inject_or_claim_success(self):
        miss = self.load_result(Enum__Inject__Script__Load__Status.MISS)
        with patch.object(self.inject_service, '_load_from_cache', return_value=miss), \
             patch.object(self.inject_service, '_store_to_cache', return_value=False) as store, \
             patch('builtins.print') as print_mock:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == ''
        store.assert_called_once_with(DOMAIN, EMPTY_STUB)
        assert not any('Created inject stub' in str(call_) for call_ in print_mock.call_args_list)

    def test_error_then_hit__retries_once_and_injects_recovered_filter(self):
        self.inject_service._cache_id = CACHE_ID
        read_error = TimeoutError('transient S3 read failure')
        read_hit   = self.client_read_result(Enum__Cache__Read__Status.HIT, value=FULL_FILTER)

        with patch.object(
            self.inject_service.cache_service.cache_client.data().retrieve(),
            'data__string__result__with__id_and_key',
            side_effect=(read_error, read_hit),
        ) as read:
            result = self.inject_service._load_from_cache(DOMAIN)

        assert result.status   is Enum__Inject__Script__Load__Status.HIT
        assert result.script   == FULL_FILTER
        assert result.attempts == 2
        assert read.call_count == 2

    def test_two_read_errors__do_not_overwrite_existing_filter(self):
        self.inject_service._cache_id = CACHE_ID
        data_key      = self.inject_service.data_key_for_domain(DOMAIN)
        backing_store = {(CACHE_ID, data_key): FULL_FILTER}

        with patch.object(
            self.inject_service.cache_service.cache_client.data().retrieve(),
            'data__string__result__with__id_and_key',
            side_effect=(TimeoutError('first failure'), TimeoutError('second failure')),
        ) as read, \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == ''
        assert backing_store[(CACHE_ID, data_key)] == FULL_FILTER
        assert read.call_count == 2
        store.assert_not_called()

    def test_empty_response_errors__retry_once_then_do_not_write(self):
        self.inject_service._cache_id = CACHE_ID
        empty_error = self.client_read_result(Enum__Cache__Read__Status.ERROR,
                                              error_type='EMPTY_RESPONSE')

        with patch.object(
            self.inject_service.cache_service.cache_client.data().retrieve(),
            'data__string__result__with__id_and_key',
            side_effect=(empty_error, empty_error),
        ) as read, \
             patch.object(self.inject_service, '_store_to_cache') as store:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == ''
        assert read.call_count == 2
        store.assert_not_called()

    def test_confirmed_script_miss__does_not_retry(self):
        self.inject_service._cache_id = CACHE_ID
        miss = self.client_read_result(Enum__Cache__Read__Status.MISS)

        with patch.object(
            self.inject_service.cache_service.cache_client.data().retrieve(),
            'data__string__result__with__id_and_key',
            return_value=miss,
        ) as read:
            result = self.inject_service._load_from_cache(DOMAIN)

        assert result.status is Enum__Inject__Script__Load__Status.MISS
        assert read.call_count == 1

    def test_cache_id_lookup_error_then_hit__recovers_on_single_retry(self):
        cache_hit = Mock(status=Enum__Cache__Read__Status.HIT, cache_id=CACHE_ID)

        with patch.object(
            self.inject_service.cache_service.cache_client.retrieve(),
            'retrieve__hash__cache_hash__cache_id__result',
            side_effect=(TimeoutError('first failure'), cache_hit),
        ) as read, \
             patch.object(
                 self.inject_service.cache_service.cache_client.store(),
                 'store__json__cache_key',
             ) as create_entry:
            result = self.inject_service._get_or_create_cache_id()

        assert result == CACHE_ID
        assert read.call_count == 2
        create_entry.assert_not_called()

    def test_cache_id_lookup_error_twice__does_not_create_parent_or_stub(self):
        with patch.object(
            self.inject_service.cache_service.cache_client.retrieve(),
            'retrieve__hash__cache_hash__cache_id__result',
            side_effect=(TimeoutError('first failure'), TimeoutError('second failure')),
        ) as read, \
             patch.object(
                 self.inject_service.cache_service.cache_client.store(),
                 'store__json__cache_key',
             ) as create_entry, \
             patch.object(self.inject_service, '_store_to_cache') as store_stub:
            result = self.inject_service.resolve_script(DOMAIN)

        assert result == ''
        assert read.call_count == 2
        create_entry.assert_not_called()
        store_stub.assert_not_called()

    def test_confirmed_cache_id_miss__creates_parent_without_retry(self):
        cache_miss = Mock(status=Enum__Cache__Read__Status.MISS)
        created    = Mock(cache_id=CACHE_ID)

        with patch.object(
            self.inject_service.cache_service.cache_client.retrieve(),
            'retrieve__hash__cache_hash__cache_id__result',
            return_value=cache_miss,
        ) as read, \
             patch.object(
                 self.inject_service.cache_service.cache_client.store(),
                 'store__json__cache_key',
                 return_value=created,
             ) as create_entry:
            result = self.inject_service._get_or_create_cache_id()

        assert result == CACHE_ID
        assert read.call_count == 1
        create_entry.assert_called_once()
