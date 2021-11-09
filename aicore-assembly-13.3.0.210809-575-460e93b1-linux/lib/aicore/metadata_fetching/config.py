"""Microservice configuration."""

from __future__ import annotations

import json

from aicore.common.config import ConfigOptionsBuilder


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "mmm")
    .start_section("Metadata fetching", 160)
    .option(
        "metadata_fetcher_dump_method",
        "ataccama.one.aicore.metadata-fetcher.dump-method",
        str,
        "Defines the method of creating the metadata dump output. Possible values: `s3`, `fs`.",
        default_value="s3",
    )
    .option(
        "metadata_fetcher_fs_dump_path",
        "ataccama.one.aicore.metadata-fetcher.fs.dump-path",
        str,
        "File path of the metadata dump in the file system.",
        default_value="metadata.json",
    )
    .option(
        "metadata_fetcher_s3_endpoint",
        "ataccama.one.aicore.metadata-fetcher.s3.endpoint",
        str,
        "S3 endpoint used to dump the metadata.",
        default_value="null",
    )
    .option(
        "metadata_fetcher_s3_access_key",
        "ataccama.one.aicore.metadata-fetcher.s3.credentials.access-key",
        str,
        "Access key (aka user ID) of an account in S3 service.",
        default_value="null",
    )
    .option(
        "metadata_fetcher_s3_secret_key",
        "ataccama.one.aicore.metadata-fetcher.s3.credentials.secret-key",
        str,
        "Secret Key (aka password) of an account in S3 service.",
        default_value="null",
    )
    .option(
        "metadata_fetcher_s3_region",
        "ataccama.one.aicore.metadata-fetcher.s3.region",
        str,
        "Region name of a bucket in S3 service.",
        default_value="null",
    )
    .option(
        "metadata_fetcher_s3_bucket",
        "ataccama.one.aicore.metadata-fetcher.s3.bucket",
        str,
        "Name of a bucket in the S3 service to dump the metadata into.",
        default_value="null",
    )
    .option(
        "metadata_fetcher_s3_dump_path",
        "ataccama.one.aicore.metadata-fetcher.s3.dump-path",
        str,
        "File path of the metadata dump in the S3 bucket.",
        default_value="metadata.json",
    )
    .option(
        "metadata_fetcher_s3_tls_enabled",
        "ataccama.one.aicore.metadata-fetcher.s3.tls.enabled",
        bool,
        "Defines whether the minio client should use TLS when communicating with the S3 service.",
        default_value=True,
    )
    .option(
        "metadata_fetcher_s3_sse_enabled",
        "ataccama.one.aicore.metadata-fetcher.s3.sse.enabled",
        bool,
        "Defines whether the Server-Side Encryption with Amazon S3-Managed Keys (SSE-S3) is used.",
        default_value=True,
    )
    .option(
        "metadata_fetcher_entities",
        "ataccama.one.aicore.metadata-fetcher.fetched-entities",
        list,
        """A list of entity types defining entity instances which should be fetched from MMM. Empty list means all
        entity types. If not empty, all entity types from the list and all entity types reachable from this list by
        properties defined in ataccama.one.aicore.metadata-fetcher.traversed_properties will be fetched.""",
        default_value=json.dumps(["catalogItem"]),
    )
    .option(
        "metadata_fetcher_traversed_properties",
        "ataccama.one.aicore.metadata-fetcher.traversed-properties",
        list,
        """A list of properties which will be used to traverse the meta-metadata structure to determine entity types
         to fetch - see ataccama.one.aicore.metadata-fetcher.fetched_entities. Possible values are:
        "SE" (Single embedded), "AE" (Array embedded), "SR" (Single reference).""",
        default_value=json.dumps(["SE", "AE"]),
    )
    .options
)
