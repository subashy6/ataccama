"""Constants used by the infrastructure code."""

from __future__ import annotations


# Do not put ML related constants here - even if they are shared by multiple algorithms!


# Generic constants (unrelated to Ataccama)
ENCODING = "utf-8"  # Encoding used to encode and decode strings to bytes
DEFAULT_HOST = "localhost"

# Ataccama specific constants (defined as part of CTX features)
# Headers must be lowercase, see https://tools.ietf.org/html/rfc7540#section-8.1.2
AUTHENTICATION_HEADER = "www-authenticate"
CORRELATION_ID_HEADER = "x-correlation-id"
CORRELATION_ID_SIZE = 6  # string of length 6
UUID_SIZE = 36  # [ASCII characters]
# UUID has 32 hex digits (128 bits), see https://tools.ietf.org/html/rfc4122.html#section-4.1
# but Java implementation uses UUID.randomUUID().toString() which adds 4 hyphens

# AI Core specific constants (unrelated to the rest of the platform)
RESPONSIVENESS_PERIOD = 0.1  # [s] A period in which one should check at least once e.g. whether to shutdown
STATE_CHANGE_TIMEOUT = 5  # [s] How long it should take for a resource at most to start or to stop

# https://docs.sqlalchemy.org/en/13/dialects/
# Oracle not supported due to -> ONE-21741
# MSSQL not supported due to -> ONE-22155
# Config instance needs to know about supported dialects and importing from `common.database` would implicitly import
# sqlalchemy, adding extra ~7MB of memory usage for microservices that might not utilize the DB at all
SUPPORTED_DIALECTS = ["postgresql"]
