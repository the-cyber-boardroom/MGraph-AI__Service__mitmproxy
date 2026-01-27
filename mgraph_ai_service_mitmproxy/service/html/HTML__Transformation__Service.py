import time
from typing import Optional, List

from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Classification__Criterion_Filter import Schema__Classification__Criterion_Filter
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Classification__Filter_Mode import Enum__Classification__Filter_Mode
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Classification__Logic_Operator import Enum__Classification__Logic_Operator
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Classification__Criteria import Enum__Text__Classification__Criteria
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Transformation__Engine_Mode import Enum__Text__Transformation__Engine_Mode
from osbot_utils.type_safe.Type_Safe                                                                         import Type_Safe
from osbot_utils.type_safe.primitives.core.Safe_Float                                                        import Safe_Float
from osbot_utils.type_safe.primitives.domains.web.safe_str.Safe_Str__Html                                    import Safe_Str__Html
from mgraph_ai_service_mitmproxy.schemas.html.Enum__HTML__Transformation_Mode                                import Enum__HTML__Transformation_Mode
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Transformation__Result                           import Schema__HTML__Transformation__Result
from mgraph_ai_service_mitmproxy.schemas.html.Schema__HTML__Transformation__Step_1                           import Schema__HTML__Transformation__Step_1
from mgraph_ai_service_mitmproxy.schemas.html.Schema__Hashes__To__Html__Request                              import Schema__Hashes__To__Html__Request
from mgraph_ai_service_mitmproxy.schemas.html.Schema__Html__To__Dict__Hashes__Request                        import Schema__Html__To__Dict__Hashes__Request
from mgraph_ai_service_mitmproxy.schemas.html.safe_dict.Safe_Dict__Hash__To__Text                            import Safe_Dict__Hash__To__Text
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Transformation__Mode         import Enum__Text__Transformation__Mode
from mgraph_ai_service_mitmproxy.service.html.HTML__Service__Client                                          import HTML__Service__Client
from mgraph_ai_service_mitmproxy.service.cache.Proxy__Cache__Service                                         import Proxy__Cache__Service
from mgraph_ai_service_mitmproxy.service.semantic_text.Semantic_Text__Service__Client                        import Semantic_Text__Service__Client
from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.Schema__Semantic_Text__Transformation__Request import Schema__Semantic_Text__Transformation__Request


class HTML__Transformation__Service(Type_Safe):                                              # Orchestrates HTML transformations with semantic-text service
    html_service_client      : HTML__Service__Client           = None                        # HTML Service HTTP client
    semantic_text_client     : Semantic_Text__Service__Client  = None                        # Semantic Text Service HTTP client
    cache_service            : Proxy__Cache__Service           = None                        # Cache service integration

    def setup(self) -> 'HTML__Transformation__Service':                                      # Initialize service dependencies
        self.html_service_client  = HTML__Service__Client().setup()
        self.semantic_text_client = Semantic_Text__Service__Client()
        self.cache_service        = Proxy__Cache__Service()#.setup()
        return self

    def transform_html(self, source_html   : str                                  ,          # Source HTML content
                             target_url    : str                                  ,          # Original URL (for cache key)
                             mode          : Enum__HTML__Transformation_Mode                 # Transformation mode
                       ) -> Schema__HTML__Transformation__Result:                            # Transformation result

        if not mode.is_active():                                                              # No transformation needed
            return self._create_passthrough_result(source_html, mode)

        cached_result = self.get_cached_transformation(target_url, mode)                     # Try cache first
        if cached_result:
            return cached_result

        transformation_result = self._transform_via_services(source_html, mode)              # Cache miss - perform transformation

        if transformation_result.transformed_html:                                            # Store successful transformation
            self._store_transformation_in_cache(target_url, mode, transformation_result)

        return transformation_result

    def _transform_via_services(self, source_html : str                             ,        # Source HTML to transform
                                      mode        : Enum__HTML__Transformation_Mode          # Transformation mode
                                ) -> Schema__HTML__Transformation__Result:                   # Transformation result

        start_time = time.time()

        try:
            step_1_result = self._step_1__get_hash_mapping(source_html)                     # Step 1: HTML → Hash Mapping
            html_dict     = step_1_result.html_dict
            hash_mapping  = step_1_result.hash_mapping
            transformed_mapping = self._step_2__transform_mapping(hash_mapping, mode)       # Step 2: Transform Hash Mapping

            transformed_html = self._step_3__reconstruct_html(html_dict,                    # Step 3: Hash Mapping → HTML
                                                              transformed_mapping)

            call_duration_ms = (time.time() - start_time) * 1000

            print(f"    ✅ Transformation complete in {call_duration_ms/1000:.2f}s")

            return Schema__HTML__Transformation__Result(
                transformed_html       = transformed_html,
                transformation_mode    = mode,
                content_type           = mode.to_content_type(),
                cache_hit              = False,
                transformation_time_ms = Safe_Float(call_duration_ms)
            )

        except Exception as e:
            print(f"    ⚠️  Transformation error: {e}")
            return self._create_error_result(source_html, mode, start_time)

    def _step_1__get_hash_mapping(self, source_html : Safe_Str__Html                         # Get hash mapping from HTML
                                   ) -> Schema__HTML__Transformation__Step_1:

        print(f"    📋 Step 1: Getting hash mapping from HTML Service...")

        request  = Schema__Html__To__Dict__Hashes__Request(html=source_html)
        response = self.html_service_client.get_dict_hashes(request)

        if not response.is_successful():
            raise Exception("Failed to get hash mapping from HTML Service")

        print(f"    📋 Got {response.total_text_hashes} text nodes")

        return Schema__HTML__Transformation__Step_1(html_dict    = response.html_dict   ,
                                                    hash_mapping = response.hash_mapping)

    # todo: see if we can convert the Enum__Text__Transformation__Mode into Enum__HTML__Transformation_Mode (even better if we can make them compatible by making one the base class of the other)
    def _step_2__transform_mapping(self, hash_mapping : Safe_Dict__Hash__To__Text      ,      # Hash mapping to transform
                                         mode         : Enum__HTML__Transformation_Mode      # Transformation mode
                                   ) -> Safe_Dict__Hash__To__Text:                                                # Transformed mapping

        print(f"    🔄 Step 2: Transforming via Semantic Text Service...")

        # semantic_mode = Enum__Text__Transformation__Mode(mode)                                # Convert to semantic-text mode
        #
        # request        = Schema__Semantic_Text__Transformation__Request(hash_mapping         = hash_mapping,
        #                                                                 transformation_mode  = semantic_mode)

        if mode.uses_sentiment_analysis():                                              # Determine engine mode and filters
            engine_mode       = Enum__Text__Transformation__Engine_Mode.AWS_COMPREHEND
            criterion_filters = self._build_criterion_filters(mode)
            logic_operator    = self._get_logic_operator(mode)
            print(f"       🧠 Using AWS Comprehend with {len(criterion_filters)} filters")
        else:
            # Default to deterministic hash-based
            engine_mode       = Enum__Text__Transformation__Engine_Mode.TEXT_HASH
            criterion_filters = []  # Empty = transform all
            logic_operator    = Enum__Classification__Logic_Operator.AND
            print(f"       🔢 Using deterministic TEXT_HASH engine")

        # Get visual transformation mode (xxx, hashes, etc)
        visual_mode = mode.to_visual_mode()

        # 🆕 Build complete request with sentiment filters
        request = Schema__Semantic_Text__Transformation__Request(
            hash_mapping=hash_mapping,
            engine_mode=engine_mode,                    # ← AWS Comprehend!
            criterion_filters=criterion_filters,         # ← Sentiment filters!
            logic_operator=logic_operator,              # ← AND/OR
            transformation_mode=visual_mode             # ← xxx, hashes
        )
        response = self.semantic_text_client.transform_text(request)

        if not response.success:
            raise Exception(f"Semantic Text Service failed: {response.error_message}")

        print(f"    🔄 Transformed {response.transformed_hashes}/{response.total_hashes} nodes")

        return response.transformed_mapping

    def _step_3__reconstruct_html(self, html_dict          : dict                   ,        # HTML structure
                                        transformed_mapping : Safe_Dict__Hash__To__Text      # Transformed hash mapping
                                  ) -> Safe_Str__Html:                                       # Reconstructed HTML

        print(f"    🔨 Step 3: Reconstructing HTML...")

        request = Schema__Hashes__To__Html__Request(html_dict    = html_dict,
                                                    hash_mapping = transformed_mapping)

        response = self.html_service_client.reconstruct_from_hashes(request)

        if not response.is_successful():
            raise Exception("Failed to reconstruct HTML from hashes")

        print(f"    🔨 Reconstructed HTML ({len(response.body)} bytes)")

        return response.body

    def get_cached_transformation(self, target_url : str                                ,    # Target URL for cache lookup
                                        mode       : Enum__HTML__Transformation_Mode         # Transformation mode
                                  ) -> Optional[Schema__HTML__Transformation__Result]:       # Cached result or None

        if not self.cache_service or not self.cache_service.cache_config.enabled:
            return None

        if not mode.requires_caching():
            return None

        page_refs    = self.cache_service.get_or_create_page_entry(target_url)
        cache_id     = page_refs.cache_id
        data_key     = mode.to_cache_data_key()
        data_file_id = f'transformation-{mode}'

        retrieve     = self.cache_service.cache_client.data().retrieve()
        cached_html  = retrieve.data__string__with__id_and_key(cache_id     = cache_id        ,
                                                               data_key     = data_key        ,
                                                               data_file_id = data_file_id    ,
                                                               namespace    = self.namespace())

        if cached_html:
            self.cache_service.increment_cache_hit()
            print(f"         >>> Cache HIT for {mode.value}: {target_url}")

            return Schema__HTML__Transformation__Result(transformed_html       = cached_html            ,
                                                        transformation_mode    = mode                   ,
                                                        content_type           = mode.to_content_type() ,
                                                        cache_hit              = True                   ,
                                                        transformation_time_ms = Safe_Float(0.0)        )
        else:
            self.cache_service.increment_cache_miss()
            return None

    def _store_transformation_in_cache(self, target_url : str                                           ,  # Target URL for cache key
                                             mode       : Enum__HTML__Transformation_Mode               ,  # Transformation mode
                                             result     : Schema__HTML__Transformation__Result             # Result to cache
                                        ) -> None:                                                       # No return value

        if not self.cache_service or not self.cache_service.cache_config.enabled:
            return

        if not mode.requires_caching():
            return

        page_refs    = self.cache_service.get_or_create_page_entry(target_url)
        cache_id     = page_refs.cache_id
        data_key     = mode.to_cache_data_key()
        data_file_id = f'transformation-{mode}'

        self.cache_service.cache_client.data_store().data__store_string__with__id_and_key(body         = result.transformed_html,
                                                                                          cache_id     = cache_id               ,
                                                                                          data_file_id = data_file_id           ,
                                                                                          data_key     = data_key               ,
                                                                                          namespace    = self.namespace()       )

        print(f"         >>> Cached {mode.value} transformation for {target_url}")

    def store_original_html(self, target_url    : str                               ,          # Target URL for cache key
                                  original_html : str                                          # Original HTML to store
                             ) -> None:                                                       # No return value

        if not self.cache_service or not self.cache_service.cache_config.enabled:
            return

        page_refs    = self.cache_service.get_or_create_page_entry(target_url)
        cache_id     = page_refs.cache_id
        data_file_id = 'original-html'

        self.cache_service.cache_client.data_store().data__store_string__with__id_and_key(
            body         = original_html,
            cache_id     = cache_id,
            data_key     = "transformations/html",
            data_file_id = data_file_id,
            namespace    = self.namespace()
        )

    def namespace(self):                                                                  # Return cache namespace
        return self.cache_service.cache_config.namespace

    def _create_passthrough_result(self, source_html : str                          ,         # Source HTML
                                         mode        : Enum__HTML__Transformation_Mode       # Mode (OFF)
                                   ) -> Schema__HTML__Transformation__Result:                # Passthrough result

        return Schema__HTML__Transformation__Result(
            transformed_html       = source_html,
            transformation_mode    = mode,
            content_type           = "text/html",
            cache_hit              = False,
            transformation_time_ms = Safe_Float(0.0)
        )

    def _create_error_result(self, source_html : str                                ,         # Source HTML
                                   mode        : Enum__HTML__Transformation_Mode    ,         # Transformation mode
                                   start_time  : float                                        # Start time
                             ) -> Schema__HTML__Transformation__Result:                      # Error result (returns original)

        call_duration_ms = (time.time() - start_time) * 1000

        return Schema__HTML__Transformation__Result(
            transformed_html       = source_html,                                             # Return original on error
            transformation_mode    = mode,
            content_type           = "text/html",
            cache_hit              = False,
            transformation_time_ms = Safe_Float(call_duration_ms)
        )

    def _build_criterion_filters(self,
                                 mode: Enum__HTML__Transformation_Mode
                                ) -> List[Schema__Classification__Criterion_Filter]:
        """
        Build criterion filters from transformation mode.

        Converts mode-specific sentiment requirements into filter objects.
        """
        filters = []
        filter_configs = mode.get_sentiment_filters()

        print(f"         Filter Configs: {filter_configs}")
        for config in filter_configs:
            criterion   = Enum__Text__Classification__Criteria(config["criterion"])
            filter_mode = Enum__Classification__Filter_Mode(config["filter_mode"])
            threshold   = Safe_Float(config["threshold"])

            filter_obj = Schema__Classification__Criterion_Filter(criterion=criterion,
                                                                  filter_mode=filter_mode,
                                                                  threshold=threshold)
            filters.append(filter_obj)

        return filters


    def _get_logic_operator(self,
                           mode: Enum__HTML__Transformation_Mode
                          ) -> Enum__Classification__Logic_Operator:
        """Get logic operator for combining filters"""
        operator_str = mode.get_logic_operator()
        return Enum__Classification__Logic_Operator(operator_str)