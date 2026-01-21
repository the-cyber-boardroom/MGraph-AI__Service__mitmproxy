import hashlib
import uuid

from osbot_utils.type_safe.primitives.domains.cryptography.safe_str.Safe_Str__Cache_Hash import Safe_Str__Cache_Hash

# todo: refactor out once the next version of osbot-utils has been installed (which has a new() method in the Safe_Str__Cache_Hash primitive)
@staticmethod
def cache_hash__new() -> Safe_Str__Cache_Hash:
    value = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    return Safe_Str__Cache_Hash(value)