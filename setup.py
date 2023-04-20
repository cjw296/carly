# See license.txt for license details.
# Copyright (c) 2018 onwards, Chris Withers

import os

from setuptools import setup, find_packages

base_dir = os.path.dirname(__file__)

setup(
    name='carly',
    version='0.13.0',
    author='Chris Withers',
    author_email='chris@withers.org',
    license='MIT',
    description=(
        "A tool for putting messages into and collecting responses from "
        "Twisted servers using real networking"
    ),
    long_description=open('README.rst').read(),
    url='https://github.com/cjw296/carly',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.6.7",
    install_requires=[
        'Twisted >= 21.7',
        'attrs',
    ],
    extras_require=dict(
        test=[
            'autobahn',
            'coverage',
            'testfixtures>6.3',
        ],
        build=['twine', 'wheel']
    ),
)
