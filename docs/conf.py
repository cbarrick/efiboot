# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Path setup --------------------------------------------------------------

import os
import sys
import datetime

sys.path.insert(0, os.path.abspath("../src"))
now = datetime.datetime.utcnow()


# -- Project information -----------------------------------------------------

project = "Efiboot"
copyright = f"{now.year} Chris Barrick"
author = "Chris Barrick"


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = []

root_doc = "index"
source_encoding = "utf-8"
default_role = "py:obj"


# -- Options for HTML output -------------------------------------------------

html_title = project
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["furo_tweaks.css"]
html_js_files = []

pygments_style = "tango"
pygments_dark_style = "rrt"


# -- sphinx.ext.autodoc ------------------------------------------------------

autodoc_mock_imports = ["docopt", "toml"]
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autoclass_content = "class"

autodoc_default_options = {
    "members": False,
    "special-members": False,
}


# -- sphinx.ext.autosummary --------------------------------------------------

autosummary_generate = True


# -- sphinx.ext.todo ---------------------------------------------------------

todo_include_todos = True


# -- sphinx.ext.intersphinx --------------------------------------------------

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
