"""Tools for checking the licenses of PIP packages used by the application."""

from __future__ import annotations

import contextlib
import importlib.metadata

from typing import TYPE_CHECKING

import pkg_resources
import requests


if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Optional, TextIO

    from aicore.management.types import GitHubRepoName, PackageClassifiers, PackageDependencies, PackageLicense


# BSD: https://opensource.org/licenses/BSD-3-Clause (2-clause is even weaker)
# MIT: https://opensource.org/licenses/MIT
# Apache: https://www.apache.org/licenses/LICENSE-2.0
# ZPL: https://spdx.org/licenses/ZPL-2.1.html
# MPL: https://www.mozilla.org/en-US/MPL/2.0/
# ISC: https://www.isc.org/licenses/
# PSF: https://docs.python.org/3/license.html
# LGPL: https://en.wikipedia.org/wiki/GNU_Lesser_General_Public_License

# Do not add more normalized license names without getting a legal approval first!
ALLOWED_MAINSTREAM_LICENSES = {"BSD", "MIT", "Apache", "ZPL 2.1", "MPL 2.0", "ISC", "PSF"}

NORMALIZED_LICENSE_NAMES = {
    "['MIT']": "MIT",
    "The MIT License (MIT)": "MIT",
    "MIT license": "MIT",
    "MIT License": "MIT",
    "The MIT License": "MIT",
    "The MIT License: http://www.opensource.org/licenses/mit-license.php": "MIT",
    "The MIT License. See `LICENSE.txt <https://github.com/bskinn/flake8-absolute-import/blob/master/LICENSE.txt>`__": "MIT",  # noqa: E501
    "Expat License": "MIT",  # See https://en.wikipedia.org/wiki/MIT_License#Minor_ambiguity_and_variants
    "Expat license": "MIT",
    "BSD License": "BSD",
    "BSD-3-Clause": "BSD",
    "new BSD License": "BSD",
    "new BSD": "BSD",
    "3-Clause BSD License": "BSD",
    "3-clause BSD": "BSD",
    "2-clause BSD": "BSD",
    "BSD-2-Clause": "BSD",
    "BSD-like": "BSD",
    "Apache 2.0": "Apache",
    "Apache-2.0": "Apache",
    "Apache Software License 2.0": "Apache",
    "Apache License 2.0": "Apache",
    "Apache License, Version 2.0": "Apache",
    "Apache 2.0 License: https://www.apache.org/licenses/LICENSE-2.0": "Apache",
    "Apache Software License": "Apache",
    "ASL 2": "Apache",  # See https://stuvel.eu/software/rsa/
    "MPL-2.0": "MPL 2.0",
    "ISC License (ISCL)": "ISC",
    "ISC license": "ISC",
    "LGPLv3+": "LGPL",
}  # Regular expressions could break dual licenses like "BSD or MIT"


def license_from_github(repository: GitHubRepoName) -> PackageLicense:
    """Extract the license name of a GitHub repository."""
    license_name = "UNKNOWN"

    with contextlib.suppress(Exception):
        license_url = f"https://api.github.com/repos/{repository}/license"
        response = requests.get(license_url, headers={"Accept": "application/vnd.github.v3+json"}).json()
        license_name = response["license"]["name"]

    return license_name


def license_from_classifiers(package_classifiers: PackageClassifiers) -> PackageLicense:
    """Extract and normalize the license from package metadata."""
    package_license = "UNKNOWN"

    for classifier in package_classifiers:
        if classifier.startswith("License :: "):
            package_license = classifier[11:]

            if package_license.startswith("OSI Approved :: "):
                package_license = package_license[16:]

    return package_license


def extract_licenses(package_names: Iterable[str]) -> dict[str, PackageLicense]:
    """Extract licenses of given PIP packages."""
    package_licenses = {}

    for package_name in package_names:
        package_metadata = importlib.metadata.metadata(package_name)
        package_license = package_metadata["License"]
        package_url = package_metadata["Home-page"]

        if package_license in {"UNKNOWN", "Dual License"}:  # Some packages store the license only as a classifier
            package_classifiers = package_metadata.get_all("Classifier", [])
            package_license = license_from_classifiers(package_classifiers)

        if package_license == "UNKNOWN":  # Some packages indicate the license only via their GitHub repo
            if "github.com" in package_url:
                package_repository = package_url.split("github.com/")[1]
                package_license = license_from_github(package_repository)

        package_license = NORMALIZED_LICENSE_NAMES.get(package_license, package_license)
        warning = license_warning(package_name, package_license, package_url)
        package_licenses[package_name] = (package_license, package_url, warning)

    return package_licenses


def license_warning(package_name: str, package_license: PackageLicense, package_url: str) -> Optional[str]:
    """Indicate if the license needs special care before it can be used in Ataccama products."""
    if not package_license or package_license == "UNKNOWN":
        return f"    License for package {package_name!r} not available, check {package_url!r} manually"
    if package_license in ALLOWED_MAINSTREAM_LICENSES or "BSD" in package_license:  # Dual licenses often allow BSD
        return None  # The license is safe to use
    if "LGPL" in package_license:
        return f"    Package {package_name!r} is OK only if unmodified due to {package_license!r}"
    elif "GPL" in package_license or "GNU General Public License" in package_license:
        return f"*** ERROR: License {package_license!r} for package {package_name!r} is forbidden! ***"
    else:
        return f"*** ERROR: License {package_license!r} may require manual check via {package_url!r} ***"


def get_all_dependencies() -> PackageDependencies:
    """Get the required packages for all packages in current virtualenv."""
    dependencies = {}

    for distribution in pkg_resources.working_set:
        package_name = distribution.as_requirement().key  # Normalizes the name (e.g. "cx_Oracle" to "cx-oracle")
        dependencies[package_name] = {requirement.key for requirement in distribution.requires()}

    return dependencies


def get_required_packages(filenames: Iterable[str]) -> set[str]:
    """Get packages explicitely listed in given requirement files."""
    required_packages = set()  # Explicitely required packages

    for filename in filenames:
        with open(filename) as requirements:
            for line in requirements:
                if line[0].isalpha():  # Skip comments and PIP options
                    package_name = pkg_resources.Requirement.parse(line).key  # Normalizes name and strips constraints
                    required_packages.add(package_name)

    return required_packages


def resolve_dependencies(required_packages: Iterable[str], dependencies: PackageDependencies) -> set[str]:
    """Resolve the whole dependency forest with explicitely required packages on top."""
    resolved_packages = set()

    # The dependency forest is processed from the top, one floor of packages at once (to avoid recursion)
    # Each tree floor contains union of packages which are required by packages in the previous tree floor
    # Packages which were already seen in upper floors are excluded (removes the dependency cycles)
    current_floor_packages = set(required_packages)

    while True:
        next_floor_packages = set()

        for package in current_floor_packages:
            not_yet_seen_packages = dependencies[package] - resolved_packages
            next_floor_packages |= not_yet_seen_packages

        resolved_packages |= current_floor_packages

        if not next_floor_packages:  # All packages are resolved
            break

        current_floor_packages = next_floor_packages

    return resolved_packages


def get_all_licenses(include_development: bool = False) -> dict[str, PackageLicense]:
    """Get the licenses of PIP packages used by the application."""
    filenames = ["requirements.txt"]
    if include_development:
        filenames.append("requirements_dev.txt")

    # Beware, setuptools extras must be added to the dependencies manually in order to check their license!
    # See https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html?highlight=extras#dependency-management
    resolved_packages = resolve_dependencies(get_required_packages(filenames), get_all_dependencies())

    return extract_licenses(resolved_packages)


def generate_licenses_content(package_licenses: dict[str, PackageLicense], file: TextIO):
    """Generate content of README-licenses.md."""
    lines = []

    # Sort by license first, then by package name
    for package_name, (package_license, package_url, _) in sorted(
        package_licenses.items(), key=lambda package: (package[1][0], package[0])
    ):
        lines.append(f"| `{package_name}` | {package_license} | [{package_url}]({package_url}) |\n")

    file.write("| Package name | License | URL |\n")
    file.write("| ----------- | ----------- | ----------- |\n")
    file.write("".join(lines))
