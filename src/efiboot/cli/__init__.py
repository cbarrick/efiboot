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

"""The ``efiboot`` command line interface.

The efiboot CLI is built from command objects. Command objects are implemented
as regular functions annotated with the `@command <command>` decorator. The
docstrings of these functions are written in `docopt <http://docopt.org>`_
format, which is used to generate the argv parser.


Custom Commands
---------------------------------------------------------------------------

Any Python package may provide a command. To register a new command with
efiboot, a package provides an `entry point <entry_point_>`_ in the
``efiboot_cli`` namespace pointing to the `command` object.

.. _entry_point: https://setuptools.pypa.io/en/latest/userguide/entry_point.html

.. rubric:: Example

A minimal command:

.. code:: python

    # Module: examplepkg.example_command

    from efiboot.cli import command
    from efiboot.config import Config

    @command
    def hello(args: Dict[str, Any], config: Config) -> int:
        \"""A simple command.

        Usage:
            efiboot hello --name <name>
            efiboot hello --help

        Options:
            --name  Your name.
        \"""
        print('hello', args['--name'])
        return 0

The command must be registered in the ``efiboot_cli`` entry point:

.. code:: toml

    # File: pyproject.toml

    [project.entry-points.efiboot_cli]
    hello = 'examplepkg.example_command:hello'

The function can then be called from the command line:

.. code:: console

    $ efiboot hello --name chris
    hello chris


Reference
---------------------------------------------------------------------------

.. rubric:: Entry Point

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.cli.main


.. rubric:: Commands

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.cli.bootnext
    ~efiboot.cli.push
    ~efiboot.cli.status
    ~efiboot.cli.timeout


.. rubric:: Command Utilities

.. autosummary::
    :toctree:
    :nosignatures:

    ~efiboot.cli.command
    ~efiboot.cli.all_commands
"""

from __future__ import annotations

import functools
import logging
import textwrap
from inspect import cleandoc
from typing import Any, Callable, Dict, List

try:
    from importlib import metadata
except:
    import importlib_metadata as metadata

try:
    from functools import cache
except:
    from functools import lru_cache as cache

from docopt import docopt


logger = logging.getLogger(__name__)


# CLI Infrastructure
# ---------------------------------------------------------------------------


def _fixup_docstring(obj: Any) -> str:
    """Takes a command docstring and processes it.

    The original command docstring should be in docopt format. This returns
    a string in reStructuredText format for Sphinx documentation.

    Arguments:
        obj (Any): The object whose docstring should be processed.

    Returns:
        str: The new docstring.
    """
    doc = obj.__doc__

    # Wrap the docstring under a code directive.
    first_line = doc.splitlines()[0]
    new_doc = first_line + "\n\n"
    new_doc += ".. code:: text\n\n"
    new_doc += textwrap.indent(cleandoc(doc), "     ")
    new_doc += "\n"

    # Add an autodata directive.
    # new_doc += f'.. autodata:: {obj.__module__}.{obj.__name__}\n'

    return new_doc


def _command_summary() -> str:
    """Generate summary documentation for all commands.

    The summary can be appended to the CLI help message.

    Returns:
        str:
            The summary.
    """
    commands = sorted((name, cmd.summary) for name, cmd in all_commands().items())

    longest_name = 0
    for name, _ in commands:
        if longest_name < len(name):
            longest_name = len(name)

    doc = "Commands:\n"
    for name, summary in commands:
        doc += "    " + name.ljust(longest_name + 4) + summary + "\n"
    return doc


def all_commands() -> Dict[str, command]:
    """Get the set of all commands.

    Returns:
        Dict[str, command]: A mapping from name to command object.
    """
    entry_points = metadata.entry_points()["efiboot_cli"]

    # Import the commands.
    #
    # We check if the same name is registered twice. This can happen when a
    # third-party package tries to register a command with the same name as
    # a builtin command. In such a case, the command is ignored.
    commands = {}
    for ep in entry_points:
        if ep.name in commands:
            logger.warning(f"duplicate definition of subcommand: {ep.name}")
            commands.pop(ep.name)
        else:
            commands[ep.name] = ep.load()

    return commands


@cache
def all_backends() -> Dict[str, command]:
    """Get the set of all commands, indexed by name.

    Returns:
        Dict[str, command]
            The commands.
    """
    entry_points = metadata.entry_points()["efiboot_cli"]
    commands = []

    # Import the commands.
    # We attach the entry point name to the command for convenience.
    for ep in entry_points:
        command = ep.load()
        command.__efiboot_cli__ = ep.name
        commands.append(command)

    # Remove duplicates.
    # If two different commands present the same name, remove both.
    commands = sorted(commands, key=lambda c: c.__efiboot_cli__)
    i = 0
    while i + 1 < len(commands):
        a, b = commands[i], commands[i + 1]
        if a == b:
            commands.pop(i + 1)
        elif a.__efiboot_cli__ == b.__efiboot_cli__:
            name = a.__efiboot_cli__
            logger.warning(f"different commands with the same name: {name}")
            logger.warning(f"ignoring commands: A = {repr(a)}, B = {repr(b)}")
            commands.pop(i + 1)
            commands.pop(i)
        else:
            i += 1

    # Index the commands by name.
    return {c.__efiboot_cli__: c for c in commands}


def get_command(name: str) -> command:
    """Get a command by name.

    Arguments:
        name (str): The name of the command.

    Returns:
        command: The command.

    Raises:
        KeyError: No such command.
    """
    return all_commands()[name]


class command:
    """A decorator for CLI command functions.

    The efiboot CLI is built from `command` objects. Command objects are
    implemented as regular functions annotated with the ``@command`` decorator.
    The docstrings of these functions are written in `docopt`_ format, which is
    used to generate the argv parser.

    All commands take an argument dictionary as their first argument and a
    `~efiboot.Config` as a keyword argument. They return an integer exit code.

    When calling a command object, you may pass a list of strings instead of an
    argument dict. In this case, the list will be parsed as an argv list using
    docopt and converted into an args dictionary.

    .. _docopt: http://docopt.org

    See Also:
        See the :doc:`module-level docs <efiboot.cli>` for information on how
        to register efiboot commands from third-party packages.

    Example:

        .. code:: python

            from efiboot import EfiBoot
            from efiboot.cli import command
            from efiboot.config import Config

            @command
            def status(args: Dict[str, Any], config: Config) -> int:
                \"""Print EFI boot entries.

                Usage:
                    efiboot status
                    efiboot status --help

                Options:
                    -h, --help    Print this help message and exit.
                \"""
                facade = EfiBoot(config)
                facade.print_state()
                return 0
    """

    def __init__(self, fn: Callable):
        """Initialize the command object.

        This initializer uses :func:`functools.update_wrapper` to wrap the given
        function. This ensures the resulting command object behaves like the
        wrapped object.

        The docstring is preprocessed to be suitable for Sphinx API reference
        documentation. The original docstring is available in the :attr:`usage`
        attribute.
        """
        # Take the name, docstring, etc from fn.
        functools.update_wrapper(self, fn)

        # Fixup the docstring.
        self.__doc__ = _fixup_docstring(self)

    def __call__(self, args: Dict[str, Any] | List[str], **kwargs) -> int:
        """Call the command object.

        If `args` is a dictionary, this call passes through to the wrapped
        function. Otherwise the args are parsed with docopt before passing
        through.

        Arguments:
            args (Dict[str, Any] | List[str]):
                The arguments. A dict is passed through directly. A list is
                parsed with docopt first.
            **kwargs:
                Additional arguments to forward to the wrapped function.

        Returns:
            int:
                An exit code.
        """
        # If the user passed an args dict, pass through to the wrapped function.
        if isinstance(args, Dict):
            return self.__wrapped__(args, **kwargs)

        # Otherwise parse the args with docopt.
        # Note: ``options_first=True`` only works at the top-level. It is
        # impossible to properly implement subsubcommands with docopt.
        if self.__wrapped__.__name__ == "main":
            args = docopt(self.usage, args[1:], options_first=True)
        else:
            args = docopt(self.usage, args[1:])

        # Call the wrapped function with the parsed args dict.
        return self.__wrapped__(args, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the command.

        Returns:
            str: The repr.
        """
        return f"{command.__qualname__}({repr(self.__wrapped__)})"

    @property
    def usage(self) -> str:
        """The usage string for the command.

        This is the original docstring of the wrapped function.

        It is in `docop <http://docopt.org>`_ format and is used to generatate
        the argv parser for the command.
        """
        # Special case for `main` to also include the command summary.
        usage = cleandoc(self.__wrapped__.__doc__)
        usage += "\n"
        if self.__name__ == "main":
            usage += "\n" + _command_summary()
        return usage

    @property
    def summary(self) -> str:
        """The first line of the usage string.

        See :attr:`usage`.
        """
        return self.usage.split("\n", 1)[0]


# Re-exports
# ---------------------------------------------------------------------------

# The entry point.
from .__main__ import main

# The sub-commands.
#
# The module names start with an underscore to prevent naming conflict with the
# actual command objects.
from ._bootnext import bootnext
from ._push import push
from ._status import status
from ._timeout import timeout
