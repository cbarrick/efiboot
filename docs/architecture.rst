.. currentmodule:: efiboot

Architecture
===========================================================================

Efiboot follows a simple, 3-layer architecture.

- At the top is the **command line interface**.
- In the middle is the **facade**, which provides the main Python API.
- At the bottom is the **component layer**, which consists of the configuration
  and controller components.

  This document is organized from the top down.

.. image:: /_static/architecture-light.svg
    :alt: Efiboot architecture diagram
    :width: 500px
    :height: 375px
    :align: center
    :class: only-light

.. image:: /_static/architecture-dark.svg
    :alt: Efiboot architecture diagram
    :width: 500px
    :height: 375px
    :align: center
    :class: only-dark


Command Line Interface
---------------------------------------------------------------------------

.. currentmodule:: efiboot.cli

Efiboot implements a toolbox-style CLI, similar to ``git``.

Lets take a look at the top-level help message:

.. code:: console

    $ efiboot --help
    Efiboot is a tool for managing EFI boot entries.

    Usage:
        efiboot [-vd] [-c <cfg>] [-x <key>=<value>...] <command> [<args>...]
        efiboot --version
        efiboot --help

    Options:
        -c <cfg>, --config <cfg>    Override the path to the config.
        -x <key>=<value>            Override a config value. May be repeated.
        -v, --verbose               Log additional information to stderr.
        -d, --debug                 Log debug info to stderr. Implies --verbose.
        -V, --version               Print the version string and exit.
        -h, --help                  Print this help message and exit.

    Commands:
        bootnext    Get or set the entry to boot into next.
        push        Push the config to the EFI.
        status      Print EFI boot entries.
        timeout     Get or set the EFI boot timeout.

All invocations start with ``efiboot`` and any global options, followed by a
subcommand name and any subcommand-specific options.

The top-level ``efiboot`` command is equivalent to ``python3 -m efiboot.cli``.

The subcommands live in the :mod:`efiboot.cli` module. Each subcommand is a
"command" object, implemented as a regular Python function annotated with the
`@command <command>` decorator.

Let's take a look at the implementation of the `status` subcommand.

.. code:: python

    from efiboot.cli import command
    from efiboot.config import Config
    from efiboot.facade import EfiBoot

    @command
    def status(args: Dict[str, Any], config: Config) -> int:
        '''Print EFI boot entries.

        Usage:
            efiboot status
            efiboot status --help

        Options:
            -h, --help    Print this help message and exit.
        '''
        facade = EfiBoot(config)
        facade.print_state()
        return 0

A subcommand takes an argument dictionary and a config (described below) and
returns an integer exit code. The docstring of the function describes the CLI
using the `docopt <http://docopt.org/>`_ language. The docstring is used to
generate an argument parser for the command.

Subcommands must be registered as an `entry point`_ in the ``efiboot_cli``
namespace. Third-party packages are also allowed to register additional
subcommands. See `efiboot.cli` for more information.

Subcommands are usually lightweight functions that delegate their main
functionality to the facade. When implementing a new subcommand, prefer to add
the business logic to the facade class so that users of the Python API also
have access to the feature.

The CLI lives under ``src/efiboot/cli/``. The primary entry point is
``src/efiboot/cli/__main__.py``.

All first-party subcommands are registered in the ``pyproject.toml`` file.

.. _entry point: https://setuptools.pypa.io/en/latest/userguide/entry_point.html


Python Facade
---------------------------------------------------------------------------

.. currentmodule:: efiboot

The main Python API is provided by the :class:`EfiBoot` facade class.

This facade combines a `Config` and an `EfiController` and provides the
highest-level functionality. For example, a facade can push configured boot
entries to the EFI variables on your machine.

The `EfiBoot` constructor can take a `Config` and an `EfiController` or it can
read the standard config (``/boot/efiboot.toml``) and pick an appropriate
controller.

All significant user-facing features should be implemented as a method on the
facade with a simple companion command in the CLI.

The current state of the EFI variables as understood by the facade is available
through the member variable :attr:`EfiBoot.state`.

The facade code live in ``src/efiboot/facade.py``.


Configuration Files
---------------------------------------------------------------------------

.. currentmodule:: efiboot

.. seealso::
    See the :doc:`config` document for syntax details.

The configuration is represented by the `Config` and `BootEntry` classes. These
are both simple dataclasses.

The `Config` class provides a stack of classmethods for parsing the config from
a TOML source:

- `Config.from_path`: parses a TOML file located at a given path.
- `Config.from_file`: parses a config from a file-like object.
- `Config.from_toml`: parses a config from a TOML string.
- `Config.from_dict`: creates a config from a dict, e.g. the output of
  ``toml.loads``.

The default config file path is ``/boot/efiboot.toml``.

The config parsing code lives in ``src/efiboot/config.py``.


Controllers and State
---------------------------------------------------------------------------

.. currentmodule:: efiboot

At its core, efiboot is a tool for manipulating EFI variables. We use the
`EfiController` and `EfiState` classes to accomplish this.

An `EfiState` is a simple dataclass representing the contents of EFI variables.
It tracks boot entries as integer IDs, which are typically printed as 4-digit
hex values. State objects are immutable.

An `EfiController` is an object that is capable of manipulating EFI variables.
Almost all controller methods return a new state object. Since APIs for
manipulating EFI variables differ by platform, the `EfiController` is an
abstract base class. Concrete controllers are provided by *backends*.

Controllers are usually created using the :func:`EfiController.from_config`
classmethod, which allows controllers to read values from the config during
initialization.

The controller API lives in ``src/efiboot/controller.py``.


Backends
---------------------------------------------------------------------------

.. currentmodule:: efiboot.backends

Backends provide a concrete controller class for a particular platform.

Backends are described by `BackendMetadata` objects. The backend metadata
describes what platforms the backend is compatible with and instructs efiboot
how to import and construct the corresponding controller class.

The main backend is called `default`. This backend implements a proxy pattern.
Depending on the users current platform, the default backend selects an
appropriate controller class from among the other backends and delegates all
functionality.

Backends may support additional options in the config.

Backends must be registered as an `entry point`_ in the ``efiboot_backends``
namespace. Like CLI commands, backends can be provided by third-party packages.
See `efiboot.backends` for details.

The backend code lives under ``src/efiboot/backends/``.

All first-party backends are registered in the ``pyproject.toml`` file.

.. _entry point: https://setuptools.pypa.io/en/latest/userguide/entry_point.html
