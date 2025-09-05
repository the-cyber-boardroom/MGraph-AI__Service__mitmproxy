# Docker Image Tag
# Allows: letters, numbers, underscore, period, hyphen
# Common values: latest, v1.0.0, 2024-01-01, sha256:abc123
import re
from osbot_utils.type_safe.primitives.safe_str.Safe_Str import Safe_Str


class Safe_Str__Docker__Tag(Safe_Str):
    max_length       = 128                                              # Docker tag limit
    regex            = re.compile(r'[^a-zA-Z0-9._\-:]')                # Allow colon for sha256:
    regex_mode       = 'REPLACE'
    replacement_char = '-'

    def __new__(cls, value=None):
        if value is not None:
            value = str(value)

            if value == '':                                             # Handle special case: empty becomes 'latest'
                value = 'latest'
            else:
                if cls.regex and cls.regex_mode == 'REPLACE':           # Apply regex replacement for invalid chars
                    value = cls.regex.sub(cls.replacement_char, value)

                if not value.startswith('sha256:'):                     # Clean up separators (except sha256: prefix)
                    value = value.strip('.-_')

                value = re.sub(r'[-]{2,}', '-', value)                # Replace multiple consecutive separators
                value = re.sub(r'[.]{2,}', '.', value)                # Replace multiple consecutive separators
                value = re.sub(r'[_]{2,}', '_', value)                # Replace multiple consecutive separators

                if len(value) > cls.max_length:                         # Apply max length
                    value = value[:cls.max_length]
        else:
            value = 'latest'                                            # None becomes 'latest'

        instance = super().__new__(cls, value)                          # Create instance with transformed value
        return instance