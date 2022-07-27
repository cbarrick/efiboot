Efiboot
==================================================

A configuration framework for EFI boot entries.


What?
--------------------------------------------------

> The Unified Extensible Firmware Interface (EFI or UEFI for short) is a new
> model for the interface between operating systems and firmware. It provides a
> standard environment for booting an operating system and running pre-boot
> applications. It is distinct from the commonly used "MBR boot code" method
> followed for BIOS systems.
>
> – [ArchWiki]

EFI systems can load the Linux kernel directly, obviating the need for a
bootloader. In practice however, configuring an EFI to do so can be cumbersome,
and thus traditional bootloaders are still commonplace. This largely stems from
the fact that bootloaders like GRUB can be easily configured through plain text
files while EFI variables are hard to access and binary formatted.

Efiboot bridges this gap by defining a sensible configuration file format for
EFI boot entries and providing a tool to push this config to the EFI variables.

[ArchWiki]: https://wiki.archlinux.org/index.php/Unified_Extensible_Firmware_Interface


Configuration
--------------------------------------------------

Boot entries are specified in a file `/boot/efiboot.toml`. Here's an example:

```toml
# /boot/efiboot.toml

esp = '/dev/sda1'
timeout = 3
backend = 'efibootmgr'

[[BootEntry]]
label = 'Arch Linux'
loader = '/vmlinuz-linux'
params = [
    'initrd=/initramfs-linux.img',
    'root=/dev/sdb2',
    'rw',
    'nvidia-drm.modeset=1'
]

[[BootEntry]]
label = 'Arch Linux (fallback)'
loader = '/vmlinuz-linux'
params = [
    'initrd=/initramfs-linux-fallback.img',
    'root=/dev/sdb2',
    'rw',
]

[[BootEntry]]
label = 'UEFI Shell'
loader = '/shellx64_v2.efi'
```

The order of the boot entries determines their priority. The first boot entry
will be set as the default.

Each boot entry contains the following:

- **name** (string): The name of the boot entry.

- **loader** (string): A path to the efistub binary that will be executed on
  boot. The path is relative to the root of the EFI System Partition.

- **params** (array of string): Additional command line arguments to be passed
  to the loader.

Additionally, the file may contain the following top-level options.

- **esp** (string): The device used for the EFI System Partition. If not
  specified, efiboot will attempt to find the ESP by looking for devices mounted
  to `/efi`, `/boot`, or `/boot/efi`. The final fallback is `/dev/sda1`.

- **timeout** (integer): The EFI boot manager timeout, in seconds. If set to -1,
  the timeout will be restored to the system default. If not set, the timeout
  will not be modified.

- **backend** (string): A Python import path to a efiboot backend. If not given,
  a suitable default will be chosen.

- Backends may support additional options.


Usage
--------------------------------------------------

```
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
```


Installation
--------------------------------------------------

Efiboot can be built with [Poetry] and installed with Pip.

```shell
# Build a wheel package at ./dist/efiboot-VERSION-py3-none-any.whl
$ poetry build -f wheel

# Install the wheel using pip.
$ pip install dist/*.whl
```

[Poetry]: https://python-poetry.org/


### Dependencies

- **Python** >= 3.8
- **[efibootmgr]** to read and update the boot entries.
- **[toml]** package for Python to read the config file.
- **[docopt]** to parse CLI arguments.

[efibootmgr]: https://github.com/rhboot/efibootmgr
[toml]: https://github.com/uiri/toml
[docopt]: https://github.com/docopt/docopt


Prior work
--------------------------------------------------

Efiboot started out as a config file based frontend to [efibootmgr], a CLI tool
for reading and updating EFI boot entries.

[efibootmgr]: https://github.com/rhboot/efibootmgr
