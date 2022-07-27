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
import sys
from pathlib import Path
from typing import List, Optional

from efiboot.backends import get_backend
from efiboot.config import BootEntry, Config
from efiboot.controller import EfiController
from efiboot import EfiState


logger = logging.getLogger(__name__)


def _format_bootorder(bootorder: List[int]) -> str:
    """Format a bootorder into a string."""
    boot_strings = [f"Boot{n:0>4X}" for n in bootorder]
    msg = " ".join(boot_strings)
    return f"[{msg}]"


class EfiBoot:
    """The primary high-level API for efiboot.

    When the parameters are not given, the config is read from
    ``/boot/efiboot.toml``, the controller is created from the config, and
    the initial state is read from the controller.

    Parameters:
        config (Optional[Config]): The efiboot config.
        controller (Optional[EfiController]): The EFI controller.
        state (Optional[EfiState]): The current state.

    Raises:
        FileNotFoundError:
            The config file or ESP could not be found.
        TypeError:
            There was a type error in the config.
        ValueError:
            There was a value error in the config.
    """

    config: Config  #: The efiboot config.
    controller: EfiController  #: The controller.
    state: EfiState  #: The current state.

    def __init__(
        self,
        config: Optional[Config] = None,
        controller: Optional[EfiController] = None,
        state: Optional[EfiState] = None,
    ) -> None:
        """Initialize the facade."""
        if config is None:
            path = Path("/boot/efiboot.toml")
            config = Config.from_path(path)
        config.validate()

        if controller is None:
            backend_name = config.backend or "default"
            logger.info(f"using backend: {backend_name}")
            backend = get_backend(backend_name)
            controller = backend.make_controller(config)

        if state is None:
            state = controller.get_state()

        self.config = config
        self.controller = controller
        self.state = state

    def find(self, label: str) -> List[int]:
        """Find all boot entries with the given label.

        Arguments:
            label (str):
                The label to search.

        Returns:
            List[int]:
                The boot entries with the given label.
        """
        return self.state.find(label)

    def create(self, entry: BootEntry):
        """Create a new boot entry on the EFI.

        Arguments:
            entry (BootEntry):
                A description of the entry to create.

        Returns:
            EfiState:
                The new state of the EFI boot entries.
        """
        logger.info(f"CREATE {repr(entry.label)} {entry.loader} {entry.params}")
        self.state = self.controller.create(entry)

    def delete(self, bootnum: int):
        """Delete a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to delete.
        """
        label = self.state.labels[bootnum]
        logger.info(f"DELETE Boot{bootnum:0>4X} ({label})")
        self.state = self.controller.delete(bootnum)

    def activate(self, bootnum: int):
        """Activate a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to activate.
        """
        label = self.state.labels[bootnum]
        logger.info(f"ACTIVATE Boot{bootnum:0>4X} ({label})")
        self.state = self.controller.activate(bootnum)

    def deactivate(self, bootnum: int):
        """Deactivate a boot entry.

        Arguments:
            bootnum (int):
                The number of the boot entry to deactivate.
        """
        label = self.state.labels[bootnum]
        logger.info(f"DEACTIVATE Boot{bootnum:0>4X} ({label})")
        self.state = self.controller.deactivate(bootnum)

    def set_bootnext(self, bootnum: int):
        """Set the bootnext field.

        Arguments:
            bootnum (int):
                The number of the boot entry to set as bootnext.
        """
        label = self.state.labels[bootnum]
        logger.info(f"SET BootNext = Boot{bootnum:0>4X} ({label})")
        self.state = self.controller.set_bootnext(bootnum)

    def unset_bootnext(self):
        """Unset the bootnext field."""
        logger.info(f"UNSET BootNext")
        self.state = self.controller.unset_bootnext()

    def set_bootorder(self, bootorder: List[int]):
        """Set the boot order.

        Arguments:
            bootorder (List[int]):
                Boot entry number to set as bootorder.
        """
        logger.info(f"SET BootOrder = {_format_bootorder(bootorder)}")
        self.state = self.controller.set_bootorder(bootorder)

    def unset_bootorder(self):
        """Unset the boot order."""
        logger.info(f"UNSET BootOrder")
        self.state = self.controller.unset_bootorder()

    def set_timeout(self, seconds: int):
        """Set the boot timeout.

        Arguments:
            seconds (int):
                The timeout in seconds.
        """
        logger.info(f"SET Timeout = {seconds}")
        self.state = self.controller.set_timeout(seconds)

    def unset_timeout(self):
        """Unset the boot timeout."""
        logger.info(f"UNSET Timeout")
        self.state = self.controller.unset_timeout()

    def push(self):
        """Push the config to the EFI."""
        logger.info(f"PUSH {self.config.name}")

        # Validate the config.
        labels = set()
        for entry in self.config.entries:
            if entry.label in labels:
                raise ValueError(f"multiple boot entries: {entry.label}")
            else:
                labels.add(entry.label)
        if len(labels) < 1:
            raise ValueError("config contains no boot entries")

        # Recreate all entries.
        for entry in self.config.entries:
            for bootnum in self.find(entry.label):
                self.delete(bootnum)
            self.create(entry)

        # Set the boot order.
        bootorder = []
        for entry in self.config.entries:
            bootnum = self.state.find(entry.label)[0]
            bootorder.append(bootnum)
        self.set_bootorder(bootorder)

        # Set the next boot.
        first = self.config.entries[0]
        bootnum = self.state.find(first.label)[0]
        self.set_bootnext(bootnum)

        # Set the timeout.
        if self.config.timeout is not None:
            self.set_bootorder(self.config.timeout)

    def print_timeout(self, file=sys.stdout, flush=False):
        """Print the timeout in an easy to parse format."""
        if self.state.timeout:
            print(f"Timeout\t{self.state.timeout} seconds", file=file)
        else:
            print(f"Timeout\tnot set", file=file)
        if flush:
            file.flush()

    def print_bootorder(self, file=sys.stdout, flush=False):
        """Print the boot order in an easy to parse format."""
        if self.state.bootorder:
            order_str_list = [f"{entry:04X}" for entry in self.state.bootorder]
            order_str = ",".join(order_str_list)
            print(f"Order\t{order_str}", file=file)
        else:
            print(f"Order\tnot set", file=file)
        if flush:
            file.flush()

    def print_bootcurrent(self, file=sys.stdout, flush=False):
        """Print the current boot entry in an easy to parse format."""
        entry = self.state.bootcurrent
        if entry is not None:
            label = self.state.labels.get(entry)
            print(f"Current\t{entry:04X}\t{label}", file=file)
        else:
            print(f"Current\tnot set", file=file)
        if flush:
            file.flush()

    def print_bootnext(self, file=sys.stdout, flush=False):
        """Print the next boot entry in an easy to parse format."""
        entry = self.state.bootnext
        if entry is not None:
            label = self.state.labels.get(entry)
            print(f"Next\t{entry:04X}\t{label}", file=file)
        else:
            print(f"Next\tnot set", file=file)
        if flush:
            file.flush()

    def print_entry(self, entry, file=sys.stdout, flush=False):
        """Print a boot entry in an easy to parse format."""
        label = self.state.labels[entry]
        properties = []
        if self.state.bootcurrent == entry:
            properties.append("current")
        if self.state.bootnext == entry:
            properties.append("next")
        if not entry in self.state.active:
            properties.append("inactive")
        if properties:
            properties_str = ",".join(properties)
            print(f"Boot\t{entry:04X}\t{label}\t[{properties_str}]", file=file)
        else:
            print(f"Boot\t{entry:04X}\t{label}", file=file)
        if flush:
            file.flush()

    def print_state(self, file=sys.stdout, flush=False):
        """Print the state in an easy to parse format."""
        logger.info(f"STATUS {repr(self.state)}")
        self.print_timeout(file=file)
        self.print_bootcurrent(file=file)
        self.print_bootnext(file=file)
        self.print_bootorder(file=file)
        for entry in self.state.entries():
            self.print_entry(entry, file=file)
        if flush:
            file.flush()
