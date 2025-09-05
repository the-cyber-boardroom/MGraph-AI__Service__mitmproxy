from osbot_utils.type_safe.primitives.safe_str.Safe_Str              import Safe_Str
import re

# Docker Image Name
# Format: [registry/]namespace/name
# Allows: lowercase letters, numbers, underscore, period, hyphen, slash
class Safe_Str__Docker__Image_Name(Safe_Str):
    max_length       = 255                                              # Docker registry limit
    regex            = re.compile(r'[^a-z0-9._/\-]')                    # Remove invalid chars
    replacement_char = '-'                                              # Replace with hyphen

    def __new__(cls, value=None):
        if value:
            value = str(value).lower()                                  # Convert to lowercase first

            if cls.regex and cls.regex_mode == 'REPLACE':
                value = cls.regex.sub(cls.replacement_char, value)      # Apply regex replacement for invalid chars

            value = value.strip('.-/')                                  # Clean up separators

            value = re.sub(r'[-]{2,}', '-', value)                    # Replace multiple consecutive - with single
            value = re.sub(r'[.]{2,}', '.', value)                    # Replace multiple consecutive .  with single
            value = re.sub(r'[/]{2,}', '/', value)                     # Replace multiple consecutive / with single

            parts = value.split('/')                                    # Ensure valid registry/namespace/name format
            if len(parts) > 3:                                          # Too many slashes
                value = '/'.join(parts[-3:])                            # Keep only last 3 parts (registry/namespace/name)

            if len(value) > cls.max_length:                             # Apply max length
                value = value[:cls.max_length]

        instance = super().__new__(cls, value)                          # Create instance with transformed value
        return instance

