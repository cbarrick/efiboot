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

"""The efibootmgr backend.

This backend delegates to the `efibootmgr`_ CLI.

.. _efibootmgr: https://github.com/rhboot/efibootmgr

.. rubric:: Contents

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.backends.efibootmgr.EFIBOOTMGR_BACKEND
    ~efiboot.backends.efibootmgr.EfibootmgrController
"""

from __future__ import annotations

import logging
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from efiboot.config import BootEntry

from efiboot import EfiState
from efiboot.backends import BackendMetadata
from efiboot.config import Config
from efiboot.controller import EfiController

logger = logging.getLogger(__name__)


#: The efibootmgr backend.
EFIBOOTMGR_BACKEND = BackendMetadata(
    name="efibootmgr",
    priority=900,
    controller="efiboot.backends.efibootmgr:EfibootmgrController",
)


def _find_mounts() -> Dict[Path, Path]:
    """Get the mountpoints of the system.

    This function parses the output of the `mount` CLI, and returns a dictionary
    mapping mount points to the device that is mounted.

    Returns:
        Dict[Path, Path]:
            A mapping from mount points to devices.
    """
    # The "type" part only appears on Linux, not the BSDs.
    mounts = {}
    mount_pattern = re.compile(r"^(.+) on (.+)( type .+)? \(.+\)$")
    proc = subprocess.run("mount", capture_output=True, encoding="utf-8")
    for line in proc.stdout.splitlines():
        match = mount_pattern.match(line)
        if match is None:
            continue
        dest = match.group(2)
        disk = match.group(1)
        if not disk.startswith("/"):
            continue
        dest_path = Path(dest).resolve()
        disk_path = Path(disk).resolve()
        mounts[dest_path] = disk_path
    return mounts


def _find_esp() -> Path:
    """Find the assumed path to the EFI system partition.

    This function checks to see if any devices are mounted at paths known to
    contain ESPs in various operating systems. Otherwise it defaults to
    ``/dev/sda1``.

    Returns:
        Path:
            The device path of the EFI system partition.
    """
    mounts = _find_mounts()

    path_efi = Path("/efi").resolve()
    path_boot = Path("/boot").resolve()
    path_boot_efi = Path("/boot/efi").resolve()
    path_dev_sda1 = Path("/dev/sda1").resolve()

    if path_efi in mounts:
        disk = mounts[path_efi]
        return disk.resolve(strict=True)

    if path_boot_efi in mounts:
        disk = mounts[path_boot_efi]
        return disk.resolve(strict=True)

    if path_boot in mounts:
        disk = mounts[path_boot]
        return disk.resolve(strict=True)

    for disk in mounts.values():
        if disk == path_dev_sda1:
            return disk.resolve(strict=True)

    return path_dev_sda1


def _get_disk_and_part(path: Path) -> Tuple[Path, int]:
    """Given the path to a partition device, get the path to the parent disk
    and get the partition number.

    Arguments:
        path (Path): The path to a partition device, e.g. ``/dev/sda1``.

    Returns:
        Tuple[Path, int]:
            The path to the parent disk, e.g. ``/dev/sda``, and the partition
            number, e.g. 1.
    """
    # TODO: This depends heavily on the standard naming convention in Linux,
    # which is not guaranteed to be stable. It would be more appropriate to read
    # this data from sysfs. See https://unix.stackexchange.com/a/226426/202864.
    path = path.resolve(strict=True)
    path_str = str(path)
    for idx, char in reversed(list(enumerate(path_str))):
        if "0" <= char <= "9":
            disk_path = Path(path_str[:idx]).resolve(strict=True)
            partition = int(path_str[idx:])
            return disk_path, partition
    else:
        raise ValueError("could not parse EFI system partition from path")


def _hex(n: int) -> str:
    """Convert an integer into a 4-digit hex string, with no '0x' prefix."""
    return f"{n:0>4X}"


def _parse_bootcurrent(line: str) -> int:
    try:
        match = re.fullmatch(r"BootCurrent: ([0-9a-fA-F]{4})", line)
        bootnum = match.group(1)
        return int(bootnum, 16)
    except (AttributeError, ValueError) as e:
        raise RuntimeError(f'failed to parse efibootmgr: "{line}"') from e


def _parse_bootnext(line: str) -> int:
    try:
        match = re.fullmatch(r"BootNext: ([0-9a-fA-F]{4})", line)
        bootnum = match.group(1)
        return int(bootnum, 16)
    except (AttributeError, ValueError) as e:
        raise RuntimeError(f'failed to parse efibootmgr: "{line}"') from e


def _parse_bootorder(line: str) -> List[int]:
    try:
        match = re.fullmatch(r"BootOrder: (([0-9a-fA-F]{4},?)*)", line)
        bootnum_list = match.group(1).split(",")
        return [int(bootnum, 16) for bootnum in bootnum_list]
    except (AttributeError, ValueError) as e:
        raise RuntimeError(f'failed to parse efibootmgr: "{line}"') from e


def _parse_timeout(line: str) -> int:
    try:
        match = re.fullmatch(r"Timeout: ([0-9]+) seconds", line)
        timeout = match.group(1)
        return int(timeout)
    except (AttributeError, ValueError) as e:
        raise RuntimeError(f'failed to parse efibootmgr: "{line}"') from e


def _parse_entry(line: str) -> Tuple[int, bool, str]:
    try:
        match = re.fullmatch(r"Boot([0-9a-fA-F]{4})([* ]) (.+?)(\t.*)?", line)
        bootnum = match.group(1)
        active = match.group(2) == "*"
        label = match.group(3)
        return int(bootnum, 16), active, label
    except (AttributeError, ValueError) as e:
        raise RuntimeError(f'failed to parse efibootmgr: "{line}"') from e


def _parse_efibootmgr_stdout(text: str) -> EfiState:
    bootcurrent: Optional[int] = None
    bootnext: Optional[int] = None
    bootorder: List[int] = []
    timeout: Optional[int] = None
    labels: Dict[int, str] = {}
    active_set: Set = set()

    for line in text.splitlines():
        if line.startswith("BootCurrent"):
            bootcurrent = _parse_bootcurrent(line)
        elif line.startswith("BootNext"):
            bootnext = _parse_bootnext(line)
        elif line.startswith("BootOrder"):
            bootorder = _parse_bootorder(line)
        elif line.startswith("Timeout"):
            timeout = _parse_timeout(line)
        else:
            bootnum, active, label = _parse_entry(line)
            labels[bootnum] = label
            if active:
                active_set.add(bootnum)

    return EfiState(
        bootcurrent=bootcurrent,
        bootnext=bootnext,
        bootorder=bootorder,
        timeout=timeout,
        labels=labels,
        active=active_set,
    )


@dataclass
class EfibootmgrController(EfiController):
    """An `~efiboot.EfiController` for Unix.

    The current implementation delegates to the ``efibootmgr`` CLI.

    Parameters:
        disk_path (~pathlib.Path):
            Path to the disk containing the EFI System Partition,
            e.g. ``/dev/sda``.
        partition (int):
            The partition number of the EFI System Partition.
        edd (int):
            The EDD version (1 or 3; -1 for autodetect).
        edd_device (int):
            The EDD 1.0 device number, usually 0x80.
        force_gpt (bool):
            If true, treat disks with invalid PMBR as GPT.
    """

    disk_path: Path  #: Disk containing the ESP.
    partition: int  #: The ESP partition number.
    edd: int  #: EDD version (1 or 3, -1 for autodetect).
    edd_device: int  #: EDD 1.0 device number, usually 0x80.
    force_gpt: bool  #: Treat disks with invalid PMBR as GPT.

    @classmethod
    def from_config(cls, config: Config) -> EfiController:
        # Get the path to the ESP
        # First check the config, then fall back to a search heruristic.
        # The default from the heuristic is `/dev/sda1`.
        esp_path = config.options.get("esp") or _find_esp()
        esp_path = Path(esp_path)

        # Get the disk and partition number.
        disk_path, partition = _get_disk_and_part(esp_path)

        # Get read or use defaults for the other values.
        edd = config.options.get("edd", -1)
        edd_device = config.options.get("edd_device", 0x80)
        force_gpt = config.options.get("force_gpt", False)

        # Construct the controller.
        return cls(
            disk_path=disk_path,
            partition=partition,
            edd=edd,
            edd_device=edd_device,
            force_gpt=force_gpt,
        )

    @classmethod
    def is_compatible_with_host(cls) -> bool:
        if shutil.which("efibootmgr") is None:
            logger.warning("the efibootmgr backend requires the efibootmgr CLI")
            return False
        return True

    def _execute(self, *args: str) -> EfiState:
        # Build the command.
        cmd = ["efibootmgr", *args]

        # Ensure all commands target the EFI partition.
        cmd += ["--disk", str(self.disk_path)]
        cmd += ["--part", str(self.partition)]

        # Set EDD flags if given.
        # Use the builtin `hex` function, not our custom `_hex` function.
        if self.edd != -1:
            cmd += ["--edd", self.edd]
        if self.edd == 1:
            cmd += ["--device", hex(self.edd_device)]

        # Set the GPT flag as needed.
        if self.force_gpt:
            cmd += ["--gpt"]

        # Run the command.
        logger.debug(f"call: {cmd}")
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8")

        # Log subprocess errors.
        if proc.returncode != 0:
            logger.error(f"failed to execute command: {cmd}")
            raise RuntimeError(proc.stderr)

        # Return the new state.
        return _parse_efibootmgr_stdout(proc.stdout)

    def get_state(self) -> EfiState:
        return self._execute()

    def create(self, entry: BootEntry) -> EfiState:
        label = entry.label

        # Convert Unix-style path to EFI-style path.
        loader = entry.loader.replace("/", "\\")

        # Assemble the cmdline
        if entry.params is None:
            cmdline = ""
        else:
            cmdline = " ".join(entry.params)

        return self._execute(
            "--create", "--label", label, "--loader", loader, "--unicode", cmdline
        )

    def delete(self, bootnum: int) -> EfiState:
        return self._execute(f"--bootnum", _hex(bootnum), "--delete-bootnum")

    def activate(self, bootnum: int) -> EfiState:
        return self._execute(f"--bootnum", _hex(bootnum), "--active")

    def deactivate(self, bootnum: int) -> EfiState:
        return self._execute(f"--bootnum", _hex(bootnum), "--inactive")

    def set_bootnext(self, bootnum: int) -> EfiState:
        return self._execute("--bootnext", _hex(bootnum))

    def unset_bootnext(self) -> EfiState:
        return self._execute("--delete-bootnext")

    def set_bootorder(self, bootorder: List[int]) -> EfiState:
        hex_bootorder = ",".join(_hex(bootnum) for bootnum in bootorder)
        return self._execute("--bootorder", hex_bootorder)

    def unset_bootorder(self) -> EfiState:
        return self._execute("--delete-bootorder")

    def set_timeout(self, seconds: int) -> EfiState:
        return self._execute("--timeout", str(seconds))

    def unset_timeout(self) -> EfiState:
        return self._execute("--delete-timeout")
