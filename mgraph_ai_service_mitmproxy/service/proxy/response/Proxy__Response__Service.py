import uuid
from typing                                                                          import Dict
from osbot_utils.type_safe.Type_Safe                                                 import Type_Safe
from osbot_utils.utils.Dev import pprint
from osbot_utils.utils.Misc import list_set

from mgraph_ai_service_mitmproxy.schemas.html                                        import Enum__HTML__Transformation_Mode
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Response_Data          import Schema__Proxy__Response_Data
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications          import Schema__Proxy__Modifications
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Response__Processing_Result   import Schema__Response__Processing_Result
from mgraph_ai_service_mitmproxy.service.html.HTML__Transformation__Service          import HTML__Transformation__Service
from mgraph_ai_service_mitmproxy.service.html_graph.HTML_Graph__Cache__Handler       import HTML_Graph__Cache__Handler
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Debug__Service                 import Proxy__Debug__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Stats__Service                 import Proxy__Stats__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Headers__Service               import Proxy__Headers__Service
from mgraph_ai_service_mitmproxy.service.proxy.Proxy__Cookie__Service                import Proxy__Cookie__Service
from mgraph_ai_service_mitmproxy.service.proxy.inject.Proxy__Inject__Service         import Proxy__Inject__Service


class Proxy__Response__Service(Type_Safe):                       # Main response processing orchestrator
    debug_service               : Proxy__Debug__Service         = None       # Debug command processing
    stats_service               : Proxy__Stats__Service                      # Statistics tracking
    headers_service             : Proxy__Headers__Service                    # Standard headers
    cookie_service              : Proxy__Cookie__Service                     # Cookie-based control
    html_transformation_service : HTML__Transformation__Service
    html_graph_handler          : HTML_Graph__Cache__Handler
    inject_service              : Proxy__Inject__Service

    def setup(self):
        self.debug_service               = Proxy__Debug__Service        ().setup()
        #self.html_transformation_service = HTML__Transformation__Service().setup()
        #self.html_graph_handler          = HTML_Graph__Cache__Handler   ()#.setup()
        return self

    def generate_request_id(self) -> str:                        # Generate unique request ID
        """Generate a unique request ID"""
        return f"req-{uuid.uuid4().hex[:12]}"

    def process_response(self, response_data : Schema__Proxy__Response_Data        # Main entry point for response processing
                          ) -> Schema__Response__Processing_Result:           # Complete processing result
        try:
            request_id       = self.generate_request_id()                                                 # todo: review if we should not be setting this request id in get_standard_headers (since that is the only place this value is used)
            body_size        = len(response_data.response.get("body", ""))                                 # Update statistics
            modifications    = Schema__Proxy__Modifications()                                          # Create modifications object
            request_headers  = response_data.request.get('headers', {})                              # Extract request headers (includes Cookie header)
            debug_params     = self.cookie_service.convert_to_debug_params(request_headers)             # Parse cookie-based debug params from request headers, The interceptor sends request headers in response_data.request['headers']
            standard_headers = self.headers_service.get_standard_headers(response_data,request_id)  # Add standard headers

            self.stats_service.increment_response(bytes_processed = body_size)
            modifications.headers_to_add.update(standard_headers)

            if self.cookie_service.has_any_proxy_cookies(request_headers):                          # Add cookie summary header if any proxy cookies present
                cookie_summary = self.cookie_service.get_cookie_summary(request_headers)
                modifications.headers_to_add["x-proxy-cookie-summary"] = str(cookie_summary)
            self.debug_service.process_debug_commands(debug_params  = debug_params ,                # Process debug commands (this may override response)
                                                      response_data = response_data,
                                                      modifications = modifications)


            if modifications.override_response:                                                     # Check if debug command overrode the response
                return self.finalize_overridden_response(response_data=response_data ,              # For overridden responses, finalize and return
                                                         modifications=modifications )
            if modifications.modified_body:                                                         # Check if content was modified (but not overridden)
                self.stats_service.increment_content_modification()

            # handle HTML-Graph and it's cache
            store_response = self.handle_html_graph_store(response_data.json())              # todo: we should be using Schema__Proxy__Response_Data here
            if store_response:
                print("     > Creating transformed_html and transformation_headers")
                transformation_headers = store_response
                transformed_html       = response_data.response.get('body')
            else:

                # Process HTML transformation based on mitm-mode cookie
                result = self.process_html_transformation(response_data   = response_data    ,
                                                          request_headers = request_headers  )
                if len(result) == 3:                # todo: fix this different return logic
                    transformed_html, transformation_headers, headers_to_remove = result
                    for h in (headers_to_remove or []):
                        modifications.headers_to_remove.append(h)
                else:
                    transformed_html, transformation_headers = result
                # if len(result) == 3:
                #     transformed_html, transformation_headers, headers_to_remove = result
                #     for h in (headers_to_remove or []):
                #         modifications.headers_to_remove.append(h)
                # else:
                #     transformed_html, transformation_headers = result
            if transformed_html:
                modifications.modified_body = transformed_html
                modifications.headers_to_add.update(transformation_headers)
                self.stats_service.increment_content_modification()

            return self._finalize_regular_response(response_data,                                   # Finalize regular response
                                                   modifications,
                                                   request_id   )

        except Exception as e:
            print('Error:' , e)
            import traceback
            traceback.print_exc()
            return self._create_error_result( response_data, str(e))        # Handle any processing errors

    def finalize_overridden_response(self, response_data  : Schema__Proxy__Response_Data,
                                           modifications  : Schema__Proxy__Modifications,
                                      ) -> Schema__Response__Processing_Result:             # Finalize a response that was overridden by debug command
        final_body = modifications.modified_body or ""

        final_headers = self.build_final_headers(response_data                      ,       # Get final headers
                                                 modifications                      ,
                                                 modifications.override_content_type,
                                                 len(final_body.encode('utf-8'))    )

        return Schema__Response__Processing_Result( modifications        = modifications                      ,
                                                    final_status_code    = modifications.override_status      ,
                                                    final_content_type   = modifications.override_content_type,
                                                    final_body           = final_body                         ,
                                                    final_headers        = final_headers                      ,
                                                    content_was_modified = True                               ,
                                                    response_overridden  = True                               )

    def _finalize_regular_response(self,                         # Finalize regular response
                                  response_data  : Schema__Proxy__Response_Data,
                                  modifications  : Schema__Proxy__Modifications,
                                  request_id     : str
                                  ) -> Schema__Response__Processing_Result:
        """Finalize a regular (non-overridden, non-preflight) response"""
        # Determine final body
        if modifications.modified_body:
            final_body = modifications.modified_body
        else:
            final_body = response_data.response.get("body", "")

        # Determine final content type
        final_content_type = response_data.response.get("content_type", "text/plain")

        # Determine final status
        final_status = response_data.response.get("status_code", 200)

        # Build final headers
        final_headers = self.build_final_headers(response_data                  ,
                                                 modifications                  ,
                                                 final_content_type             ,
                                                 len(final_body.encode('utf-8')))

        return Schema__Response__Processing_Result( modifications        = modifications                    ,
                                                    final_status_code    = final_status                     ,
                                                    final_content_type   = final_content_type               ,
                                                    final_body           = final_body                       ,
                                                    final_headers        = final_headers                    ,
                                                    content_was_modified = bool(modifications.modified_body),
                                                    response_overridden  = False                            )

    def build_final_headers(self, response_data   : Schema__Proxy__Response_Data,  # Build the complete set of final headers
                                  modifications   : Schema__Proxy__Modifications,
                                  content_type    : str,
                                  content_length  : int
                             ) -> Dict[str, str]:                 # Final headers

        final_headers   = response_data.response.get("headers", {}).copy()                            # Start with original response headers
        content_headers = self.headers_service.get_content_headers(content_type, content_length)    # Add content headers
        final_headers.update(content_headers)

        # Add all headers from modifications (includes standard, debug)
        final_headers.update(modifications.headers_to_add)

        # Remove headers that should be removed
        for header_to_remove in modifications.headers_to_remove:
            final_headers.pop(header_to_remove, None)

        final_headers = {k: str(v) for k, v in final_headers.items()}           # ensure all a strings
        return final_headers

    def _create_error_result(self,                               # Create error result
                            response_data : Schema__Proxy__Response_Data,
                            error_message : str
                            ) -> Schema__Response__Processing_Result:
        """Create an error result when processing fails"""
        error_body = f"Response processing error: {error_message}"

        return Schema__Response__Processing_Result(
            modifications        = Schema__Proxy__Modifications(),
            final_status_code    = 500,
            final_content_type   = "text/plain",
            final_body          = error_body,
            final_headers       = { "content-type": "text/plain"            ,
                                    "content-length": str(len(error_body))  ,
                                    "X-Processing-Error": "true"            },
            content_was_modified = False,
            response_overridden  = False,
            processing_error    = error_message
        )

    # todo: refactor tuple with Type_Safe class
    def process_html_transformation(self,                                                   # Process HTML transformation based on mitm-mode cookie
                                          response_data  : Schema__Proxy__Response_Data,    # Response data with HTML
                                          request_headers: Dict[str, str]                   # Request headers with cookies
                                ) -> tuple:                                                 # (transformed_html, headers_to_add)

        extra_sites_to_inject = ["www.bbc.co.uk"]                           # sites where setting the mitm-mode cookie doesn't work reliably
        host        = response_data.request.get('host')
        if host in extra_sites_to_inject:
            transformation_mode = Enum__HTML__Transformation_Mode.INJECT
            print(">>>>>>>> transformation_mode", transformation_mode)
        else:
            transformation_mode = self.cookie_service.get_mitm_mode(request_headers)        # Extract transformation mode from cookie

        if not transformation_mode.is_active():                                          # No transformation needed
            return (None, {})
        if transformation_mode == Enum__HTML__Transformation_Mode.CACHE:
            return (None, {})


        if transformation_mode == Enum__HTML__Transformation_Mode.INJECT:
            response_body = response_data.response.get("body", "")
            content_type  = response_data.response.get("headers", {}).get("content-type", "")
            if "text/html" not in content_type.lower():
                return (None, {}, [])
            target_url = self._construct_target_url(response_data)

            return self.inject_service.inject_script_into_html(
                html=response_body, target_url=target_url)

        response_body = response_data.response.get("body", "")                           # Extract HTML from response
        target_url    = self._construct_target_url(response_data)

        if not response_body:                                                            # No body to transform
            return (None, {})

        content_type = response_data.response.get("headers", {}).get("content-type", "")    # Only transform HTML content
        if "text/html" not in content_type.lower():
            print(f"         >>> Skipping transformation - not HTML: {content_type}")
            return (None, {})

        print(f"    🔄 Transforming HTML with mode: {transformation_mode.value}")

        self.html_transformation_service.store_original_html(                            # Store original HTML for provenance
            target_url    = target_url     ,
            original_html = response_body
        )

        result = self.html_transformation_service.transform_html(                        # Perform transformation
            source_html = response_body       ,
            target_url  = target_url          ,
            mode        = transformation_mode
        )

        headers_to_add = result.to_headers()                                             # Generate transformation headers

        return (result.transformed_html, headers_to_add)


    def _construct_target_url(self, response_data: 'Schema__Proxy__Response_Data'       # Response data
                              ) -> str:                                                  # Constructed URL
        """Construct the target URL from response data"""
        request    = response_data.request
        scheme     = request.get('scheme', 'https')
        host       = request.get('host', '')
        port       = request.get('port', 443)
        path       = request.get('path', '/')

        if (scheme == 'https' and port == 443) or (scheme == 'http' and port == 80):    # Standard ports - omit from URL
            return f"{scheme}://{host}{path}"
        else:
            return f"{scheme}://{host}:{port}{path}"


    # todo: move this HTML Graph code to separate class

    def extract_cookies_from_request(self, response_data: dict                  # Get cookies from request in response_data
                                      ) -> Dict[str, str]:
        request = response_data.get("request", {})
        headers = request.get("headers", {})
        cookies = {}
        cookie_header = headers.get("cookie", headers.get("Cookie", ""))

        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    key, value = item.strip().split("=", 1)
                    cookies[key.strip()] = value.strip()

        return cookies


    def handle_html_graph_store(self, response_data: dict                       # Store HTML on cache miss
                                 ) -> Dict[str, str]:                           # Returns headers to add
        if self.html_graph_handler is None:
            return {}

        headers = response_data.get('request', {}).get("headers", {})
        mitm_mode = self.cookie_service.get_mitm_mode(headers)

        cookies = self.extract_cookies_from_request(response_data)

        # if self.html_graph_handler.is_cache_mode(cookies) is False:
        #     return {}                                                           # Not in cache mode
        if mitm_mode == Enum__HTML__Transformation_Mode.CACHE:
            store_headers = self.html_graph_handler.store_html(response_data)
            return store_headers
        else:
            return {}


    def process_cache_mode_response(self, response_data: dict                   # Handle full response for cache mode
                                     ) -> dict:                                 # Returns response dict
        store_headers = self.handle_html_graph_store(response_data)

        response         = response_data.get("response", {})
        existing_headers = dict(response.get("headers", {}))
        existing_headers.update(store_headers)

        return {"status_code": response.get("status_code", 200),
                "body"       : response.get("body", "")        ,
                "headers"    : existing_headers                }