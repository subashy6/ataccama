"""Abbreviations for commonly used types in metadata fetching."""
from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Any, TypeVar

    from aicore.metadata_fetching.graphql import Entity, EntityTypeData, PropertyTypeBase, ReferencingPropertyTypeBase

    EntityId = str  # GID of an entity - together with its type uniquely identifies each entity
    EntityType = str  # Type of an entity (can be both abstract like catalogItem or concrete like tableCatalogItem)
    # Json format of mate-data returned by MMM = Union[str, int, float, bool, None, dict[str, Json], list[Json]]
    Json = Any  # Json format of mate-data returned by MMM

    PropertyType = TypeVar("PropertyType", bound=PropertyTypeBase)
    ReferencingPropertyType = TypeVar("ReferencingPropertyType", bound=ReferencingPropertyTypeBase)
    Entities = dict[EntityId, Entity]
    EntityTypesData = dict[EntityType, EntityTypeData]  # Entity types and their data (i.e. meta-meta-data)
