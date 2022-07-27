Quickstart
===========================================================================

Installing Efiboot
---------------------------------------------------------------------------

.. tip::
    Look for efiboot in your favorite package repository.

Efiboot is written in Python and published to PyPI. You can install it with
``pip``.

.. code:: console

    $ python3 -m pip install efiboot

On Linux, the default backend also depends on `efibootmgr`_, which should be
installed using your operating system's package manager. For example:

.. code:: console

    # apt install efibootmgr

.. _efibootmgr: https://github.com/rhboot/efibootmgr


Defining Boot Entries
---------------------------------------------------------------------------

Boot entries are defined in the file ``/boot/efiboot.toml``.

Each boot entry consists of:

1. A unique label,
2. The path to an EFI application, relative to the EFI System Partition,
3. The list of command line parameters.

For Linux, the EFI application can be the Linux kernel itself or a bootloader
(e.g. ``grub.efi``). For Windows, the bootloader is usually
``\EFI\Microsoft\boot\bootmgfw.efi``.

Efiboot can handle both forwards- and backwards-slash as the path separator.

Full details about the syntax of this file are given in the :doc:`config`
document.

.. rubric:: Example

.. code:: toml

    # File: /boot/efiboot.toml

    [[BootEntry]]
    label = 'Arch Linux'
    loader = '/vmlinuz-linux'
    params = [
        'initrd=/amd-ucode.img',
        'initrd=/initramfs-linux.img',
        'root=/dev/disk/by-label/arch-linux',
        'rw',
        'nvidia-drm.modeset=1',
        'acpi_enforce_resources=lax',
    ]

    [[BootEntry]]
    label = 'Arch Linux (fallback)'
    loader = '/vmlinuz-linux'
    params = [
        'initrd=/initramfs-linux-fallback.img',
        'root=/dev/disk/by-label/arch-linux',
        'rw',
    ]


Updating the EFI
---------------------------------------------------------------------------

Each time you modify your ``efiboot.toml``, you must push those changes to the
EFI.

.. code:: console

    # efiboot push


Other Commands
---------------------------------------------------------------------------

Efiboot provides many other commands to help manage your boot entries.

- ``efiboot status`` lets you to view all boot entries in your EFI.
- ``efiboot bootnext`` lets you to pick the boot entry for your next reboot.
- ``efiboot timeout`` lets you set the timeout on the EFI boot screen.

For a full list of functionality, see ``efiboot --help``.
