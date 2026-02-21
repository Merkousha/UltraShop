"""Simple symmetric encryption for sensitive config fields (PA-15).

Uses Django's signing framework (HMAC-based) to encrypt/decrypt values.
For production, consider django-encrypted-model-fields or Fernet.
"""

import base64

from django.core.signing import Signer, BadSignature


_signer = Signer()


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _signer.sign(plaintext)


def decrypt_value(signed: str) -> str:
    if not signed:
        return ""
    try:
        return _signer.unsign(signed)
    except BadSignature:
        return ""
