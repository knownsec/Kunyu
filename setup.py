#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: setup.py
@Time: 2021/7/24
'''


import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

    def find_packages(where='.'):
        # os.walk -> list[(dirname, list[subdirs], list[files])]
        return [folder.replace("/", ".").lstrip(".")
                for (folder, _, fils) in os.walk(where)
                if "__init__.py" in fils]

from kunyu.config.__version__ import __version__


DEPENDENCIES = open('requirements.txt', 'r', encoding='utf-8').read().split('\n')
README = open('README.md', 'r', encoding='utf-8').read()

setup(
    name='kunyu',
    version=__version__,
    description='kunyu is Cyberspace Resources Surveying and Mapping auxiliary tools',
    long_description=README,
    long_description_content_type='text/markdown',
    author='风起 <onlyzaliks@gmail.com>',
    url='',
    packages=find_packages(),
    include_package_data=True,
    entry_points={'console_scripts': ['kunyu=kunyu.console:main']},
    install_requires=DEPENDENCIES,
    keywords=['Cyberspace Resources', 'zoomeye', 'kunyu'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
