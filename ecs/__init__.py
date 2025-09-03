"""An entity/component system library for games."""

from ecs import metadata as _metadata

# Provide a common namespace for these classes.
from ecs.system import System  # NOQA
from ecs.system_manager import SystemManager

from ecs.entity import Entity
from ecs.entity_manager import EntityManager

from ecs.component import Component  # NOQA


__version__ = _metadata.version
__author__ = _metadata.authors[0]
__license__ = _metadata.license
__copyright__ = _metadata.copyright
