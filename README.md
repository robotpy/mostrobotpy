mostrobotpy
===========

This repository contains core python libraries that wrap the C++ artifacts of
[allwpilib](https://github.com/wpilibsuite/allwpilib). These libraries are
officially supported for use in the FIRST Robotics Competition.

API Documentation
=================

API documentation is at https://robotpy.readthedocs.io/projects/robotpy/en/latest/

Building RobotPy
================

> [!WARNING]
> It is not recommended for users to build their own copy of RobotPy.
> Instead you should use our prebuilt packages that we publish on PyPI and
> on the WPILib artifactory site. See TODO for details

mostrobotpy consists of many interdependent python packages, which can be
found in the `subprojects` directory. Each subproject can be built like
any other python project, but it is recommended that you use our `rdev.sh`
tool instead.

The managed subprojects track `pyproject.in.toml` templates. The `develop` and
wheel-building commands generate each project's ignored `pyproject.toml` when
that project is reached. To generate all project files for use with other
Python tooling, run:

    ./rdev.sh update-pyproject

You must have a working C++ build system and python development headers
installed for your system.

Next install dependencies using pip:

    pip install -r rdev_requirements.txt
    pip install numpy

Then run these commands to build all the wheels for the current operating system.

    ./rdev.sh ci build-pure-wheels
    ./rdev.sh ci build-other-wheels
    ./rdev.sh ci build-meson-wheels

All the resulting wheels are in `dist`, which can be installed using `pip`.

To build wheels for the robot platform, see Cross Compilation below.

Development environment
-----------------------

To install all robotpy packages in [editable mode](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode)
first run this to install dependencies:

    ./rdev.sh install-prereqs

Then each time you want to build everything:

    ./rdev.sh develop

For pure python development, you can just edit the files in this repository in-place, and
changes will take effect immediately.

If you are changing C++/wrapper code, you will need to rebuild the package that you are
modifying. You can either run the develop command above (which rebuilds everything) or
rebuild an individual package:

    ./rdev.sh develop NAME

For cross-checkout ccache reuse with GCC/Clang, opt in with
`./rdev.sh develop --portable-build-paths NAME` or `RDEV_PORTABLE_BUILD_PATHS=1`.
This sets `CCACHE_BASEDIR` and appends a `CXXFLAGS` prefix map for build subprocesses;
`CCACHE_DIR` is unchanged. Use matching toolchains, dependencies, and directory
layouts. Existing Meson builds may need their `build/` directory recreated.
Debug and `__FILE__` paths become relative. Disabled by default on all platforms;
`--no-portable-build-paths` overrides the environment variable.

It can be a slow process, see the [semiwrap documentation](https://semiwrap.readthedocs.io/en/stable/tips.html)
for tips to make it more efficient.

Cross Compilation
-----------------

Build SystemCore wheels using the same Docker image and build steps as CI:

    ./rdev.sh cross-build --output wheels

Docker must be running, and the host Python needs `rdev_requirements.txt`.
The current image is `wpilib/systemcore-cross-debian:2026-trixie-py315`.
Use `--buildtype=debug` to request a debug Meson build.

The command copies tracked and non-ignored untracked sources, including local
edits, into an isolated workspace. Build directories, caches, and the local
`build-actions` checkout are excluded. Existing desktop build artifacts are
unaffected. Relative output paths are relative to this repository, as with other
`rdev.sh` commands.
The repository's `wheels/` directory is ignored by Git; an absolute output path
can also be used.

Native, pure-Python, and wrapper wheels are copied to the output directory only
after a successful build. Matching filenames are replaced; other files are left
alone. Cross-compiled tests are not run, matching CI.

Compiler, pip, and artifact downloads persist in the Docker volume
`rdev-systemcore-cache`. The cross files use ccache, whose statistics are printed
at the end of the build. Wheels are exported with the invoking user's ownership.
The container requires network access to install tools and download dependencies.

CI and local builds share `devtools/cross/setup.sh` and `build.sh`. The setup and
cross files originate from `robotpy/build-actions/setup-cross-meson@v2027`;
update them together when changing toolchains.
