"""Utilities used for internal encryption."""

from __future__ import annotations

import base64
import binascii
import re

import cryptography.hazmat.primitives.ciphers
import cryptography.hazmat.primitives.ciphers.algorithms
import cryptography.hazmat.primitives.ciphers.modes
import cryptography.hazmat.primitives.padding

from aicore.common.constants import ENCODING
from aicore.common.exceptions import AICoreException


ENCRYPTION_PREFIX = "crypted:"
SUPPORTED_ALGORITHMS = {"AES_CBC": cryptography.hazmat.primitives.ciphers.algorithms.AES}
SUPPORTED_CONTEXTS = {
    "I": "internal",
    "P": "properties",
}


class EncryptionPropertyError(AICoreException):
    """Error signifying bad format of encrypted property."""


def parse_encrypted_property_info(encrypted_property: str):
    """Parse information about encrypted property.

    Note: Ataccama uses following format: crypted:<ALGORITHM>(<key_alias>):<context>:<base64_encrypted_string>
        - ALGORITHM - algorithm used to encrypt the value - mandatory
        - key_alias - alias (in the keystore) of the key used to encrypt the value - optional
        - context - defines what keystore should be used - optional
        - base64_encrypted_string - value that is encrypted and base64 encoded
    """
    if not encrypted_property.startswith(ENCRYPTION_PREFIX):
        raise EncryptionPropertyError("Encrypted property should start with `crypted:` prefix")

    encrypted_property = encrypted_property.removeprefix(ENCRYPTION_PREFIX)
    parts = encrypted_property.split(":")

    # Context is optional - the property can have either 2 or 3 parts
    if len(parts) < 2 or len(parts) > 3:
        raise EncryptionPropertyError(f"Invalid number of colon-delimited parts: {len(parts)}, expected 2 or 3")

    alias_search = re.match("([^(]*)\\((.*)\\)", parts[0])

    if alias_search:
        algorithm = alias_search.groups()[0]
        alias = alias_search.groups()[1]
    else:
        algorithm = parts[0]
        alias = None

    if algorithm not in SUPPORTED_ALGORITHMS:
        raise EncryptionPropertyError(f"Unsupported encryption algorithm {algorithm!r}")

    alias = alias or "aes_cbc"
    context_key = parts[1] if len(parts) == 3 else "P"

    if context_key not in SUPPORTED_CONTEXTS:
        raise EncryptionPropertyError(f"Unknown encryption context key {context_key!r}")

    context = SUPPORTED_CONTEXTS[context_key]
    property_value = parts[-1]

    if not property_value:
        raise EncryptionPropertyError("Missing encrypted value")

    try:
        property_value = base64.b64decode(property_value)
    except binascii.Error as error:
        raise EncryptionPropertyError("Encrypted property isn't base64-encoded") from error

    return algorithm, alias, context, property_value


def decrypt_value(algorithm: str, key: bytes, value: bytes) -> str:
    """Decrypt value based on Ataccama internal encryption rules."""
    decryption_algorithm = SUPPORTED_ALGORITHMS[algorithm]

    # Initial vector needs to be supplied - java puts it in the beginning of the encrypted string
    block_bytes_size = int(decryption_algorithm.block_size / 8)
    initial_vector = value[:block_bytes_size]
    encrypted_value = value[block_bytes_size:]

    # We support only CBC mode for now
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        decryption_algorithm(key), cryptography.hazmat.primitives.ciphers.modes.CBC(initial_vector)
    )

    decryptor = cipher.decryptor()
    decrypted_value = decryptor.update(encrypted_value) + decryptor.finalize()

    # Java uses PKCS7 padding, too
    unpadder = cryptography.hazmat.primitives.padding.PKCS7(decryption_algorithm.block_size).unpadder()
    unpadded_value = unpadder.update(decrypted_value) + unpadder.finalize()

    return unpadded_value.decode(ENCODING)
