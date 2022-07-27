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

# Installation directories.
# We mostly follow the GNU conventions here.
# https://www.gnu.org/prep/standards/html_node/Directory-Variables.html
DESTDIR ?= /
prefix ?= /usr/local
datarootdir := $(prefix)/share
datadir := $(datarootdir)/efiboot
licensedir := $(datarootdir)/licenses/efiboot
docdir := $(datarootdir)/doc/efiboot
htmldir := $(docdir)

# Local sources.
srcdir := src
docsrcdir := docs
sources := $(shell find $(srcdir) -type f -not -path *__pycache__*)
docsources := $(shell find $(docsrcdir) -type f)

# The version as specified in pyproject.toml is used in some file names.
version := $(shell sed -En 's/version = "(.*)"/\1/p' pyproject.toml)


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
	.venv/bin/black $(srcdir)

# Launch a sphinx-autobuild server for the docs.
sphinx-autobuild: .venv/bin/sphinx-autobuild docs
	.venv/bin/sphinx-autobuild \
		-aEn \
		-j auto \
		-b dirhtml \
		--watch '$(srcdir)' \
		--re-ignore '$(docsrcdir)/api/.*' \
		"$(docsrcdir)" dist/docs


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
	$(BLACK) --check $(srcdir)


# Build Targets
# ---------------------------------------------------------------------------

.DEFAULT: all
.PHONY: all wheel sdist docs

# The default target.
all: sdist wheel docs

# The core artifacts.
sdist: dist/efiboot-$(version).tar.gz
wheel: dist/efiboot-$(version)-py3-none-any.whl
docs: dist/docs/index.html


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
clean-pycache:; find $(srcdir) -name __pycache__ | xargs -tn1 rm -rf


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
	mkdir -p "$(DESTDIR)$(prefix)"
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
	mkdir -p "$(DESTDIR)$(licensedir)"
	install -m644 "LICENSE" "$(DESTDIR)$(licensedir)/LICENSE"

# Install the compiled docs.
install-docs: docs
	mkdir -p "$(DESTDIR)$(htmldir)"
	cp -r dist/docs/* "$(DESTDIR)$(htmldir)"
	find "$(DESTDIR)$(htmldir)" -type f | xargs -tn1 chmod 644


# Concrete Targets
# ---------------------------------------------------------------------------

# Create the dev environment.
.venv/%:
	$(PYTHON3) -m venv .venv
	.venv/bin/python3 -m pip install --upgrade pip
	.venv/bin/python3 -m pip install build flit
	.venv/bin/flit install -s

# Build the wheel.
dist/efiboot-$(version)-py3-none-any.whl: $(sources) pyproject.toml
	$(PYTHON3) -m build --wheel

# Build the sdist.
dist/efiboot-$(version).tar.gz: $(sources) pyproject.toml
	$(PYTHON3) -m build --sdist

# Build the docs.
dist/docs/%: $(docsources) $(sources) pyproject.toml
	$(SPHINXBUILD) -aEnW -j auto -b dirhtml $(docsrcdir) dist/docs
