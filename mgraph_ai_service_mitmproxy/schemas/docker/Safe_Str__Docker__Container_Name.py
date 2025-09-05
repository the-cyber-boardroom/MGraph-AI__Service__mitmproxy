from osbot_utils.type_safe.primitives.safe_str.Safe_Str import Safe_Str
import re

# Docker Container Name
# Docker allows: lowercase letters, numbers, underscore, period, hyphen
# Must start with alphanumeric, 1-242 chars
class Safe_Str__Docker__Container_Name(Safe_Str):                       # Inherit from Safe_Str, not Safe_Id
    max_length       = 242                                              # Docker max is 242 chars
    regex            = re.compile(r'[^a-z0-9._\-]')                    # Keep only valid Docker chars

    def __new__(cls, value=None):
        if value:                                                       # Convert to lowercase first
            value = str(value).lower()                                  # Docker prefers lowercase

        # Create instance with transformed value
        return super().__new__(cls, value)