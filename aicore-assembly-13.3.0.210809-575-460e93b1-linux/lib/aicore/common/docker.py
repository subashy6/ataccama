"""Utility functions for working with Docker containers."""
from __future__ import annotations

import os
import re


def get_container_id():
    """Retrieve current container ID."""
    CONTROL_GROUP_FILENAME = "/proc/self/cgroup"

    if os.path.exists(CONTROL_GROUP_FILENAME):
        with open(CONTROL_GROUP_FILENAME, "rt") as control_group_file:
            for line in control_group_file:
                if re.match(".*/[0-9a-f]{64}$", line.strip()):
                    return re.sub(".*/([0-9a-f]{64})$", "\\1", line.strip())
