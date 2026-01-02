#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Imports
#

import os
from os.path import abspath, dirname

from importlib.metadata import version as get_version

# Project must be built+installed to generate docs
import commands2

# -- RTD configuration ------------------------------------------------

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

# This is used for linking and such so we link to the thing we're building
rtd_version = os.environ.get("READTHEDOCS_VERSION", "latest")
if rtd_version not in ["stable", "latest"]:
    rtd_version = "stable"

# -- General configuration ------------------------------------------------


# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "robotpy_sphinx.all",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "RobotPy Commands v2"
copyright = "2021, RobotPy development team"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

release: str = get_version("robotpy-commands-v2")
version: str = ".".join(release.split(".")[:2])

autoclass_content = "both"

intersphinx_mapping = {
    "robotpy": (
        f"https://robotpy.readthedocs.io/projects/robotpy/en/{rtd_version}/",
        None,
    ),
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_rtd_theme"

# Output file base name for HTML help builder.
htmlhelp_basename = "RobotPyCommandDoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        "index",
        "RobotPyCommandV2Doc.tex",
        "RobotPy CommandV2 Documentation",
        "RobotPy development team",
        "manual",
    )
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "RobotPyCommandV2Doc",
        "RobotPy CommandV2 Documentation",
        "RobotPy development team",
        "RobotPyCommandV2Doc",
        "One line description of project.",
        "Miscellaneous",
    )
]

# -- Options for Epub output ----------------------------------------------

# Bibliographic Dublin Core info.
epub_title = "RobotPy CommandV2"
epub_author = "RobotPy development team"
epub_publisher = "RobotPy development team"
epub_copyright = "2021, RobotPy development team"

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["search.html"]

# -- Custom Document processing ----------------------------------------------

from robotpy_sphinx.regen import gen_package
from robotpy_sphinx.sidebar import generate_sidebar

generate_sidebar(
    globals(),
    "commandv2",
    "https://raw.githubusercontent.com/robotpy/docs-sidebar/master/sidebar.toml",
)

root = abspath(dirname(__file__))

gen_package(root, "commands2")
gen_package(root, "commands2.button")
gen_package(root, "commands2.cmd")
gen_package(root, "commands2.sysid")
