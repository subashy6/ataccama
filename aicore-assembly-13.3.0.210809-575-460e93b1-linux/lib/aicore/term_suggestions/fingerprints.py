"""Definition of type and size of the fingerprints."""

from __future__ import annotations

import numpy


Fingerprint = numpy.ndarray  # 128 statistical features of data stored in one attribute of customer database
FINGERPRINT_DTYPE = numpy.float32
FINGERPRINT_LENGTH = 128
FINGERPRINT_SIZE = FINGERPRINT_LENGTH * 4  # [bytes]
