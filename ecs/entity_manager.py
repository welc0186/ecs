from __future__ import annotations

from typing import Dict, Iterator, Tuple, Type, TypeVar, Optional, Any, cast
from collections.abc import ItemsView
from ecs.exceptions import NonexistentComponentTypeForEntity
from ecs.entity import Entity
from ecs.component import Component


# Type variables for better type safety
C = TypeVar("C", bound=Component)
ComponentType = Type[Component]


class EntityManager:
    """Provide database-like access to components based on an entity key.

    This class manages the storage and retrieval of components associated with entities
    in an Entity Component System (ECS) architecture.
    """

    def __init__(self) -> None:
        """Initialize the EntityManager with an empty database and reset the GUID counter."""
        self._database: Dict[ComponentType, Dict[Entity, Component]] = {}
        self._next_guid: int = 0

    @property
    def database(self) -> Dict[ComponentType, Dict[Entity, Component]]:
        """Get this manager's database. Direct modification is not permitted.

        Returns:
            The database containing all components organized by type and entity.
        """
        return self._database

    def create_entity(self) -> Entity:
        """Create a new entity instance with the current lowest GUID value.

        Does not store a reference to it, and does not make any entries in the
        database referencing it.

        Returns:
            A new entity with a unique ID.
        """
        entity = Entity(self._next_guid)
        self._next_guid += 1
        return entity

    def add_component(self, entity: Entity, component_instance: Component) -> None:
        """Add a component to the database and associate it with the given entity.

        Args:
            entity: The entity to associate with the component.
            component_instance: The component instance to add to the entity.
        """
        component_type = type(component_instance)
        if component_type not in self._database:
            self._database[component_type] = {}

        self._database[component_type][entity] = component_instance

    def add_components(
        self, entity: Entity, component_instances: list[Component]
    ) -> None:
        """Add multiple components to the database and associate them with the given entity.
        Args:
            entity: The entity to associate with the components.
            component_instances: A list of component instances to add to the entity.
        """
        for component_instance in component_instances:
            self.add_component(entity, component_instance)

    def remove_component(self, entity: Entity, component_type: Type[C]) -> None:
        """Remove the component of the specified type associated with the entity.

        Doesn't perform any kind of data teardown. It is up to the system calling
        this code to do that. In the future, a callback system may be used to
        implement type-specific destructors.

        Args:
            entity: The entity to remove the component from.
            component_type: The type of component to remove from the entity.
        """
        try:
            del self._database[component_type][entity]
            if not self._database[component_type]:  # More pythonic than == {}
                del self._database[component_type]
        except KeyError:
            pass

    def pairs_for_type(self, component_type: Type[C]) -> Iterator[Tuple[Entity, C]]:
        """Return an iterator over (entity, component_instance) tuples.

        Returns all entities in the database possessing a component of the specified type.
        Returns an empty iterator if there are no components of this type in the database.

        Example usage:
            for entity, renderable_component in entity_manager.pairs_for_type(Renderable):
                # do something with entity and renderable_component
                pass

        Args:
            component_type: The type of component to search for.

        Returns:
            An iterator yielding (entity, component_instance) tuples.
        """
        try:
            component_dict = self._database[component_type]
            # Cast is safe because we know the components in this dict are of type C
            return cast(Iterator[Tuple[Entity, C]], iter(component_dict.items()))
        except KeyError:
            return iter([])  # Return empty iterator instead of using six.iteritems

    def component_for_entity(self, entity: Entity, component_type: Type[C]) -> C:
        """Return the instance of the specified component type for the entity.

        Args:
            entity: The entity to get the component from.
            component_type: The type of component to retrieve.

        Returns:
            The component instance of the specified type.

        Raises:
            NonexistentComponentTypeForEntity: When the component type does not
                exist on the given entity.
        """
        try:
            component = self._database[component_type][entity]
            # Cast is safe because we know this component is of type C
            return cast(C, component)
        except KeyError:
            raise NonexistentComponentTypeForEntity(entity, component_type)

    def has_component(self, entity: Entity, component_type: Type[Component]) -> bool:
        """Check if an entity has a component of the specified type.

        Args:
            entity: The entity to check.
            component_type: The type of component to check for.

        Returns:
            True if the entity has the component, False otherwise.
        """
        try:
            return entity in self._database[component_type]
        except KeyError:
            return False

    def get_component_safe(
        self, entity: Entity, component_type: Type[C]
    ) -> Optional[C]:
        """Safely get a component for an entity, returning None if not found.

        Args:
            entity: The entity to get the component from.
            component_type: The type of component to retrieve.

        Returns:
            The component instance if found, None otherwise.
        """
        try:
            return self.component_for_entity(entity, component_type)
        except NonexistentComponentTypeForEntity:
            return None

    def entities_for_component(
        self, component_type: Type[Component]
    ) -> Iterator[Entity]:
        """Return an iterator over all entities that have the specified component type.

        Args:
            component_type: The type of component to search for.

        Returns:
            An iterator yielding entities that have the specified component.
        """
        try:
            return iter(self._database[component_type].keys())
        except KeyError:
            return iter([])

    def components_for_entity(self, entity: Entity) -> Iterator[Component]:
        """Return an iterator over all components associated with the entity.

        Args:
            entity: The entity to get components for.

        Returns:
            An iterator yielding all components associated with the entity.
        """
        for component_type, component_dict in self._database.items():
            if entity in component_dict:
                yield component_dict[entity]

    def get_component_types_for_entity(
        self, entity: Entity
    ) -> Iterator[Type[Component]]:
        """Return an iterator over all component types associated with the entity.

        Args:
            entity: The entity to get component types for.

        Returns:
            An iterator yielding component types associated with the entity.
        """
        for component_type, component_dict in self._database.items():
            if entity in component_dict:
                yield component_type

    def remove_entity(self, entity: Entity) -> None:
        """Remove all components from the database that are associated with the entity.

        This has the side-effect that the entity is also no longer in the database.

        Args:
            entity: The entity to remove completely from the database.
        """
        # Create a copy of keys to avoid runtime mutation errors
        component_types = list(self._database.keys())

        for comp_type in component_types:
            try:
                del self._database[comp_type][entity]
                # Clean up empty component type dictionaries
                if not self._database[comp_type]:
                    del self._database[comp_type]
            except KeyError:
                pass

    def clear(self) -> None:
        """Clear all entities and components from the database."""
        self._database.clear()
        self._next_guid = 0

    def entity_count(self) -> int:
        """Get the total number of unique entities in the database.

        Returns:
            The number of unique entities that have at least one component.
        """
        entities = set()
        for component_dict in self._database.values():
            entities.update(component_dict.keys())
        return len(entities)

    def component_count(self) -> int:
        """Get the total number of components in the database.

        Returns:
            The total count of all component instances.
        """
        return sum(len(component_dict) for component_dict in self._database.values())

    def component_types(self) -> Iterator[Type[Component]]:
        """Get an iterator over all component types in the database.

        Returns:
            An iterator yielding all component types that have at least one instance.
        """
        return iter(self._database.keys())

    def __len__(self) -> int:
        """Return the number of unique entities in the database."""
        return self.entity_count()

    def __contains__(self, entity: Entity) -> bool:
        """Check if an entity exists in the database (has at least one component).

        Args:
            entity: The entity to check for.

        Returns:
            True if the entity has at least one component, False otherwise.
        """
        for component_dict in self._database.values():
            if entity in component_dict:
                return True
        return False

    def __repr__(self) -> str:
        """Return a string representation of the EntityManager."""
        return (
            f"EntityManager(entities={self.entity_count()}, "
            f"components={self.component_count()}, "
            f"next_guid={self._next_guid})"
        )
