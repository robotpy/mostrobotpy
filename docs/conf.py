# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "RobotPy API"
copyright = "2023, RobotPy Development Team"
author = "RobotPy Development Team"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "robotpy_sphinx.all",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autoclass_content = "both"


# -- Custom Document processing ----------------------------------------------

import os
from os.path import abspath, dirname
from robotpy_sphinx.regen import gen_package
from robotpy_sphinx.sidebar import generate_sidebar

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

# This is used for linking and such so we link to the thing we're building
rtd_version = os.environ.get("READTHEDOCS_VERSION", "latest")
if rtd_version not in ["stable", "latest"]:
    rtd_version = "stable"


generate_sidebar(
    globals(),
    "mostrobotpy",
    "https://raw.githubusercontent.com/robotpy/docs-sidebar/master/sidebar.toml",
)

root = abspath(dirname(__file__))

# WPILib
gen_package(root, "wpilib", exclude=["wpi_*"])
gen_package(root, "wpilib.simulation")
gen_package(root, "wpilib.sysid")

# NTCore
gen_package(root, "ntcore")
gen_package(root, "ntcore.meta")

# CSCore
gen_package(root, "cscore")
# Apriltag
gen_package(root, "robotpy_apriltag")

# WPIMath
gen_package(root, "wpimath")

# WPINet
gen_package(root, "wpinet")

# WPIUtil
gen_package(root, "wpiutil")
gen_package(root, "wpiutil.log")
gen_package(root, "wpiutil.sync")
gen_package(root, "wpiutil.wpistruct")

# HAL
gen_package(root, "hal", include=["Sim*"])
gen_package(root, "hal.simulation")

# ROMI
gen_package(root, "romi")

# XRP
gen_package(root, "xrp")
