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

"""The default backend.

The default backend acts as a proxy. It detects the user's platform, loads
an appropriate backend, and delegates all functionality to it.

.. rubric:: Contents

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.backends.default.DEFAULT_BACKEND
    ~efiboot.backends.default.DefaultController
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Tuple

from efiboot import EfiState
from efiboot.backends import all_backends, BackendMetadata
from efiboot.backends.efibootmgr import EfibootmgrController
from efiboot.config import BootEntry, Config
from efiboot.controller import EfiController

logger = logging.getLogger(__name__)


#: The default backend.
DEFAULT_BACKEND = BackendMetadata(
    name="default",
    priority=1000,
    controller="efiboot.backends.default:DefaultController",
)


def _select_backend() -> BackendMetadata:
    """Select a backend.

    Returns:
        BackendMetadata:
            The name of the backend and the corresponding backend metadata.
    """
    # Note that backends are already sorted by priority.
    for backend in all_backends().values():
        if backend.is_compatible_with_host():
            return backend
        if 999 < backend.priority:
            break
    raise RuntimeError("efiboot could not load a compatible backend")


@dataclass
class DefaultController(EfiController):
    """The default controller for EFI variables.

    This is a simple proxy class. When constructed, it selects an
    appropriate backend for the current system.

    Parameters:
        controller (EfiController):
            The backend controller to proxy.
    """

    #: The backend controller to proxy.
    controller: EfiController

    @classmethod
    def from_config(cls, config: Config) -> EfiController:
        backend = _select_backend()
        logger.info(f"using backend: {backend.name}")
        controller = backend.make_controller(config)
        return cls(controller)

    @classmethod
    def is_compatible_with_host(cls) -> bool:
        return True

    def get_state(self) -> EfiState:
        return self.controller.get_state()

    def create(self, entry: BootEntry) -> EfiState:
        return self.controller.create(entry)

    def delete(self, bootnum: int) -> EfiState:
        return self.controller.delete(bootnum)

    def activate(self, bootnum: int) -> EfiState:
        return self.controller.activate(bootnum)

    def deactivate(self, bootnum: int) -> EfiState:
        return self.controller.deactivate(bootnum)

    def set_bootnext(self, bootnum: int) -> EfiState:
        return self.controller.set_bootnext(bootnum)

    def unset_bootnext(self) -> EfiState:
        return self.controller.unset_bootnext()

    def set_bootorder(self, bootorder: List[int]) -> EfiState:
        return self.controller.set_bootorder(bootorder)

    def unset_bootorder(self) -> EfiState:
        return self.controller.unset_bootorder()

    def set_timeout(self, seconds: int) -> EfiState:
        return self.controller.set_timeout(seconds)

    def unset_timeout(self) -> EfiState:
        return self.controller.unset_timeout()
