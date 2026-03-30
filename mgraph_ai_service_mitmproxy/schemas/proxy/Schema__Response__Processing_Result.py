from osbot_utils.type_safe.Type_Safe                                                        import Type_Safe
from osbot_utils.type_safe.primitives.domains.common.safe_str.Safe_Str__Text                import Safe_Str__Text
from osbot_utils.type_safe.primitives.domains.http.safe_str.Safe_Str__Http__Content_Type    import Safe_Str__Http__Content_Type
from osbot_utils.type_safe.primitives.domains.http.safe_str.Safe_Str__Http__Header__Name    import Safe_Str__Http__Header__Name
from osbot_utils.type_safe.primitives.domains.http.safe_str.Safe_Str__Http__Header__Value   import Safe_Str__Http__Header__Value
from mgraph_ai_service_mitmproxy.schemas.proxy.Schema__Proxy__Modifications                 import Schema__Proxy__Modifications
from mgraph_ai_service_mitmproxy.schemas.Safe_UInt__HTTP__Status                            import Safe_UInt__HTTP__Status
from typing                                                                                 import Dict, Optional

class Schema__Response__Processing_Result(Type_Safe):            # Complete response processing result
    modifications       : Schema__Proxy__Modifications           # Content modifications
    final_status_code   : Safe_UInt__HTTP__Status                # Final HTTP status
    final_content_type  : Safe_Str__Http__Content_Type           # Final content type
    final_body          : str                                    # Final response body  # todo: change str to Safe_Str_* class
    # final_headers       : Dict[Safe_Str__Http__Header__Name,
    #                            Safe_Str__Http__Header__Value]    # Final response headers

    final_headers       : Dict[Safe_Str__Http__Header__Name,
                               str                          ]    # todo: fix this (some websites had values bigger than 8k , one had 10k)
    content_was_modified: bool            = False                # Whether content was modified
    response_overridden : bool            = False                # Whether response was overridden
    processing_error    : Optional[Safe_Str__Text]   = None      # Error message if processing failed

    def has_error(self) -> bool:                                 # Check if processing had error
        """Check if response processing encountered an error"""
        return self.processing_error is not None

    def get_summary(self) -> Dict:                               # Get processing summary
        """Get a summary of response processing"""
        return { 'status_code': int(self.final_status_code),
                 'content_type': self.final_content_type,
                 'body_size': len(self.final_body),
                 'headers_added': len(self.modifications.headers_to_add),
                 'modified': self.content_was_modified,
                 'overridden': self.response_overridden,
                 'error': self.processing_error}