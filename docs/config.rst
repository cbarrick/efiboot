Configuration Format
===========================================================================

Efiboot configuration is canonically stored in a `TOML <https://toml.io>`_ file
located at ``/boot/efiboot.toml``.

Here is an example:

.. code:: toml

    # /boot/efiboot.toml

    backend = 'efibootmgr'
    esp = '/dev/sda1'
    timeout = 3

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

The file contains global configuration options followed by zero or more boot
entry specifications.


Global Configuration
---------------------------------------------------------------------------

The following global configuration options are recognized by all backends.

**backend** (string)
    The backend to use. The list of first-party backends can be found in the
    API docs under :mod:`efiboot.backends`. The default will select an
    appropriate backend based on your current platform.

**timeout** (int)
    The boot timeout in seconds. Set this to -1 to clear the timeout and revert
    to your motherboard's default behavior. When this option is not set, Efiboot
    will not modify the timeout.


Efibootmgr backend
---------------------------------------------------------------------------

The following global options are recognized by the ``efibootmgr`` backend.

**esp** (string)
    The block device for the EFI System Partition. If not given, the backend
    will attempt to automatically determine the patrition or fall back to
    ``/dev/sda1``.

**edd** (int):
    The EDD version to use. Must be one of 1, 3, or -1. The default value is
    -1, which allows the backend to autodetect the appropriate EDD version.

**edd_device** (int):
    The EDD 1.0 device number. Defaults to 0x80.

**force_gpt** (bool):
    If true, the backend treats disks with invalid PMBR as GPT.


Boot Entries
---------------------------------------------------------------------------

Each boot entry begins with a ``[[BootEntry]]`` header.

The order of boot entries matters. The first entry will be set as the default,
and the EFI will be configured to fallback in order.

**label** (string)
    The name of the boot entry. All boot entries must have a label, and all
    labels must be unique.

**loader** (string)
    The path to the EFI application to boot, relative to the EFI System
    Partition. All boot entries must have a loader. The Linux kernel is a valid
    EFI application.

**params** (list of strings)
    Optional parameters to pass to the loader at boot.
