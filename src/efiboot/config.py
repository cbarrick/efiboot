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

import dataclasses
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

import tomli


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BootEntry:
    """A boot entry in the efiboot configuration.

    Parameters:
        label (str):
            The label for this boot entry. Labels must be unique throughout the
            config file.
        loader (str):
            The EFI application to boot. The loader is interpreted as a path
            relative to the root of the EFI system partition. The path may use
            either forward- or backward-slashes as the directory separator.
        params (List[str]):
            Command-line parameters to be passed to the loader. Details about
            command-line parameters in the Linux kernel can be found at
            https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html
    """

    label: str  #: Title of the boot entry.
    loader: str  #: EFI application to boot.
    params: List[str]  #: Command line params to pass.

    def validate(self):
        """Validate the boot entry.

        Raises:
            TypeError: A member has the wrong type.
            ValueError: A member has an invalid value.
        """
        if self.label == "":
            raise ValueError("BootEntry label must not be empty")

        if self.loader == "":
            raise ValueError("BootEntry loader must not be empty")

        for p in self.params:
            if not isinstance(p, str):
                raise TypeError(f"invalid BootEntry parameter: {repr(p)}")

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> BootEntry:
        """Create a boot entry from a dictionary.

        Arguments:
            d (Dict[str, Any]):
                A dictionary describing the boot entry.

        Returns:
            BootEntry:
                The parsed boot entry.
        """
        fields = set(f.name for f in dataclasses.fields(cls))
        for k in d.keys():
            if k not in fields:
                logger.warning(f"unknown BootEntry field: {k}")

        return cls(
            label=d.get("label", ""),
            loader=d.get("loader", ""),
            params=d.get("params", []),
        )


@dataclass(frozen=True)
class Config:
    """The efiboot configuration format.

    Efiboot configuration typically lives in a TOML file. This class provides
    several classmethods to load a Config object from such a file:

    - `Config.from_path`: parses a TOML file located at a given path.
    - `Config.from_file`: parses a config from a file-like object.
    - `Config.from_toml`: parses a config from a TOML string.
    - `Config.from_dict`: creates a config from a dict, e.g. the output of
      ``toml.loads``.

    See Also:
        The :doc:`/config` document contains additional details and examples.

    Parameters:
        path (Optional[~pathlib.Path]):
            The path to the config file. This may be None if the config was not
            parsed from a file.
        timeout (Optional[int]):
            The boot timeout in seconds. If this is not set, efiboot will not
            modify the boot timeout. If this is -1, efiboot will clear the boot
            timeout on the EFI, reverting to the motherboard's default value.
        backend (Optional[str]):
            The backend to use. This must be a dotted import path to a Python
            module providing an efiboot backend. See `efiboot.backends`.
        options (Dict[str, Any]):
            A dictionary of additional backend-specific options.
        entries (List[BootEntry]):
            The boot entries.
    """

    path: Optional[Path]  #: Path to the config file, if any.
    timeout: Optional[int]  #: The boot timeout in seconds.
    backend: Optional[str]  #: The backend to use.
    options: Dict[str, Any]  #: Additional options.
    entries: List[BootEntry]  #: The boot entries.

    def validate(self):
        """Validate the config.

        Raises:
            TypeError: A member has the wrong type.
            ValueError: A member has an invalid value.
        """
        # We don't strictly need to validate this.
        # If this is set, then we probably loaded the config from that path.
        if self.path is not None:
            if not isinstance(self.path, Path):
                raise TypeError(f"invalid path: {repr(self.path)}")
            if not self.path.exists():
                raise FileNotFoundError(f"file not found: {self.path}")

        if self.timeout is not None:
            if not isinstance(self.timeout, int):
                raise TypeError(f"invalid timeout: {repr(self.timeout)}")
            if self.timeout < -1:
                raise ValueError(f"invalid timeout: {self.timeout}")

        if self.backend is not None:
            if not isinstance(self.backend, str):
                raise TypeError(f"invalid backend: {repr(self.backend)}")

        for entry in self.entries:
            entry.validate()

    @property
    def name(self) -> str:
        """A string name for this config."""
        if self.path is not None:
            return str(self.path)
        else:
            return "<anonymous_config>"

    @classmethod
    def empty(cls) -> Config:
        """Create an empty config object.

        Returns:
            Config:
                The config object.
        """
        return cls(
            path=None,
            timeout=None,
            backend="efiboot.backends.default",
            options={},
            entries=[],
        )

    @classmethod
    def from_dict(
        cls,
        d: dict,
        path: Optional[Path] = None,
        **kwargs,
    ) -> Config:
        """Create a config object from a dictionary.

        Arguments:
            d (Dict[str, Any]):
                A dictionary describing the config file.
            path (Optional[~pathlib.Path]):
                The path to the config file, if known.
            **kwargs:
                Overrides values in the resulting config object.

        Returns:
            Config:
                The config object.
        """
        d.update(kwargs)

        if "path" in d:
            raise ValueError("illegal config option: path")

        timeout = d.get("timeout")
        backend = d.get("backend")

        options = {}
        fields = set(f.name for f in dataclasses.fields(cls))
        for k, v in d.items():
            if k not in fields:
                options[k] = v

        entry_dicts = d.get("BootEntry", [])
        entries = [BootEntry.from_dict(ed) for ed in entry_dicts]

        return cls(
            path=path,
            timeout=timeout,
            backend=backend,
            options=options,
            entries=entries,
        )

    @classmethod
    def from_toml(
        cls,
        text: str,
        path: Optional[Path] = None,
        **kwargs,
    ) -> Config:
        """Parse a config object from a TOML string.

        Arguments:
            text (str):
                TOML data containing the config.
            path (Optional[~pathlib.Path]):
                The path to the config file, if known.
            **kwargs:
                Overrides values in the resulting config object.

        Returns:
            Config:
                The config object.
        """
        d = tomli.loads(text)
        return cls.from_dict(d, path, **kwargs)

    @classmethod
    def from_file(cls, fd: TextIO, **kwargs) -> Config:
        """Read a config object from a file.

        Arguments:
            fd (TextIO):
                TOML data containing the config.
            **kwargs:
                Overrides values in the resulting config object.

        Returns:
            Config:
                The config object.
        """
        text = fd.read()
        path = Path(fd.name) if fd.name is not None else None
        return cls.from_toml(text, path, **kwargs)

    @classmethod
    def from_path(cls, path: Path, **kwargs) -> Config:
        """Read a config object from a path.

        Arguments:
            path (~pathlib.Path):
                A path to a TOML file containing the config.
            **kwargs:
                Overrides values in the resulting config object.

        Returns:
            Config:
                The config object.

        Raises:
            FileNotFoundError:
                No config file was found.
        """
        with path.open() as fd:
            return cls.from_file(fd, **kwargs)
