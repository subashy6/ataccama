"""Fetching meta-data about entity types and their instances."""

from __future__ import annotations

import abc
import collections
import dataclasses
import itertools
import pprint
import string

from typing import TYPE_CHECKING

import more_itertools


if TYPE_CHECKING:
    from typing import Any, Collection, Iterable, Iterator, Optional

    from aicore.metadata_fetching.types import (
        Entities,
        EntityId,
        EntityType,
        EntityTypesData,
        Json,
        PropertyType,
        ReferencingPropertyType,
    )


CORE_PERSISTENCE_TRAIT_NAME = "core:persistence"

# Query for fetching all entity types and their properties
METAMETADATA_QUERY = """
    {
        _modelMetadata {
            entities(entityName: "metadata") {
                entityName
                superEntities
                traits {
                  traitName
                   ... on PersistenceTrait {
                    storedAsSimple
                  }
                }
                properties {
                    name
                    __typename
                     ... on SingleEmbeddedPropertyMetadata {
                        entityName
                     }
                     ... on ArrayEmbeddedPropertyMetadata {
                        entityName
                     }
                     ... on ScalarPropertyMetadata {
                        dataType
                     }
                     ... on SingleReferencePropertyMetadata {
                        entityName
                    }
                }
            }
        }
    }
"""

# Query for fetching all instances of given entity type with all possible properties they can have
SINGLE_ENTITY_QUERY_TEMPLATE = string.Template(
    """
    {
        $entity_name(versionSelector: {
            publishedVersion: true
        }) {
            edges {
                node {
                    gid
                    type
                    publishedVersion {
                        $properties
                    }
                }
            }
        }
    }
"""
)


@dataclasses.dataclass
class PropertyTypeBase(abc.ABC):
    """Base class for meta-data about properties."""

    type_name: str

    @classmethod
    @abc.abstractmethod
    def from_metadata(cls: type[PropertyType], metadata: dict[str, str]) -> PropertyType:
        """Create the property type from mmd metadata json."""

    @abc.abstractmethod
    def create_instance(self, property_info: dict[str, Any]) -> PropertyBase:
        """Create an instance of the property and fill fields from a MMD dict."""

    @abc.abstractmethod
    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""


@dataclasses.dataclass
class ReferencingPropertyTypeBase(PropertyTypeBase, abc.ABC):
    """Property referencing entities."""

    entity_type: Optional[EntityType]  # Type of the entity(entities) being referenced

    @classmethod
    def from_metadata(cls: type[ReferencingPropertyType], metadata: dict[str, str]) -> ReferencingPropertyType:
        """Create the property type from mmd metadata json."""
        return cls(metadata["name"], metadata["entityName"])

    def fill_metadata(self, metadata: dict[str, str]):
        """Fill metadata of the referenced entity(entities) type from a MMD dict."""
        self.entity_type = metadata["entityName"]


@dataclasses.dataclass
class ScalarPropertyType(PropertyTypeBase):
    """Meta-data about a scalar property."""

    data_type: str

    @classmethod
    def from_metadata(cls, metadata: dict[str, str]) -> ScalarPropertyType:
        """Create the property type from mmd metadata json."""
        return cls(metadata["name"], metadata["dataType"])

    def create_instance(self, property_info: dict[str, str]) -> ScalarProperty:
        """Create an instance of the property and fill fields from a MMD dict."""
        value = property_info[self.type_name]
        return ScalarProperty(self.type_name, value, self.data_type)

    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""
        return self.type_name


@dataclasses.dataclass
class SingleEmbeddedPropertyType(ReferencingPropertyTypeBase):
    """Meta-data about a single embedded property."""

    def create_instance(self, property_info: dict[str, dict[str, str]]) -> SingleEmbeddedProperty:
        """Create an instance of the property and fill fields from a MMD dict."""
        entity_info = property_info[self.type_name]

        gid = entity_info["gid"] if entity_info else None  # None means no instance is assigned to this entity
        return SingleEmbeddedProperty(self.type_name, self.entity_type, gid)

    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""
        return self.type_name + " { gid }"


@dataclasses.dataclass
class ArrayEmbeddedPropertyType(ReferencingPropertyTypeBase):
    """Meta-data about an array embedded property."""

    def create_instance(self, property_info: Json) -> ArrayEmbeddedProperty:
        """Create an instance of the property and fill fields from a MMD dict."""
        entities_info = property_info[self.type_name]
        children = []
        for edge in entities_info["edges"]:
            property_dict = edge["node"]
            gid = property_dict["gid"]
            children.append(gid)

        return ArrayEmbeddedProperty(self.type_name, self.entity_type, children)

    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""
        return self.type_name + " { edges { node { gid } } }"


@dataclasses.dataclass
class SingleReferencePropertyType(ReferencingPropertyTypeBase):
    """Meta-data about a single reference property."""

    def create_instance(self, property_info: dict[str, dict[str, str]]) -> SingleReferenceProperty:
        """Create an instance of the property and fill fields from a MMD dict."""
        entity_info = property_info[self.type_name]

        gid = entity_info["gid"] if entity_info else None  # None means no instance is assigned to this entity
        return SingleReferenceProperty(self.type_name, self.entity_type, gid)

    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""
        return self.type_name + " { gid }"


@dataclasses.dataclass
class ArrayArbitraryReferencePropertyType(PropertyTypeBase):
    """Meta-data about an array arbitrary reference property."""

    @classmethod
    def from_metadata(cls, metadata: dict[str, str]) -> ArrayArbitraryReferencePropertyType:
        """Create the property type from mmd metadata json."""
        return cls(metadata["name"])

    def create_instance(self, property_info: Json) -> ArrayArbitraryReferenceProperty:
        """Create an instance of the property and fill fields from a MMD dict."""
        entities_info = property_info[self.type_name]
        children = []
        for edge in entities_info["edges"]:
            property_dict = edge["node"]
            gid = property_dict["gid"]
            children.append(gid)
        return ArrayArbitraryReferenceProperty(self.type_name, children)

    def gql_query(self) -> str:
        """Return a GraphQL query necessary for retrieving information about this property."""
        return self.type_name + " { edges { node { gid type } } }"


PROPERTY_TYPE_FROM_GQL: dict[str, type[PropertyTypeBase]] = {
    "ScalarPropertyMetadata": ScalarPropertyType,
    "SingleEmbeddedPropertyMetadata": SingleEmbeddedPropertyType,
    "ArrayEmbeddedPropertyMetadata": ArrayEmbeddedPropertyType,
    "SingleReferencePropertyMetadata": SingleReferencePropertyType,
    "ArrayArbitraryReferencePropertyMetadata": None,  # not currently supported, but should be easy to add
}

PROPERTY_TYPE_NAME_TO_PROPERTY_TYPE: dict[str, type[PropertyTypeBase]] = {
    # "scalar": ScalarPropertyType,  # Not usable for traversing the composition graph
    "SE": SingleEmbeddedPropertyType,
    "AE": ArrayEmbeddedPropertyType,
    "SR": SingleReferencePropertyType,
    # "AAR": ArrayArbitraryReferencePropertyType,  # Not usable for traversing the composition graph
}


@dataclasses.dataclass
class PropertyBase(abc.ABC):
    """Base class for property instances."""

    type_name: str


@dataclasses.dataclass
class ScalarProperty(PropertyBase):
    """An instance of a scalar property."""

    value: Optional[str]
    data_type: str


@dataclasses.dataclass
class SingleEmbeddedProperty(PropertyBase):
    """An instance of a single embedded property."""

    entity_type: Optional[EntityType]  # Type of the embedded entity (actual instance can be a subtype of this type)
    entity: Optional[EntityId]  # GID of the embedded entity


@dataclasses.dataclass
class ArrayEmbeddedProperty(PropertyBase):
    """An instance of an array embedded property."""

    entities_type: Optional[EntityType]  # Type of the embedded entities (actual instances can be subtypes of this type)
    entities: Optional[list[EntityId]]  # GID of the embedded entities


@dataclasses.dataclass
class SingleReferenceProperty(PropertyBase):
    """An instance of a single reference property."""

    entity_type: Optional[EntityType]  # Type of the referenced entity (actual instance can be a subtype of this type)
    entity: Optional[EntityId]  # GID of the referenced entity


@dataclasses.dataclass
class ArrayArbitraryReferenceProperty(PropertyBase):
    """An instance of an array arbitrary reference property."""

    entities: Optional[list[EntityId]]  # GID of the referenced entities


@dataclasses.dataclass
class EntityTypeData:
    """Meta-meta-data about one entity type."""

    type_name: EntityType  # Name of this entity type
    properties: list[PropertyTypeBase]
    stored_as_simple: bool = False  # Whether it is stored in MMM DB as a table (False), or as a json column (True)
    children_properties: list[PropertyTypeBase] = None
    parent_properties: list[PropertyTypeBase] = None

    def gql_query(self) -> str:
        """Compose a GraphQL query on properties of this entity type, its children and parent types."""
        properties = ", ".join(property_.gql_query() for property_ in self.iter_properties(include_children=True))
        type_string = self.type_name + "s"
        return SINGLE_ENTITY_QUERY_TEMPLATE.substitute(entity_name=type_string, properties=properties)

    def iter_properties(self, include_children: bool = False) -> Iterator[PropertyTypeBase]:
        """Iterate over all parent, own and optionally also all children properties."""
        yield from self.parent_properties
        yield from self.properties
        if include_children:
            yield from self.children_properties


@dataclasses.dataclass
class Entity:
    """Meta-data about one particular instance of an entity."""

    type: EntityType  # Most concrete type of the entity
    gid: EntityId
    properties: list[PropertyBase] = dataclasses.field(default_factory=list)

    def __repr__(self):
        formatted_properties = pprint.pformat(self.properties)
        return f"Entity(type={self.type}, gid={self.gid}, properties=\n{formatted_properties}\n)"


class MmmDeserializationError(Exception):
    """Error when deserializing json data from MMM."""


def expand_entity_types(
    selected_entity_types: Optional[Iterable[EntityType]],
    traversed_properties: Iterable[str],
    composition: Composition,
    inheritance: Inheritance,
) -> set[EntityType]:
    """Expand selected entity types to all reachable by selected properties."""
    traversed_property_types = [PROPERTY_TYPE_NAME_TO_PROPERTY_TYPE[prop] for prop in traversed_properties]
    expanded_entity_types = composition.get_reachable_entities(selected_entity_types, traversed_property_types)
    # Children can be fetched together with their parents, so no need to fetch them also separately
    deduplicated_entity_types = inheritance.deduplicate_entities(expanded_entity_types)
    return deduplicated_entity_types


def generate_instance_queries(
    entity_types_data: Iterable[EntityTypeData],
    inheritance: Inheritance,
) -> Iterator[tuple[EntityType, EntityType, str]]:
    """Generate queries for fetching entity instances of selected types, return also the type and its base type."""
    for entity_type_data in entity_types_data:
        if entity_type_data.stored_as_simple:  # Those cannot be fetched
            continue

        base_type_name = inheritance.most_abstract_parent(entity_type_data.type_name)
        query = entity_type_data.gql_query()
        yield entity_type_data.type_name, base_type_name, query


def simplify_single_entity_type_response(response: Json, entity_types_data: EntityTypesData) -> Json:
    """Simplify list of fetched entities by removing properties unrelated to each entity type."""
    data = more_itertools.first(response.values())
    entities = data["edges"]
    for instance in entities:
        filter_properties(instance, entity_types_data)
    return entities


def filter_properties(instance: Json, entity_types_data: EntityTypesData) -> None:
    """Filter out properties (in-place) which are not related to the concrete type of entity."""
    node = instance["node"]
    concrete_type = node["type"]
    entity_type_data = entity_types_data[concrete_type]
    selected_properties = itertools.chain(entity_type_data.properties, entity_type_data.parent_properties)
    old_properties = node["publishedVersion"]
    filtered_properties = {p.type_name: old_properties[p.type_name] for p in selected_properties}
    node["publishedVersion"] = filtered_properties


@dataclasses.dataclass
class Inheritance:
    """Holds type inheritance of entity types and provides related utility methods."""

    # Parent types of each entity type from the most concrete to the most abstract one
    parents: dict[EntityType, list[EntityType]] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_mmd(cls, mmd_json: Json) -> Inheritance:
        """Create an inheritance object from meta-meta-data json."""
        entity_types_json = mmd_json["_modelMetadata"]["entities"]
        parents = {entity_type["entityName"]: entity_type["superEntities"] for entity_type in entity_types_json}
        return Inheritance(parents)

    def children_types(self, stem_type: EntityType, include_stem_type: bool = False) -> set[EntityType]:
        """Return all children types of given entity type (all which have this entity as a parent)."""
        children = {entity for entity, parents in self.parents.items() if stem_type in parents}
        if include_stem_type:
            children.add(stem_type)
        return children

    def most_abstract_parent(self, entity_type: EntityType) -> EntityType:
        """Return the most abstract parent of the entity type."""
        parents = self.parents[entity_type]
        if not parents:
            return entity_type
        else:
            return parents[-1]

    def deduplicate_entities(self, entity_types: Iterable[EntityType]) -> set[EntityType]:
        """Remove entity types which have a parent in the list."""
        deduplicated: set[EntityType] = set()
        for entity_type in entity_types:
            # More abstract type or itself is not present
            if entity_type not in deduplicated and deduplicated.isdisjoint(self.parents[entity_type]):
                deduplicated.add(entity_type)
                # Now remove all more concrete types already present
                deduplicated.difference_update(self.children_types(entity_type))

        return deduplicated


@dataclasses.dataclass
class Composition:
    """Provides information about compositional relationships of entities."""

    children: dict[EntityType, dict[str, list[EntityType]]]  # Children types of each entity based on the relation type

    @staticmethod
    def property_type_key(property_type: PropertyTypeBase) -> str:
        """Return a hashable key for property type."""
        return type(property_type).__name__

    @classmethod
    def from_entity_types(cls, entity_types_data: EntityTypesData) -> Composition:
        """Create a composition object based on MMD meta-meta-data."""
        children_tree = {}
        for entity_type, type_data in entity_types_data.items():
            children = collections.defaultdict(list)
            for property_type in type_data.iter_properties():
                if not isinstance(property_type, ReferencingPropertyTypeBase):
                    continue

                children[cls.property_type_key(property_type)].append(property_type.entity_type)

            children_tree[entity_type] = children

        return cls(children_tree)

    def get_reachable_entities(
        self, entity_types: Iterable[EntityType], property_types: Collection[type[PropertyTypeBase]]
    ) -> set[EntityType]:
        """Return all entity types reachable from any of the given types traversing over selected property types."""
        reachable_entity_types: set[EntityType] = set()
        relation_types = [property_type.__name__ for property_type in property_types]
        for entity_type in entity_types:
            self.add_descendants_recursively(entity_type, relation_types, reachable_entity_types)
        return reachable_entity_types

    def add_descendants_recursively(
        self, entity_type: EntityType, relation_types: Collection[str], nodes: set[EntityType]
    ):
        """Add reachable nodes to the set of nodes recursively."""
        if entity_type in nodes:
            return  # End of recursion

        nodes.add(entity_type)
        for property_type in relation_types:
            for child in self.children[entity_type][property_type]:
                self.add_descendants_recursively(child, relation_types, nodes)


class Metadata:
    """Holds all metadata about selected entities and their types (meta-meta data)."""

    # Instances of entities of different base types.
    # Beware that entities of some concrete type are stored under their base type
    entities: dict[EntityType, Entities]
    inheritance: Inheritance  # Information about entity types inheritance
    composition: Composition  # Information about entity types composition
    # Information about entity types, including properties of their parents and children
    entity_types_data: EntityTypesData
    skipped_property_types: collections.Counter  # Property types which are not supported and were ignored

    def __init__(self, metadata_json: Json):
        """Create the metadata object using MMD meta-meta-data and optionally also entity instances."""
        mmd = metadata_json["mmd"]
        all_entity_types, self.skipped_property_types = self.deserialize_mmd(mmd)
        self.inheritance = Inheritance.from_mmd(mmd)
        self.entity_types_data = self.augment_entity_types(all_entity_types, self.inheritance)
        self.composition = Composition.from_entity_types(self.entity_types_data)

        instances_json = metadata_json.get("instances", {})
        self.entities = {
            type_name: self.deserialize_single_base_type(instance_json, self.entity_types_data)
            for type_name, instance_json in instances_json.items()
        }

    @classmethod
    def deserialize_mmd(cls, mmd_json: Json) -> tuple[EntityTypesData, collections.Counter[str]]:
        """Deserialize meta-meta-data about entity types and their properties from MMM."""
        unsupported_property_types: collections.Counter[str] = collections.Counter()
        entity_types_data = {}
        for entity_type in mmd_json["_modelMetadata"]["entities"]:
            entity_type_name = entity_type["entityName"]
            property_types, skipped_property_types = cls.deserialize_property_types(entity_type["properties"])
            unsupported_property_types.update(skipped_property_types)
            stored_as_simple = cls.find_store_as_simple_trait(entity_type)
            entity_types_data[entity_type_name] = EntityTypeData(entity_type_name, property_types, stored_as_simple)

        return entity_types_data, unsupported_property_types

    @classmethod
    def deserialize_property_types(
        cls, properties_json: list[Json]
    ) -> tuple[list[PropertyTypeBase], collections.Counter[str]]:
        """Deserialize property types from mmd json and return them together with a list of types which were skipped."""
        property_types = []
        skipped_property_types: collections.Counter[str] = collections.Counter()
        for property_info in properties_json:
            property_type_instance = cls.deserialize_property_type(property_info)
            if property_type_instance is None:  # Property type not supported
                name = property_info["__typename"]
                skipped_property_types[name] += 1
            else:
                property_types.append(property_type_instance)

        return property_types, skipped_property_types

    @staticmethod
    def deserialize_property_type(property_info: Json) -> Optional[PropertyTypeBase]:
        """Deserialize information about a property type from mmd json. Return None if it is not supported."""
        property_type_name = property_info["__typename"]
        property_type_class: type[PropertyTypeBase] = PROPERTY_TYPE_FROM_GQL.get(property_type_name)
        return property_type_class.from_metadata(property_info) if property_type_class else None

    @staticmethod
    def find_store_as_simple_trait(entity_type_json: Json) -> bool:
        """Determine the value of `store_as_simple` trait."""
        for trait in entity_type_json["traits"]:
            if trait["traitName"] == CORE_PERSISTENCE_TRAIT_NAME:
                return trait["storedAsSimple"]

        entity_type_name = entity_type_json["name"]
        raise MmmDeserializationError(f"Trait `{CORE_PERSISTENCE_TRAIT_NAME}` is not present in {entity_type_name}")

    @classmethod
    def augment_entity_types(
        cls,
        entity_types_data: EntityTypesData,
        inheritance: Inheritance,
        selected_entity_types: Optional[Iterable[EntityType]] = None,
    ) -> EntityTypesData:
        """For each entity type add all properties from its children and parent types."""
        if not selected_entity_types:
            selected_entity_types = entity_types_data.keys()

        return {
            entity_type_name: cls.augment_properties(entity_type_name, entity_types_data, inheritance)
            for entity_type_name in selected_entity_types
        }

    @classmethod
    def augment_properties(
        cls, entity_type_name: EntityType, entity_types_data: EntityTypesData, inheritance: Inheritance
    ) -> EntityTypeData:
        """Return an augmented entity type by adding child and parent properties."""
        old_entity_type_data = entity_types_data[entity_type_name]

        children_properties = cls.merge_properties(entity_types_data, inheritance.children_types(entity_type_name))
        parent_properties = cls.merge_properties(entity_types_data, inheritance.parents[entity_type_name])
        own_properties = old_entity_type_data.properties
        return EntityTypeData(
            entity_type_name,
            own_properties,
            old_entity_type_data.stored_as_simple,
            children_properties,
            parent_properties,
        )

    @staticmethod
    def merge_properties(
        entity_types_data: EntityTypesData, entity_types: Iterable[EntityType]
    ) -> list[PropertyTypeBase]:
        """Merge property types of multiple entity types into a list."""
        return list(
            itertools.chain.from_iterable(
                entity_types_data[entity_type_name].properties for entity_type_name in entity_types
            )
        )

    @staticmethod
    def deserialize_single_base_type(entities_json: list[Json], entity_types_data: EntityTypesData) -> Entities:
        """Deserialize instances of one entity (base) type. They can have different concrete types."""
        entities = {}
        for entities_data in entities_json:
            node = entities_data["node"]
            instance = node["publishedVersion"]
            entity_type_data = entity_types_data[node["type"]]  # Get type data based on concrete type name
            properties = [
                property_type.create_instance(instance)
                for property_type in itertools.chain(entity_type_data.parent_properties, entity_type_data.properties)
            ]
            gid = node["gid"]
            entities[gid] = Entity(type=entity_type_data.type_name, gid=gid, properties=properties)

        return entities

    def __repr__(self):
        counts = {entity_type: len(instances) for entity_type, instances in self.entities.items()}
        n_entity_types = len(self.entities)
        n_entities = sum(counts.values())
        counts_str = pprint.pformat(counts)
        return (
            f"Metadata({n_entity_types} entity types, {n_entities} entities: \n{counts_str},"
            f"\nskipped property types = {self.skipped_property_types},"
            f"\nskipped entity types = {self.skipped_entity_types})"
        )

    def resolve(self, entity_type: EntityType) -> EntityType:
        """Return the most abstract parent of the entity type."""
        return self.inheritance.most_abstract_parent(entity_type)

    def iter_entities(self, stem_type: EntityType) -> Iterator[Entity]:
        """Return all entities of a type or its children types."""
        base_type = self.resolve(stem_type)
        children_types = self.inheritance.children_types(stem_type, include_stem_type=True)
        for entity in self.entities[base_type].values():
            if entity.type in children_types:
                yield entity

    def get_entity(self, entity_id: EntityId, entity_type: EntityType) -> Entity:
        """Return the entity defined by the id and type."""
        base_type = self.resolve(entity_type)
        return self.entities[base_type][entity_id]

    @property
    def skipped_entity_types(self) -> list[EntityType]:
        """Entity types which are not supported and were not fetched."""
        return [
            entity_type_data.type_name
            for entity_type_data in self.entity_types_data.values()
            if entity_type_data.stored_as_simple
        ]
