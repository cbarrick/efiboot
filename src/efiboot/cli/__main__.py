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
from typing import Any, Dict, List

import tomli

import efiboot
from efiboot.facade import EfiBoot
from efiboot.cli import command, get_command
from efiboot.config import Config


# We use the root efiboot logger instead of a module-specific logger.
logger = logging.getLogger("efiboot")


def _setup_logging(level: int = logging.WARNING):
    """Perform basic logging setup.

    This is called when using the efiboot CLI.

    Arguments:
        level: The log level.
    """
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="{levelname}: {message}",
        style="{",
        force=True,
    )


def _parse_overrides(overrides: List[str]) -> Dict[str, Any]:
    ret = {}
    for override_str in overrides:
        try:
            try:
                # First try to parse as TOML. This handles 'key=value' where
                # value is a quoted string, integer, or collection.
                override = tomli.loads(override_str)
                ret.update(override)
            except tomli.TOMLDecodeError:
                # Otherwise, fall back to 'key=value' where value as a string.
                key, value = override_str.split("=", 1)
                key = key.strip()
                value = value.strip()
                ret[key] = value

        except Exception as e:
            logger.debug(e)
            raise ValueError(f"failed to parse override: {override_str}")

    if len(ret) != 0:
        logger.debug(f"parsed overrides: {ret}")
    return ret


@command
def main(args: Dict[str, Any]) -> int:
    """Efiboot is a tool for managing EFI boot entries.

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
    """
    try:
        _setup_logging()

        # Parse command line args.
        print_version = args["--version"]
        verbose = args["--verbose"]
        debug = args["--debug"]
        config_path = args["--config"] or "/boot/efiboot.toml"
        overrides = args["-x"]
        cmd_name = args["<command>"]
        cmd_args = args["<args>"]

        # Handle `--verbose` and `--debug`.
        if verbose:
            _setup_logging(logging.INFO)
        if debug:
            _setup_logging(logging.DEBUG)

        # Handle `--version`.
        if print_version:
            print(efiboot.__version__)
            return 0

        # Parse config overrides from `-x`.
        override_dict = _parse_overrides(overrides)

        # Load the config.
        config_path = Path(config_path).resolve(strict=True)
        config = Config.from_path(config_path, **override_dict)
        config.validate()

        # Create a facade and run the subcommand.
        cmd_argv = [sys.argv[0], cmd_name, *cmd_args]
        cmd = get_command(cmd_name)
        return cmd(cmd_argv, config=config)

    except Exception as e:
        if debug:
            logger.exception(e)
        else:
            logger.error(e)
        return 1


def start():
    """The main entry point exported in pyproject.toml."""
    code = main(sys.argv)
    sys.exit(code)


if __name__ == "__main__":
    start()
