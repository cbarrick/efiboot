Developer Quickstart
===========================================================================

This guide walks through everything you need to become a productive developer
for efiboot.

.. important::
    Efiboot on Linux requires `efibootmgr`_. You'll need to install it before
    continuing.

    .. _efibootmgr: https://github.com/rhboot/efibootmgr

    On Debian-based distributions:

    .. code:: console

        # apt install efibootmgr

    On Arch-based distributions:

    .. code:: console

        # pacman -S efibootmgr


Working Tree
---------------------------------------------------------------------------

The efiboot source repository looks like this:

.. code:: text

    .
    ├── LICENSE
    ├── README.md
    ├── Makefile
    ├── pyproject.toml
    ├── dist/
    │   └── ...
    ├── docs/
    │   └── ...
    └── src/
        └── ...

Lets go over what each of these are for.

Makefile
    The makefile is the heart of the development workflow. It contains recipes
    to initialize the development environment, build and install efiboot,
    format the source code, run the tests, and more. You'll be using the
    makefile throughout this guide.

pyproject.toml
    This contains the project metadata, dependency specs, and configuration for
    the build system and other tooling. To build efiboot, we use PyPA's `build`_
    and `flit`_ tools for the build frontend and backend respectively.

dist/
    This directory contains the build artifacts. It is not distributed with the
    efiboot source repository, but it will be created automatically as soon as
    you start development.

docs/
    This directory contains the project documentation used to build this site.
    The site is built with `Sphinx`_ and written using reStructuredText. The
    ``docs/api/`` directory is special: Its contents are generated from the
    source code and are not included in the source repository.

src/
    This directory contains the source code. Efiboot is implemented as a
    traditional Python package. You may find the :doc:`architecture` document
    and the :doc:`API Reference </api/efiboot>` helpful for finding your way
    around.

.. _build: https://pypa-build.readthedocs.io/en/stable/
.. _flit: https://flit.readthedocs.io/en/latest/
.. _Sphinx: https://www.sphinx-doc.org/en/master/


Initializing the Development Environment
---------------------------------------------------------------------------

The makefile includes a recipe for creating a Python `virtual environment
<venv_>`_ that contains everything you need for development:

.. _venv: https://docs.python.org/3/tutorial/venv.html

.. code:: console

    $ make venv

This creates the virtual environment in your working tree under ``.venv/``.

The virtual environment contains its own copy of Python and isolated
site-packages, as well as a few development tools and an editable install of
efiboot.

In your shell, the virtual environment must be *activated* so that the tools
and packages it provides are made available to you:

.. code:: console

    $ make activate

To deactivate the virtual environment and return to your system environment:

.. code:: console

    $ exit

Finally, if you need to obliterate your virtual environment and rebuild it from
scratch:

.. code:: console

    $ make clean venv


Writing Code
---------------------------------------------------------------------------

.. tip::
    The development environment includes `iPython`_. For interactive sessions,
    use ``ipython`` instead of ``python3``.

.. tip::
    If you are using an IDE, point it to the interpreter at
    ``.venv/bin/python3``.

The source code lives under ``src/``. Efiboot is implemented as a traditional
Python package. You may find the :doc:`architecture` document and the :doc:`API
Reference </api/efiboot>` helpful for finding your way around.

.. rubric:: Style

We use `Black`_ to format the source code. You can point your editor to the
formatter at ``.venv/bin/black`` or manually run the formatter:

.. code:: console

    $ make fmt

For questions of style not covered by the formatter, defer to the `Google Python
Style Guide <py_style>`_.

.. rubric:: Logging

All modules must include a logger:

.. code:: python

    import logging

    logger = logging.getLogger(__name__)

The user sets the log-level when they run efiboot, using ``--verbose``
(for INFO) or ``--debug`` (for DEBUG). The default log-level is WARNING.

.. rubric:: Type Annotations

All code must be type annotated, and all modules must contain the following:

.. code:: python

    from __future__ import annotations

This allows type annotations to be used before the types are declared. It also
allows for the use of newer type annotation syntax in a backwards-compatible
way.

.. rubric:: Dependencies

.. danger::
    Do not use ``pip`` to install dependencies. It may cause your environment
    to deviate from the canonical dev environment. If you do use ``pip``, you
    must also verify that your changes work in a clean dev environment.

The project metadata and dependencies are specified in ``pyproject.toml``. If
you make changes to this file, you may need to recreate the environment:

.. code:: console

    $ make clean venv

Alternatively, you can use `flit`_ to install the dependencies from
``pyproject.toml`` into your current environment:

.. code:: console

    $ flit install

.. _Black: https://black.readthedocs.io/en/stable/
.. _flit: https://flit.readthedocs.io/en/latest/
.. _iPython: https://ipython.org/
.. _py_style: https://google.github.io/styleguide/pyguide.html


Writing Documentation
---------------------------------------------------------------------------

The documentation (this site) is built with `Sphinx`_ and written in
reStructuredText. All documentation lives under the ``docs/`` directory.

To build the docs:

.. code:: console

    $ make docs

This will generate HTML documentation under ``dist/docs/``.

Note that the API docs are generated from the source code. The API documentation
lives under ``docs/api/``. This directory is initially empty and (re)populated
when you build the docs.

Sometimes doc generation will fail due to a leftover API document after a code
refactor. You can fix this by obliterating the generated docs:

.. code:: console

    $ make clean-docs

Often when writing docs, you want to continuously rebuild and serve the docs
on a local http server. There's a recipe for that:

.. code:: console

    $ make sphinx-autobuild

This will continuously rebuild and serve the documentation at
http://127.0.0.1:8000.

.. _Sphinx: https://www.sphinx-doc.org/en/master/


Running Tests
---------------------------------------------------------------------------

.. todo::
    No tests have been written yet. Once we have tests, we should add some
    details about the test harness here.

With your dev environment active:

.. code:: console

    $ make check

This will run all tests, check the code style, and rebuild the artifacts.


Packaging Efiboot
---------------------------------------------------------------------------

.. note::
    Efiboot is automatically installed into the development environment.

    This section is most useful for package maintainers.

To build efiboot:

.. code:: console

    $ make all

This will create the following:

- ``./dist/efiboot-X.Y.Z-py3-none-any.whl``: A Python *wheel* package for efiboot.
- ``./dist/efiboot-X.Y.Z.tar.gz``: A Python *sdist* package for efiboot.
- ``./dist/docs/*``: The HTML documentation (this website).

Each of these artifacts can be (re)created individually:

.. code:: console

    $ make sdist wheel doc

Once built, you can install efiboot into the current Python environment:

.. code:: console

    $ make install

The makefile more-or-less follows the `GNU Makefile Conventions <make_>`_. You
can use these conventions to install efiboot to an alternate location:

.. code:: console

    $ make install DESTDIR=${pkgdir} prefix=/usr

The makefile includes a variety of install recipes for package maintainers:

.. code:: console

    $ make install          # Installs efiboot using pip.
    $ make install-docs     # Installs the docs to ${prefix}/share/docs/efiboot.
    $ make install-license  # Installs the license to ${prefix}/share/licenses/efiboot.
    $ make install-all      # All of the above.

.. _make: https://www.gnu.org/prep/standards/html_node/Makefile-Conventions.html
