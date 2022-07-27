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


# Configuration
# ---------------------------------------------------------------------------

# Disable all implicit rules.
.SUFFIXES:

# Tools used in the recipes.
# These allow the user to override the tools.
SHELL := /bin/sh
PYTHON3 ?= python3
PIP ?= $(PYTHON3) -m pip
SPHINXBUILD ?= sphinx-build
BLACK ?= black

# Tool flags.
# These allow the user to specify extra flags to tools.
PIPFLAGS ?=
SPHINXFLAGS ?= -aEn -j auto -b dirhtml

# Installation directories.
# We mostly follow the GNU conventions here.
# https://www.gnu.org/prep/standards/html_node/Directory-Variables.html
DESTDIR ?= /
prefix := /usr/local
datarootdir := $(prefix)/share
licensedir := $(datarootdir)/licenses
docdir := $(datarootdir)/doc
htmldir := $(docdir)

# Local sources.
srcdir := .
pysrcdir := $(srcdir)/src
docsrcdir := $(srcdir)/docs
sources := $(shell find $(pysrcdir) -type f -not -path *__pycache__*)
docsources := $(shell find $(docsrcdir) -type f)

# The version as specified in pyproject.toml is used in some file names.
version := $(shell sed -En 's/version = "(.*)"/\1/p' pyproject.toml)


# Help Targets
# ---------------------------------------------------------------------------

.DEFAULT: help
.PHONY: help debug

help:
	@echo "The efiboot build system.                                       "
	@echo "                                                                "
	@echo "USAGE                                                           "
	@echo "    make [<options>...] [<target>...]                           "
	@echo "                                                                "
	@echo "HELP TARGETS                                                    "
	@echo "    help     Print this help message.                           "
	@echo "    debug    Print all options and their values.                "
	@echo "                                                                "
	@echo "BUILD TARGETS                                                   "
	@echo "    all      Build all artifacts.                               "
	@echo "    wheel    Build the Python wheel package.                    "
	@echo "    sdist    Build the Python sdist package.                    "
	@echo "    docs     Build the HTML documentation.                      "
	@echo "                                                                "
	@echo "INSTALL TARGETS                                                 "
	@echo "    install            Install efiboot.                         "
	@echo "    install-license    Install the license file.                "
	@echo "    install-docs       Install the HTML documentation.          "
	@echo "    install-all        Install everything.                      "
	@echo "                                                                "
	@echo "CHECK TARGETS                                                   "
	@echo "    check          Run all checks.                              "
	@echo "    check-build    Perform a full build in a clean environment. "
	@echo "    check-fmt      Check the source code formatting.            "
	@echo "                                                                "
	@echo "CLEAN TARGETS                                                   "
	@echo "    clean            Cleanup everything.                        "
	@echo "    clean-venv       Cleanup the development environment.       "
	@echo "    clean-dist       Cleanup the built Python packages.         "
	@echo "    clean-docs       Cleanup the HTML documentation.            "
	@echo "    clean-pycache    Cleanup the __pycache__ directories.       "
	@echo "                                                                "
	@echo "DEVELOPMENT TARGETS                                             "
	@echo "    venv                Build a development environment.        "
	@echo "    activate            Activate the development environment.   "
	@echo "    fmt                 Reformat the source code.               "
	@echo "    sphinx-autobuild    Start a Sphinx development server.      "

debug:
	@echo "SHELL       : $(SHELL)                                          "
	@echo "PYTHON3     : $(PYTHON3)                                        "
	@echo "PIP         : $(PIP)                                            "
	@echo "SPHINXBUILD : $(SPHINXBUILD)                                    "
	@echo "BLACK       : $(BLACK)                                          "
	@echo "PIPFLAGS    : $(PIPFLAGS)                                       "
	@echo "DESTDIR     : $(DESTDIR)                                        "
	@echo "prefix      : $(prefix)                                         "
	@echo "datarootdir : $(datarootdir)                                    "
	@echo "licensedir  : $(licensedir)                                     "
	@echo "docdir      : $(docdir)                                         "
	@echo "htmldir     : $(htmldir)                                        "
	@echo "srcdir      : $(srcdir)                                         "
	@echo "pysrcdir    : $(pysrcdir)                                       "
	@echo "docsrcdir   : $(docsrcdir)                                      "
	@echo "version     : $(version)                                        "


# Build Targets
# ---------------------------------------------------------------------------

.PHONY: all wheel sdist docs

# The default target.
all: sdist wheel docs

# The core artifacts.
sdist: dist/efiboot-$(version).tar.gz
wheel: dist/efiboot-$(version)-py3-none-any.whl
docs: dist/docs/index.html

# Concrete Targets
# -------------------------

# Build the wheel.
dist/efiboot-$(version)-py3-none-any.whl: $(sources) pyproject.toml
	$(PYTHON3) -m build --wheel

# Build the sdist.
dist/efiboot-$(version).tar.gz: $(sources) pyproject.toml
	$(PYTHON3) -m build --sdist

# Build the docs.
dist/docs/%: $(docsources) $(sources) pyproject.toml
	$(SPHINXBUILD) -W $(SPHINXFLAGS) $(docsrcdir) dist/docs

# Create the dev environment.
.venv/%:
	$(PYTHON3) -m venv .venv
	.venv/bin/python3 -m pip install --upgrade pip
	.venv/bin/python3 -m pip install build flit
	.venv/bin/flit install -s


# Install Targets
# ---------------------------------------------------------------------------

.PHONY: install install-license install-docs install-all

# Run all install recipes.
install-all: install install-license install-docs

# Install the wheel using pip.
#
# 1. We use --root and --prefix to specify the install location. The prefix
#    must be given as a path relative to the destdir. (Absolute paths are
#    resolved relative to the real root!!)
#
# 2. We use --no-warn-script-location because we don't care where the user
#    chooses to put the scripts.
#
# 3. We don't want to touch the network and we don't care about dependencies.
#    We will clobber any previously installed version of this package, even if
#    it breaks whatever else is installed. It's the user's job to make sure
#    that is all sorted out ahead of time. For pip, we use --ignore-installed,
#    --no-deps, --no-cache-dir, and --no-index.
#
# 4. We do not want to compile .pyc files with pip at this time. The user may
#    want to compile them with their own optimizations later; --no-compile.
#
# 5. We want to install the package as if it was downloaded from PyPI. In this
#    case, we DO NOT pass the path to the wheel file. Instead we use the
#    --find-links option and the logical package name.
install: wheel
	@mkdir -p "$(DESTDIR)$(prefix)"
	$(PIP) install \
		--root="$(DESTDIR)" \
		--prefix="./$(prefix)" \
		--no-warn-script-location \
		--ignore-installed \
		--no-deps \
		--no-cache-dir \
		--no-index \
		--no-compile \
		--find-links="./dist" \
		$(PIPFLAGS) \
		efiboot

# Install the license file.
install-license: LICENSE
	@mkdir -p "$(DESTDIR)$(licensedir)/efiboot"
	install -m644 "LICENSE" "$(DESTDIR)$(licensedir)/efiboot/LICENSE"

# Install the compiled docs.
install-docs: docs
	@mkdir -p "$(DESTDIR)$(htmldir)/efiboot"
	cp -r dist/docs/* "$(DESTDIR)$(htmldir)/efiboot"
	find "$(DESTDIR)$(htmldir)/efiboot" -type f | xargs -tn1 chmod 644


# Check Targets
# ---------------------------------------------------------------------------

.PHONY: check check-build check-fmt

# Run tests.
check: check-build check-fmt

# Force rebuild everything in a clean environment.
check-build:
	$(MAKE) clean venv
	. .venv/bin/activate && $(MAKE) -B all

# Check style.
check-fmt:
	$(BLACK) --check $(pysrcdir)


# Clean Targets
# ---------------------------------------------------------------------------

.PHONY: clean clean-venv clean-dist clean-docs clean-pycache

# Cleanup the venv and all build artifacts.
clean: clean-venv clean-dist clean-docs clean-pycache

# Individual clean recipes.
# After cleaning docs, we touch the index. Useful if autobuild is running.
clean-venv:; rm -rf .venv
clean-dist:; rm -rf dist
clean-docs:; rm -rf $(docsrcdir)/api dist/docs && touch $(docsrcdir)/index.rst
clean-pycache:; find $(pysrcdir) -name __pycache__ | xargs -tn1 rm -rf


# Development Targets
# ---------------------------------------------------------------------------

.PHONY: venv activate fmt sphinx-autobuild

# Create the virtual environment.
venv: .venv/bin/activate

# Activate the virtual environment in a new subshell.
activate: .venv/bin/activate
	$$SHELL -c ". .venv/bin/activate && exec $$SHELL -i"

# Format the code using Black.
fmt: .venv/bin/black
	.venv/bin/black $(pysrcdir)

# Launch a sphinx-autobuild server for the docs.
sphinx-autobuild: .venv/bin/sphinx-autobuild docs
	.venv/bin/sphinx-autobuild \
		$(SPHINXFLAGS) \
		--watch '$(pysrcdir)' \
		--re-ignore '$(docsrcdir)/api/.*' \
		"$(docsrcdir)" dist/docs
