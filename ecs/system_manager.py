"""Entity and System Managers."""

from ecs.exceptions import DuplicateSystemTypeError, SystemAlreadyAddedToManagerError
from typing import Any, Tuple


class SystemManager(object):
    """A container and manager for :class:`ecs.system.System` objects."""

    def __init__(self, entity_manager):
        """:param entity_manager: this manager's entity manager
        :type entity_manager: :class:`SystemManager`
        """
        self._systems = []
        self._system_types = {}
        self._entity_manager = entity_manager

    # Allow getting the list of systems but not directly setting it.
    @property
    def systems(self):
        """Get this manager's list of systems.

        :return: system list
        :rtype: :class:`list` of :class:`ecs.system.System`
        """
        return self._systems

    def add_system(self, system_instance, priority=0):
        """Add a :class:`ecs.system.System` instance to the manager.

        :param system_instance: instance of a system
        :param priority: non-negative integer (default: 0)
        :type system_instance: :class:`ecs.system.System`
        :type priority: :class:`int`
        :raises: :class:`ecs.exceptions.DuplicateSystemTypeError` when the
            system type is already present in this manager
        :raises: :class:`ecs.exceptions.SystemAlreadyAddedToManagerError` when
            the system already belongs to a system manager
        """
        system_type = type(system_instance)
        if system_type in self._system_types:
            raise DuplicateSystemTypeError(system_type)
        if system_instance.system_manager is not None:
            raise SystemAlreadyAddedToManagerError(
                system_instance, self, system_instance.system_manager
            )
        system_instance.entity_manager = self._entity_manager
        system_instance.system_manager = self
        self._system_types[system_type] = system_instance
        self._systems.append(system_instance)

        system_instance.priority = priority
        self._systems.sort(key=lambda x: x.priority)

    def add_systems(self, system_instances: list[Tuple[Any, int]]):
        """Add multiple :class:`ecs.system.System` instances to the manager.

        :param Tuple[system_instance, int]: tuple of system instance and
            priority (non-negative integer)
        :type Tuple[system_instance, int]: :class:`tuple` of
            (:class:`ecs.system.System`, :class:`int`)
        """
        for system_instance, priority in system_instances:
            self.add_system(system_instance, priority)

    def remove_system(self, system_type):
        """Tell the manager to no longer run the system of this type.

        :param system_type: type of system to remove
        :type system_type: :class:`type`
        """
        system = self._system_types[system_type]
        system.entity_manager = None
        system.system_manager = None
        self._systems.remove(system)
        del self._system_types[system_type]

    def update(self, dt):
        """Run each system's ``update()`` method for this frame. The systems
        are run in the order in which they were added.

        :param dt: delta time, or elapsed time for this frame
        :type dt: :class:`float`
        """
        # Iterating over a list of systems instead of values in a dictionary is
        # noticeably faster. We maintain a list in addition to a dictionary
        # specifically for this purpose.
        #
        # Though initially we had the entity manager being passed through to
        # each update() method, this turns out to cause quite a large
        # performance penalty. So now it is just set on each system.
        for system in self._systems:
            system.update(dt)
