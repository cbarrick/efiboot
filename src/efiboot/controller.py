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

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Set

from efiboot.config import Config, BootEntry


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EfiState:
    """A view of the EFI variables.

    Parameters:
        bootcurrent (Optional[int]):
            The ID of the currently booted entry, if known.
        bootnext (Optional[int]):
            The ID of the boot entry to use for the next reboot, if known.
        bootorder (List[int]):
            The current boot order as a list of IDs. This may not contain all
            boot entries, and may be the empty list if not known.
        timeout (Optional[int]):
            The boot timeout, if known.
        labels (Dict[int, str]):
            A mapping from boot ID to label. Some boot entries may be lacking
            labels.
        active (Set[int]):
            The boot entries that are marked as active, if known.
    """

    bootcurrent: Optional[int]  #: The most recently booted entry.
    bootnext: Optional[int]  #: Boot entry to be used on the next reboot.
    bootorder: List[int]  #: The boot order.
    timeout: Optional[int]  #: The timeout set on the EFI boot process.
    labels: Dict[int, str]  #: The boot entry labels.
    active: Set[int]  #: The active boot entries.

    def entries(self) -> Iterator[int]:
        """Returns an iterator over boot entry IDs.

        Yields:
            int: The ID of the boot entry.
        """
        yield from self.labels

    def find(self, label: str) -> List[int]:
        """Find all boot entries with the given label.

        Arguments:
            label (str):
                The label to search.

        Returns:
            List[int]:
                The boot entries with the given label.
        """
        return [b for b, l in self.labels.items() if l == label]


class EfiController(ABC):
    """An abstract base class for EFI controllers.

    Controllers provide methods to read and modify EFI variables. Most
    importantly, a controller is capable of creating and deleting boot entries.

    Almost all controller methods return an `EfiState` which provides a view of
    the EFI variables after each operation.

    See Also:
        Concrete controller classes are provided by
        `backends </api/efiboot.backends>`_.
    """

    @classmethod
    def from_config(cls, config: Config) -> EfiController:
        """Create a controller from a config file.

        Returns:
            EfiController:
                The controller.
        """
        pass

    @classmethod
    @abstractmethod
    def is_compatible_with_host(cls) -> bool:
        """True if this controller class is compatible with the host system.

        Returns:
            bool:
                True if the controller is compatible.
        """
        pass

    @abstractmethod
    def get_state(self) -> EfiState:
        """Read the EFI variables.

        Returns:
            EfiState:
                The current state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def create(self, entry: BootEntry) -> EfiState:
        """Create a new boot entry on the EFI.

        Arguments:
            entry (BootEntry):
                A description of the entry to create.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def delete(self, bootnum: int) -> EfiState:
        """Delete a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to delete.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def activate(self, bootnum: int) -> EfiState:
        """Activate a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to activate.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def deactivate(self, bootnum: int) -> EfiState:
        """Deactivate a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to deactivate.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def set_bootnext(self, bootnum: int) -> EfiState:
        """Set the bootnext field.

        Arguments:
            bootnum (int):
                The number of the boot entry to set as bootnext.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def unset_bootnext(self) -> EfiState:
        """Unset the bootnext field.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def set_bootorder(self, bootorder: List[int]) -> EfiState:
        """Set the boot order.

        Arguments:
            bootorder (List[int]):
                Boot entry number to set as bootorder.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def unset_bootorder(self) -> EfiState:
        """Unset the boot order.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def set_timeout(self, seconds: int) -> EfiState:
        """Set the boot timeout.

        Arguments:
            seconds (int):
                The timeout in seconds.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass

    @abstractmethod
    def unset_timeout(self) -> EfiState:
        """Unset the boot timeout.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        pass
