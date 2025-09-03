"""Entity, Component, and System classes."""

from abc import ABCMeta, abstractmethod

import six

from ecs.entity_manager import EntityManager

from ecs.system_manager import SystemManager


class Component(object):
    """Class from which all components should derive."""

    pass


@six.add_metaclass(ABCMeta)
class System(object):
    """An object that represents an operation on a set of objects from the game
    database. The :meth:`update` method must be implemented.
    """

    def __init__(self):
        self.entity_manager: EntityManager | None = None
        """This system's entity manager. It is set for each system when it is
        added to a system manager, so a system may not (reasonably) use
        multiple entity managers. The reason is performance. See
        :meth:`ecs.managers.SystemManager.update()` for more information.
        """
        self.system_manager: SystemManager | None = None
        """The system manager to which this system belongs. Again, a system is
        only allowed to belong to one at a time."""
        self.priority: int | None = None
        """The priority for this system when the system manager runs
        :meth:`ecs.managers.SystemManager.update()`. Must be a non-negative
        integer with 0 being the highest priority."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Run the system for this frame. This method is called by the system
        manager, and is where the functionality of the system is implemented.

        :param entity_manager: this system's entity manager, used for
            querying components
        :type entity_manager: :class:`ecs.managers.EntityManager`
        :param dt: delta time, or elapsed time for this frame
        :type dt: :class:`float`
        """
        six.print_("System's update() method was called: dt={}".format(dt))
