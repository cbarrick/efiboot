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

"""Efiboot is a tool for managing EFI boot entries.

.. seealso::
    See the :doc:`/architecture` document for an overview of how these pieces
    fit together.


Reference
---------------------------------------------------------------------------


.. rubric:: The Facade

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.EfiBoot


.. rubric:: Configuration Files

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.Config
    ~efiboot.BootEntry


.. rubric:: EFI Controllers

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.EfiController
    ~efiboot.EfiState


.. rubric:: Miscellanea

.. autosummary::
    :toctree:
    :nosignatures:

    __version__
"""

from __future__ import annotations

import logging

try:
    from importlib import metadata
    from importlib.metadata import PackageNotFoundError
except:
    import importlib_metadata as metadata
    from importlib_metadata import PackageNotFoundError


logger = logging.getLogger(__name__)


# Re-exports
# ---------------------------------------------------------------------------

from .config import BootEntry, Config
from .controller import EfiController, EfiState
from .facade import EfiBoot


# Misc
# ---------------------------------------------------------------------------


def _version():
    """Read the version string from the package metadata."""
    try:
        return metadata.version("efiboot")
    except PackageNotFoundError:
        return "0.0.0"


#: The version string.
#:
#: The version string is read from the package metadata when the package is
#: initialized.
#:
#: The string may be "0.0.0" if the package is not installed. This can happen
#: when importing the package directly from the source repository.
__version__ = _version()
