#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name="robotpy-commands-v2",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="RobotPy Development Team",
    author_email="robotpy@googlegroups.com",
    description="WPILib command framework v2",
    url="https://github.com/robotpy/robotpy-commands-v2",
    packages=["commands2"],
    install_requires=[
        "wpilib<2025,>=2024.2.1.2",
        "typing_extensions>=4.1.0,<5",
    ],
    license="BSD-3-Clause",
    python_requires=">=3.8",
    include_package_data=True,
)
