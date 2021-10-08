#!/usr/bin/env python3

from setuptools import setup

setup(
    name="tstl",
    version="1.0.1",
    py_modules=["tstl"],
    entry_points="""
        [console_scripts]
        tstl=tstl:main
    """,
)
