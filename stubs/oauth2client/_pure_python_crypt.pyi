from oauth2client import _helpers as _helpers
from typing import Any

_PKCS12_ERROR: str
_POW2: Any
_PKCS1_MARKER: Any
_PKCS8_MARKER: Any
_PKCS8_SPEC: Any

def _bit_list_to_bytes(bit_list: Any): ...

class RsaVerifier:
    _pubkey: Any = ...
    def __init__(self, pubkey: Any) -> None: ...
    def verify(self, message: Any, signature: Any): ...
    @classmethod
    def from_string(cls, key_pem: Any, is_x509_cert: Any): ...

class RsaSigner:
    _key: Any = ...
    def __init__(self, pkey: Any) -> None: ...
    def sign(self, message: Any): ...
    @classmethod
    def from_string(cls, key: Any, password: str = ...): ...
