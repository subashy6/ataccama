"""Job for fetching metadata from MMM."""
from __future__ import annotations

import collections
import io
import json
import math

from typing import TYPE_CHECKING

import minio
import minio.sse

from aicore.common.config import ConfigurationError
from aicore.common.graphql import GraphQLResponseException
from aicore.common.microservice import Microservice, sleep_between_periods
from aicore.common.utils import human_readable_size, random_correlation_id
from aicore.metadata_fetching import METADATA_FETCHER
from aicore.metadata_fetching.graphql import (
    METAMETADATA_QUERY,
    Metadata,
    expand_entity_types,
    generate_instance_queries,
    simplify_single_entity_type_response,
)
from aicore.metadata_fetching.registry import LogId


if TYPE_CHECKING:
    from typing import Callable

    from aicore.common.resource import Health
    from aicore.metadata_fetching.graphql import EntityType, Json


class MetadataFetcher(Microservice):
    """A job which fetches metadata from MMM and dumps it into S3 bucket."""

    def __init__(self, config):
        super().__init__("metadata_fetcher", config)

        self.add_external_dependency("mmm")
        self.mmm_client = self.graphql_client("mmm")

    def run_processing_forever(self, processing_thread_health: Health) -> None:
        """Fetch metadata from MMM, create a dump of it and shut down the whole microservice."""
        # Disable liveness checks for this thread as e.g. the metadata fetching can take a long time
        processing_thread_health.tracks_liveness = False
        dump = self.get_dump_function(self.config.metadata_fetcher_dump_method)

        dump({})  # Dump dummy metadata to verify dumping works before we start fetching the real metadata

        metadata = self.fetch_metadata()
        dump_info = dump(metadata)

        self.logger.info(
            f"Created dump, {', '.join(f'{key}: {{{key}!r}}' for key in dump_info)}",
            **dump_info,
            message_id=LogId.dump_created,
            _color="<white><bold>",
        )

        self.shutdown()  # Trigger shutdown of the microservice
        # No resource should shut itself down before it's asked to do so
        sleep_between_periods(processing_thread_health, sleep=math.inf)  # Stay alive until asked to shut down

    def dump_to_file(self, metadata: dict) -> dict[str, str]:
        """Dump the metadata into a file."""
        path = self.config.metadata_fetcher_fs_dump_path  # Has a default value

        with open(path, "wt") as file:
            json.dump(metadata, file)
            size = file.tell()

        return {
            "path": path,
            "size": human_readable_size(size),
        }

    def dump_to_s3(self, metadata: dict) -> dict[str, str]:
        """Dump the metadata into an S3 bucket."""
        endpoint = self.config.metadata_fetcher_s3_endpoint
        access_key = self.config.metadata_fetcher_s3_access_key
        secret_key = self.config.metadata_fetcher_s3_secret_key
        region = self.config.metadata_fetcher_s3_region  # Isn't always necessary
        secure = self.config.metadata_fetcher_s3_tls_enabled  # Has a default value
        bucket = self.config.metadata_fetcher_s3_bucket
        dump_path = self.config.metadata_fetcher_s3_dump_path  # Has a default value
        sse_enabled = self.config.metadata_fetcher_s3_sse_enabled  # Has a default value

        if endpoint is None or access_key is None or secret_key is None or bucket is None:
            raise ConfigurationError("S3 endpoint, access key, secret key and bucket must all be specified")

        metadata_bytes = json.dumps(metadata).encode("utf-8")
        size = len(metadata_bytes)

        client = minio.Minio(endpoint, access_key, secret_key, region=region, secure=secure)
        sse = minio.sse.SseS3() if sse_enabled else None
        result = client.put_object(bucket, dump_path, io.BytesIO(metadata_bytes), size, "application/json", sse=sse)

        return {
            "path": result.object_name,
            "size": human_readable_size(size),
            "bucket": result.bucket_name,
            "endpoint": endpoint,
            "etag": result.etag,
        }

    def get_dump_function(self, method_name: str) -> Callable[[dict], dict[str, str]]:
        """Return a dump function according to the nome of the dump method."""
        dump_functions = {
            "fs": self.dump_to_file,
            "s3": self.dump_to_s3,
        }

        try:
            return dump_functions[method_name]
        except KeyError:
            raise ConfigurationError(
                f"Unknown metadata dump method: {method_name!r}, supported methods: {list(dump_functions.keys())}"
            ) from None

    def fetch_metadata(self) -> dict:
        """Fetch Metadata from MMM."""
        # Fetch meta-metadata
        mmd_correlation_id = random_correlation_id()
        mmd = self.mmm_client.send(METAMETADATA_QUERY, mmd_correlation_id)

        metadata_dict = {"mmd": mmd}
        metadata = Metadata(metadata_dict)
        if metadata.skipped_property_types:
            self.logger.warning(
                "Some property types are not supported and will be skipped: {skipped_property_types}",
                skipped_property_types=metadata.skipped_property_types,
                message_id=LogId.property_types_unsupported,
                correlation_id=mmd_correlation_id,
            )
        if metadata.skipped_entity_types:
            self.logger.warning(
                "Some entity types cannot be fetched: {skipped_entity_types}",
                skipped_entity_types=metadata.skipped_entity_types,
                message_id=LogId.entity_types_unsupported,
                correlation_id=mmd_correlation_id,
            )

        # Selected entities or all present
        entities = self.config.metadata_fetcher_entities or list(metadata.entity_types_data.keys())
        traversed_properties = self.config.metadata_fetcher_traversed_properties
        metadata_dict["parameters"] = {"entities": entities}

        instances: collections.defaultdict[EntityType, list[Json]] = collections.defaultdict(list)
        expanded_entity_type_names = expand_entity_types(
            entities, traversed_properties, metadata.composition, metadata.inheritance
        )
        expanded_entity_types_data = [metadata.entity_types_data[name] for name in expanded_entity_type_names]

        for entity_type, base_type, query in generate_instance_queries(
            expanded_entity_types_data, metadata.inheritance
        ):
            instances_correlation_id = random_correlation_id()
            self.logger.info(
                "Fetching entities of type {entity_type}[{base_type}]",
                entity_type=entity_type,
                base_type=base_type,
                message_id=LogId.fetching_entity,
                correlation_id=instances_correlation_id,
            )
            try:
                response = self.mmm_client.send(query, instances_correlation_id)
            except GraphQLResponseException as error:
                self.logger.warning(
                    "Entities of type {entity_type}[{base_type}] could not be fetched, error message: {error_message}",
                    entity_type=entity_type,
                    base_type=base_type,
                    error_message=str(error),
                    message_id=LogId.entities_fetching_error,
                    correlation_id=instances_correlation_id,
                )
            else:
                list_of_entities = simplify_single_entity_type_response(response, metadata.entity_types_data)
                instances[base_type].extend(list_of_entities)  # Store under the base type

        metadata_dict["instances"] = instances
        metadata_info = str(Metadata(metadata_dict))
        self.logger.info(
            "Fetched in total: {metadata_info}",
            metadata_info=metadata_info,
            message_id=LogId.fetched_info,
            correlation_id=mmd_correlation_id,
        )

        return metadata_dict


JOBS = {
    METADATA_FETCHER: MetadataFetcher,
}
