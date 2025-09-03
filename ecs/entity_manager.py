from ecs.exceptions import NonexistentComponentTypeForEntity
from ecs.entity import Entity


import six


class EntityManager(object):
    """Provide database-like access to components based on an entity key."""

    def __init__(self):
        self._database = {}
        self._next_guid = 0

    @property
    def database(self):
        """Get this manager's database. Direct modification is not
        permitted.

        :return: the database
        :rtype: :class:`dict`
        """
        return self._database

    def create_entity(self):
        """Return a new entity instance with the current lowest GUID value.
        Does not store a reference to it, and does not make any entries in the
        database referencing it.

        :return: the new entity
        :rtype: :class:`ecs.models.Entity`
        """
        entity = Entity(self._next_guid)
        self._next_guid += 1
        return entity

    def add_component(self, entity, component_instance):
        """Add a component to the database and associate it with the given
        entity.

        :param entity: entity to associate
        :type entity: :class:`ecs.models.Entity`
        :param component_instance: component to add to the entity
        :type component_instance: :class:`ecs.models.Component`
        """
        component_type = type(component_instance)
        if component_type not in self._database:
            self._database[component_type] = {}

        self._database[component_type][entity] = component_instance

    def remove_component(self, entity, component_type):
        """Remove the component of ``component_type`` associated with
        entity from the database. Doesn't do any kind of data-teardown. It is
        up to the system calling this code to do that. In the future, a
        callback system may be used to implement type-specific destructors.

        :param entity: entity to associate
        :type entity: :class:`ecs.models.Entity`
        :param component_type: component type to remove from the entity
        :type component_type: :class:`type` which is :class:`Component`
            subclass
        """
        try:
            del self._database[component_type][entity]
            if self._database[component_type] == {}:
                del self._database[component_type]
        except KeyError:
            pass

    def pairs_for_type(self, component_type):
        """Return an iterator over ``(entity, component_instance)`` tuples for
        all entities in the database possessing a component of
        ``component_type``. Return an empty iterator if there are no components
        of this type in the database. It should be used in a loop like this,
        where ``Renderable`` is a component type:

        .. code-block:: python

            for entity, renderable_component in \
entity_manager.pairs_for_type(Renderable):
                pass # do something

        :param component_type: a type of created component
        :type component_type: :class:`type` which is :class:`Component`
            subclass
        :return: iterator on ``(entity, component_instance)`` tuples
        :rtype: :class:`iter` on
            (:class:`ecs.models.Entity`, :class:`ecs.models.Component`)
        """
        try:
            return six.iteritems(self._database[component_type])
        except KeyError:
            return six.iteritems({})

    def component_for_entity(self, entity, component_type):
        """Return the instance of ``component_type`` for the entity from the
        database.

        :param entity: associated entity
        :type entity: :class:`ecs.models.Entity`
        :param component_type: a type of created component
        :type component_type: :class:`type` which is :class:`Component`
            subclass
        :return: component instance
        :rtype: :class:`ecs.models.Component`
        :raises: :exc:`NonexistentComponentTypeForEntity` when
            ``component_type`` does not exist on the given entity
        """
        try:
            return self._database[component_type][entity]
        except KeyError:
            raise NonexistentComponentTypeForEntity(entity, component_type)

    def remove_entity(self, entity):
        """Remove all components from the database that are associated with
        the entity, with the side-effect that the entity is also no longer
        in the database.

        :param entity: entity to remove
        :type entity: :class:`ecs.models.Entity`
        """
        # For Python 2, don't use iterkeys(), otherwise we will get a
        # RuntimeError about mutating the length of the dictionary at runtime.
        # For Python 3, we can't even use keys(), because that is a view object
        # that acts like iterkeys(). We therefore make a copy using list() to
        # avoid modifying the iterator.
        for comp_type in list(self._database.keys()):
            try:
                del self._database[comp_type][entity]
                if self._database[comp_type] == {}:
                    del self._database[comp_type]
            except KeyError:
                pass
