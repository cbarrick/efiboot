# Copyright 2022 Chris Barrick <cbarrick1@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The efiboot backend system.

Backends provide concrete implementations of the `~efiboot.EfiController`
interface, along with other metadata to help efiboot identify when a particular
backend should be used.

The backend can be specified in ``efiboot.toml`` or at the command line. When
no backend is specified, the `default` backend us used. This backend is special:
when used, it searches through all other backends and delegates to the one that
is most appropriate for the host system.


Custom Backends
---------------------------------------------------------------------------

A backend is described by a `BackendMetadata` object.

Any Python package may provide a backend. To register a new backend with
efiboot, a package provides an `entry point <entry_point_>`_ in the
``efiboot_backends`` namespace pointing to a `BackendMetadata` object.

.. _entry_point: https://setuptools.pypa.io/en/latest/userguide/entry_point.html

.. rubric:: Example

A minimal backend contains only a global `BackendMetadata`:

.. code:: python

    # Module: examplepkg.example_backend

    from efiboot.backends import BackendMetadata

    EFIBOOT_BACKEND = BackendMetadata(name='example')

The backend must be registered in the ``efiboot_backends`` entry point:

.. code:: toml

    # File: pyproject.toml

    [project.entry-points.efiboot_backends]
    example = 'examplepkg.example_backend:EFIBOOT_BACKEND'

The backend can then be used in `efiboot.toml </config>`_.

.. code:: toml

    # File: /boot/efiboot.toml

    backend = 'example'

    [[BootEntry]]
    name = 'Linux'
    loader = '/vmlinuz'


Reference
---------------------------------------------------------------------------

.. rubric:: Builtin Backends

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.backends.default
    ~efiboot.backends.efibootmgr


.. rubric:: Backend Utilities

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.backends.BackendMetadata
    ~efiboot.backends.get_backend
    ~efiboot.backends.all_backends
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, Type

try:
    from importlib import metadata
except:
    import importlib_metadata as metadata

try:
    from functools import cache
except:
    from functools import lru_cache as cache

from efiboot.config import Config
from efiboot.controller import EfiController


logger = logging.getLogger(__name__)


# Backend Infrastructure
# ---------------------------------------------------------------------------


def _import(name: str) -> Any:
    # The name must have the form `<module>:<attr>`.
    # First import the module, then get the attribute.
    mod_name, attr_name = name.split(":", 1)
    mod = importlib.import_module(mod_name)
    attr = getattr(mod, attr_name)
    return attr


@dataclass(frozen=True)
class BackendMetadata:
    """The efiboot backend metadata class.

    Packages should register their `BackendMetadata` objects under the
    ``efiboot_backends`` entry point namespace. This allows the backend to be
    auto-discovered by efiboot.

    Parameters:
        name (str):
            The name of the backend. All backends must have a unique name. If
            this backend is registered under the ``efiboot_backends`` entry
            point, it must be registered with the same name.
        priority (int):
            The priority of this backend. This is used to pick a backend when
            multiple backends that are compatible with the host system. A
            **lower** value has higher priority. The default is 500.
        controller (str):
            A string of the form ``<module>:<class>`` pointing to an
            `~efiboot.EfiController` subclass.
    """

    #: The name of the backend.
    name: str

    #: The priority of this backend.
    priority: int = 500

    #: The controller class for this backend.
    controller: str = "efiboot.backends.default:DefaultController"

    def import_controller(self) -> Type[EfiController]:
        """Import the backend controller class.

        Returns:
            Type[EfiController]: The controller class.
        """
        return _import(self.controller)

    def make_controller(self, config: Config) -> EfiController:
        """Create an instance of the backend controller.

        Returns:
            EfiController: The controller.
        """
        klass = self.import_controller()
        return klass.from_config(config)

    def is_compatible_with_host(self) -> bool:
        """Returns true if this backend is compatible with the host system.

        Returns:
            bool: The compatibility.
        """
        klass = self.import_controller()
        return klass.is_compatible_with_host()


@cache
def all_backends() -> Dict[str, BackendMetadata]:
    """Get the set of all backends, indexed by name.

    Returns:
        Dict[str, BackendMetadata]:
            The backends.
    """
    entry_points = metadata.entry_points()["efiboot_backends"]
    backends = []

    # Import the backends.
    for ep in entry_points:
        backend = ep.load()
        name = backend.name
        backends.append(backend)
        if name != ep.name:
            logger.warning(f"entry point does not match backend name")
            logger.warning(f"entry point = {ep.name} / backend name = {name}")

    # Remove duplicates.
    # If two different backends present the same name, remove both.
    backends = sorted(backends, key=lambda b: b.name)
    i = 0
    while i + 1 < len(backends):
        a, b = backends[i], backends[i + 1]
        if a == b:
            backends.pop(i + 1)
        elif a.name == b.name:
            logger.warning(f"different backends with the same name: {a.name}")
            logger.warning(f"ignoring backends: A = {repr(a)}, B = {repr(b)}")
            backends.pop(i + 1)
            backends.pop(i)
        else:
            i += 1

    # Sort the backends by priority.
    backends = sorted(backends, key=lambda b: b.priority)

    # Index the backends by name.
    return {b.name: b for b in backends}


def get_backend(name: str) -> BackendMetadata:
    """Get a backend by name.

    Arguments:
        name (str):
            The name of the backend. This can be either the name registered in
            the entry point or the dotted import path of the backend module.

    Returns:
        BackendMetadata: The backend.

    Raises:
        KeyError: No such backend.
    """
    return all_backends()[name]


def always_compatible() -> bool:
    """The default compatibility function.

    Always returns True.
    """
    return True
