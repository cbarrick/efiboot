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
def push(args: Dict[str, Any], config: Config) -> int:
    """Push the config to the EFI.

    Usage:
        efiboot push
        efiboot push --help

    Options:
        -h, --help    Print this help message and exit.
    """
    facade = EfiBoot(config)
    facade.push()
    return 0
