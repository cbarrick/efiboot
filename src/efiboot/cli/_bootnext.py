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
from typing import Any, Dict

from efiboot.cli import command
from efiboot.config import Config
from efiboot.facade import EfiBoot


logger = logging.getLogger(__name__)


@command
def bootnext(args: Dict[str, Any], config: Config) -> int:
    """Get or set the entry to boot into next.

    Usage:
        efiboot bootnext
        efiboot bootnext <entry>
        efiboot bootnext --help

    Options:
        -h, --help    Print this help message and exit.

    Arguments:
        <entry>    If given, sets the entry to boot next. This can either be a
                   boot label or a boot entry number (as a hex int).
    """
    facade = EfiBoot(config)
    entry = args["<entry>"]

    if entry is not None:
        try:
            matching_entries = facade.state.find(entry)
            if len(matching_entries) != 0:
                bootnext = matching_entries[0]
                facade.set_bootnext(bootnext)
            else:
                bootnext = int(entry, 16)
                facade.set_bootnext(bootnext)
        except:
            logger.error(f"could not set bootnext: {repr(entry)}")
            return 1

    facade.print_bootnext()
    return 0
