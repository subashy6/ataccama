"""Nearest neighbors for attributes based on their fingerprints."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

import bidict
import faiss
import numpy
import tenacity

from aicore.common.exceptions import AICoreException
from aicore.common.resource import ReadinessDependency, RuntimeState
from aicore.term_suggestions.fingerprints import FINGERPRINT_DTYPE, FINGERPRINT_LENGTH
from aicore.term_suggestions.registry import LogId
from aicore.term_suggestions.utils import ResizableNumpyArray


if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator
    from typing import Any

    from aicore.common.logging import Logger
    from aicore.term_suggestions.database import TSDAO
    from aicore.term_suggestions.fingerprints import Fingerprint
    from aicore.term_suggestions.types import AttributeId, Neighbors


class FingerprintsIndexFullError(AICoreException):
    """Error raised when trying to add item to index with full capacity."""


class FingerprintsIndex(MutableMapping):
    """Efficiently maintains the mapping: attribute id <=> idx => contiguous fingerprint array."""

    def __init__(self, capacity, fingerprint_length=FINGERPRINT_LENGTH, fingerprint_dtype=FINGERPRINT_DTYPE):
        self.capacity = capacity

        self.id_to_idx = bidict.bidict()  # Bidirectional mapping attribute <=> its fingerprint's index in the array
        self.fingerprints = ResizableNumpyArray(
            capacity=capacity, item_shape=(fingerprint_length,), dtype=fingerprint_dtype
        )

    def __iter__(self) -> Iterator[AttributeId]:
        """Iterate over attribute ids present in the index (preserves insertion order)."""
        return iter(self.id_to_idx)

    def __getitem__(self, attribute_id: AttributeId) -> Fingerprint:
        """Get a stored fingerprint for the attribute."""
        return self.fingerprints[self.id_to_idx[attribute_id]]

    def __setitem__(self, attribute_id: AttributeId, fingerprint: Fingerprint):
        """Set a new fingerprint for the attribute."""
        fingerprint_idx = self.id_to_idx.get(attribute_id, None)

        if fingerprint_idx is None:
            if len(self) >= self.capacity:
                raise FingerprintsIndexFullError(f"Inserting into full {self!r}")

            fingerprint_idx = len(self.fingerprints)
            self.fingerprints.append(fingerprint)
            self.id_to_idx[attribute_id] = fingerprint_idx  # Write only after append (consistency in case it fails)
        else:
            self.fingerprints[fingerprint_idx] = fingerprint  # Just update the fingerprint

    def __delitem__(self, attribute_id: AttributeId):
        """Delete the attribute and its fingerprint."""
        to_remove_idx = self.id_to_idx[attribute_id]
        last_idx = len(self.fingerprints) - 1

        if to_remove_idx < last_idx:
            # Fingerprint to remove isn't last => replace it with the last (making the last the new one to remove)
            last_attr_id = self.id_to_idx.inverse[last_idx]
            self.id_to_idx.put(key=last_attr_id, val=to_remove_idx, on_dup=bidict.ON_DUP_DROP_OLD)  # Replace mapping
            self.fingerprints[to_remove_idx] = self.fingerprints[last_idx]  # Replace fingerprint
        else:
            del self.id_to_idx[attribute_id]  # Attribute to remove is already last, just drop its mapping

        self.fingerprints.pop()

    def __len__(self):
        return len(self.id_to_idx)

    def __repr__(self):
        return f"Fingerprints cache (containing {len(self)}/{self.capacity} attributes)"


class NeighborsCalculator:
    """Computes k nearest neighbors for attributes based on their fingerprints."""

    def __init__(self, fingerprints_index: FingerprintsIndex):
        self.fingerprints_index = fingerprints_index

    def top_k(self, attributes_ids: Collection[AttributeId], k: int = 20) -> list[Neighbors]:
        """Compute k nearest neighbors for the given attributes' ids (empty list for each unknown attribute id)."""
        results: list[Neighbors] = [[]] * len(attributes_ids)
        fingerprints_idxs, idxs_of_known_ids = self.map_ids(attributes_ids)

        if not fingerprints_idxs:
            return results  # All the queried attributes' ids are unknown (or none were queried)

        query = self.fingerprints_index.fingerprints[fingerprints_idxs]
        adjusted_k = min(k + 1, len(self.fingerprints_index))  # +1 for the query points themselves, later removed

        # faiss.IndexFlatL2 is equally space-efficient as our index + our index handles modifications better
        neighbors_distances, neighbors = faiss.knn(query, self.fingerprints_index.fingerprints.view, adjusted_k)
        numpy.sqrt(neighbors_distances, out=neighbors_distances)

        self.fill_results(results, idxs_of_known_ids, fingerprints_idxs, neighbors, neighbors_distances, k)

        return results

    def map_ids(self, attributes_ids: Iterable[AttributeId]) -> tuple[list[int], list[int]]:
        """Map attrs' ids to indexes of their fingerprints (skip unknown), also return indexes of known attrs' ids."""
        fingerprints_idxs = []
        idxs_of_known_ids = []

        for i, attribute_id in enumerate(attributes_ids):
            idx = self.fingerprints_index.id_to_idx.get(attribute_id, None)

            if idx is not None:
                fingerprints_idxs.append(idx)
                idxs_of_known_ids.append(i)

        return fingerprints_idxs, idxs_of_known_ids

    def fill_results(
        self,
        results: list[Neighbors],
        results_idxs: list[int],
        query_fingerprints_idxs: list[int],
        neighbors: numpy.ndarray,
        neighbors_distances: numpy.ndarray,
        k: int,
    ):
        """Filter, transform, limit and distribute the neighbors and their distances."""
        idx_to_id = self.fingerprints_index.id_to_idx.inverse
        for (attribute_neighbors, attribute_neighbors_distances, result_idx, query_fingerprint_idx) in zip(
            neighbors, neighbors_distances, results_idxs, query_fingerprints_idxs
        ):
            attribute_result = [
                (idx_to_id[neighbor_idx.item()], distance.item())  # Transform to (id, dist)
                for neighbor_idx, distance in zip(attribute_neighbors, attribute_neighbors_distances)
                if neighbor_idx != query_fingerprint_idx
            ]  # Filter out query fingerprint
            attribute_result = attribute_result[:k]  # Necessary for cases when query fingerprint not among neighbors
            results[result_idx] = attribute_result


class AttributeLimit(ReadinessDependency):
    """Resource waiting for the count of attributes (stored in the DB) to be low enough to fit into the index."""

    def __init__(
        self,
        name: str,
        logger: Logger,
        onstart_retrying: tenacity.Retrying,
        dao: TSDAO,
        limit: int,
    ) -> None:
        super().__init__(name, logger, onstart_retrying, readiness_predicate=self.is_ready, tracks_liveness=False)

        self.dao = dao
        self.limit = limit

    def __repr__(self):
        return f"{self.name!r} with limit={self.limit}"

    def is_ready(self) -> bool:
        """Indicate whether the number of attributes in database will fit into the index."""
        database = self.dao.database

        if not database.is_ready():
            self.health.not_ready(f"{database!r} is {database.health.state!r}")
            return False

        attribute_count = self.dao.get_attribute_count()
        if attribute_count > self.limit:
            self.health.not_ready(
                f"Number of attributes in the database {attribute_count!r} exceeds the limit={self.limit}"
            )
            return False

        return True

    def prepare_state_change_log_record(self) -> tuple[str, dict[str, Any]]:
        """Return log message and kwargs appropriate for the new state the index limit is in."""
        if self.health.state is not RuntimeState.NOT_READY:
            return "", {}  # Don't log anything in other states

        kwargs = {"event_id": LogId.neighbors_too_many_attributes}

        return "{self!r} is {health!r}", kwargs
