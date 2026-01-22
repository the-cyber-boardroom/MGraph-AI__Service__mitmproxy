from enum import Enum
from typing import List, Dict

from mgraph_ai_service_mitmproxy.schemas.semantic_text.client.enums.Enum__Text__Transformation__Mode import Enum__Text__Transformation__Mode


# todo: move the logic/code below into a helper class
# todo: renamed HTML to Html
                                                   # Validation test (html→dict→html)
class Enum__HTML__Transformation_Mode(str, Enum):
    # Existing modes
    OFF           = "off"
    DICT          = "dict"
    XXX           = "xxx"              # All text → xxx (no filtering)
    HASHES        = "hashes"           # All text → hashes (no filtering)

    # CACHE Modes
    CACHE              = "cache"                                                            # Passive HTML Graph cache

    # 🆕 Sentiment-filtered modes
    XXX_NEGATIVE          = "xxx-negative"           # Show positive sentiment (negative > 0.3)
    XXX_NEGATIVE_05       = "xxx-negative-0.5"       # Show positive sentiment (negative > 0.5)
    XXX_NEGATIVE_1        = "xxx-negative-1"         # Show positive sentiment (negative > 0.1)
    XXX_NEGATIVE_2        = "xxx-negative-2"         # Show positive sentiment (negative > 0.2)
    XXX_NEGATIVE_3        = "xxx-negative-3"         # Show positive sentiment (negative > 0.3)
    XXX_NEGATIVE_4        = "xxx-negative-4"         # Show positive sentiment (negative > 0.4)
    # XXX_HIDE_POSITIVE     = "xxx-hide-positive"      # Mask only positive sentiment
    # XXX_HIDE_NEGATIVE     = "xxx-hide-negative"      # Mask only negative sentiment
    # XXX_HIDE_NEUTRAL      = "xxx-hide-neutral"       # Mask only neutral sentiment
    # XXX_HIDE_MIXED        = "xxx-hide-mixed"         # Mask only mixed sentiment

    XXX_RANDOM    =  "xxx-random" ,
    XXX_TEXT_HASH =  "xxx-text-hash" ,


    # HASHES_POSITIVE  = "hashes-positive"   # Show hashes for positive
    # HASHES_NEGATIVE  = "hashes-negative"   # Show hashes for negative

    # Existing random/local modes
    #XXX_RANDOM       = "xxx-random"
    HASHES_RANDOM    = "hashes-random"
    ABCDE_BY_SIZE    = "abcde-by-size"
    ROUNDTRIP        = "roundtrip"

    @classmethod
    def from_cookie_value(cls, cookie_value: str                                    # Parse cookie value to mode
                         ) -> 'Enum__HTML__Transformation_Mode':                    # Transformation mode or OFF
        """Parse mitm-mode cookie value to transformation mode"""
        if not cookie_value:
            return cls.OFF

        cookie_value_lower = cookie_value.lower().strip()

        for mode in cls:
            if mode.value == cookie_value_lower:
                return mode

        return cls.OFF                                                              # Default to OFF for unknown values

    def is_active(self) -> bool:                                                    # Check if mode requires transformation
        """Check if this mode requires transformation (not OFF)"""
        return self != Enum__HTML__Transformation_Mode.OFF

    def is_local_transformation(self) -> bool:                                      # Check if this transformation is processed locally (not via HTML Service)
        return self in (Enum__HTML__Transformation_Mode.XXX_RANDOM    ,
                        Enum__HTML__Transformation_Mode.HASHES_RANDOM ,
                        Enum__HTML__Transformation_Mode.ABCDE_BY_SIZE )

    def requires_caching(self) -> bool:                                             # Check if mode should be cached
        """Check if this transformation should be cached"""
        return self.is_active()                                                     # All active modes are cacheable

    def to_endpoint_path(self) -> str:                                              # Convert mode to HTML Service endpoint path"""
        mapping = {
            Enum__HTML__Transformation_Mode.DICT          : "/html/to/tree/view"       , # BUG this should be to html/to/dict and we should add new TREE_VIEW mode which would be the one that points to /html/to/tree/view
            Enum__HTML__Transformation_Mode.XXX           : "/html/to/html/xxx"        ,
            Enum__HTML__Transformation_Mode.XXX_RANDOM    : ""                         ,  # Empty = local processing
            Enum__HTML__Transformation_Mode.HASHES        : "/html/to/html/hashes"     ,
            Enum__HTML__Transformation_Mode.HASHES_RANDOM : ""                         , # Empty = local processing
            Enum__HTML__Transformation_Mode.ABCDE_BY_SIZE : ""                         ,
            Enum__HTML__Transformation_Mode.ROUNDTRIP     : "/html/to/html"
        }
        return mapping.get(self, "")

    def to_content_type(self) -> str:                                               # Get response content type
        """Get content type for this transformation mode"""
        if self == Enum__HTML__Transformation_Mode.DICT:
            return "text/plain"                                                     # Tree view is plain text
        else:
            return "text/html"                                                      # All other modes return HTML

    def to_cache_data_key(self) -> str:                                             # Get cache storage key
        """Get cache data key for this transformation mode"""
        mapping = {
            Enum__HTML__Transformation_Mode.DICT          : "transformations/html-dict"    ,
            Enum__HTML__Transformation_Mode.XXX           : "transformations/html-xxx"     ,
            Enum__HTML__Transformation_Mode.XXX_RANDOM    : ""                             ,   # Not cached
            Enum__HTML__Transformation_Mode.HASHES        : "transformations/html-hashes"  ,
            Enum__HTML__Transformation_Mode.ABCDE_BY_SIZE : ""                             ,
            Enum__HTML__Transformation_Mode.ROUNDTRIP     : "transformations/html-roundtrip"
        }
        return mapping.get(self, "")

    def str(self):
        return self.value


    def uses_sentiment_analysis(self) -> bool:                          # Check if mode requires AWS Comprehend sentiment analysis
        #return False
        sentiment_modes = {
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE  ,
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE_05,
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE_1,
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE_2,
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE_3,
            Enum__HTML__Transformation_Mode.XXX_NEGATIVE_4,

            # Enum__HTML__Transformation_Mode.XXX_HIDE_POSITIVE,
            # Enum__HTML__Transformation_Mode.XXX_HIDE_NEGATIVE,
            # Enum__HTML__Transformation_Mode.XXX_HIDE_NEUTRAL ,
            # Enum__HTML__Transformation_Mode.XXX_HIDE_MIXED   ,

            # Enum__HTML__Transformation_Mode.HASHES_POSITIVE,
            # Enum__HTML__Transformation_Mode.HASHES_NEGATIVE,
            #Enum__HTML__Transformation_Mode.XXX_EXTREME,
            #Enum__HTML__Transformation_Mode.XXX_OPINIONATED,
        }
        return self in sentiment_modes

    # improve this since we need to take into account that positive(ish) will also have good neutral and mixed
    def get_sentiment_filters(self) -> List[Dict]:      # Get sentiment filters for this mode
        #return []
        filters_map = { Enum__HTML__Transformation_Mode.XXX_NEGATIVE        : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.3}],
                        Enum__HTML__Transformation_Mode.XXX_NEGATIVE_05     : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.05}],
                        Enum__HTML__Transformation_Mode.XXX_NEGATIVE_1      : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.1}],
                        Enum__HTML__Transformation_Mode.XXX_NEGATIVE_2      : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.2}],
                        Enum__HTML__Transformation_Mode.XXX_NEGATIVE_3      : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.3}],
                        Enum__HTML__Transformation_Mode.XXX_NEGATIVE_4      : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.4}]}
                        # Enum__HTML__Transformation_Mode.XXX_HIDE_POSITIVE   : [{"criterion": "positive", "filter_mode": "above", "threshold": 0.7} ],
                        # Enum__HTML__Transformation_Mode.XXX_HIDE_NEGATIVE   : [{"criterion": "negative", "filter_mode": "above", "threshold": 0.7} ],
                        # Enum__HTML__Transformation_Mode.XXX_HIDE_NEUTRAL    : [{"criterion": "neutral" , "filter_mode": "above", "threshold": 0.6} ],
                        # Enum__HTML__Transformation_Mode.XXX_HIDE_MIXED      : [{"criterion": "mixed"   , "filter_mode": "above", "threshold": 0.8}]}
        return filters_map.get(self, [])

    def get_logic_operator(self) -> str:        # Get logic operator for combining filters
        return "or"                             # for now default to "or"
        # if self == Enum__HTML__Transformation_Mode.XXX_EXTREME:             # XXX_EXTREME uses OR (match positive OR negative)
        #     return "or"
        # return "and"                                                        # Default: all filters must match

    def to_visual_mode(self) -> Enum__Text__Transformation__Mode:       # Convert to visual transformation mode (xxx, hashes, etc)
        if 'xxx' in self.value:
            return Enum__Text__Transformation__Mode.XXX
        elif 'hashes' in self.value:
            return Enum__Text__Transformation__Mode.HASHES
        return Enum__Text__Transformation__Mode.XXX