What is Efiboot
===========================================================================

Efiboot is a tool for managing EFI boot entries.

What?
---------------------------------------------------------------------------

Efiboot is **not** a bootloader. It is a tool that interacts with the EFI
firmware of the system, which is itself acting as a bootloader. Using efiboot,
boot entries can be created, reshuffled, and removed.

Unlike similar tools, efiboot is designed to support interactive human users.
Efiboot provides a comfortable command line interface, a `configuration
format </config>`_ for maintaining boot entry definitions, and a `Python API
</api/efiboot>`_ for more complex scripting needs.

How?
---------------------------------------------------------------------------

Bootloaders are a relic of the past. Modern EFI systems can load OS kernels
directly, speeding up boot times. Many motherboards even provide pretty UIs
for selecting among boot entries.

These boot entries are stored in EFI variables on your motherboard. By
manipulating these variables, we can create and delete boot entries, manage
boot priority, and even override the entry to be used for the next boot.

Unfortunately, EFI variables are painful to modify by hand. Instead, efiboot
provides a configuration file for specifying the intended state and a command
line tool for pushing that configuration to the EFI.

Why?
---------------------------------------------------------------------------

Red Hat's `efibootmgr`_ is another popular tool for managing EFI boot entries.
However, efibootmgr is a relatively low-level tool. It only provides an
imperative interface for adding and removing boot entries. It does not provide
any assistance in *managing* those boot entries. Simple tasks like changing the
command line parameters of your kernel is a chore with efibootmgr.

After years of slogging around with efibootmgr and growing frustrated with its
obtuse interface, I decided to bite the bullet and implement a configuration
framework on top. Efiboot is the result of that effort.


.. _efibootmgr: https://github.com/rhboot/efibootmgr
