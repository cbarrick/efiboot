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
def timeout(args: Dict[str, Any], config: Config) -> int:
    """Get or set the EFI boot timeout.

    Usage:
        efiboot timeout
        efiboot timeout <timeout>
        efiboot timeout clear
        efiboot timeout --help

    Options:
        -h, --help    Print this help message and exit.

    Arguments:
        <timeout>    The new timeout in seconds.
    """
    facade = EfiBoot(config)

    # Since the usage string with "<timeout>" comes before the one with "clear",
    # then "<timeout>" will always match, and the value may be "clear".
    timeout = args["<timeout>"]

    if timeout is not None:
        try:
            if timeout == "clear":
                facade.unset_timeout()
            else:
                try:
                    timeout_secs = int(timeout)
                    if 0 <= timeout_secs:
                        raise ValueError()
                except:
                    print("invalid timeout", timeout)
                    return 1
                facade.set_timeout(timeout_secs)
        except:
            logger.error(f"could not set timeout: {repr(timeout)}")
            return 1

    facade.print_timeout()
    return 0
