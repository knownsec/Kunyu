#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: console.py
@Time: 2021/7/21 17:19
'''

import os
import sys

module_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(1, module_path)

from kunyu.config.__version__ import __help__, init
from kunyu.core.console import KunyuInterpreter
from kunyu.utils.log import logger_console
from kunyu.core import conf


def main():
    try:
        if str(conf.get("zoomeye", "apikey")) == "None" and str(conf.get("login", "token")) == "None":
            raise Exception

        # Call the main class
        KunyuInterpreter().main()
    except Exception:
        logger_console.info(__help__.format(datil=init))


if __name__ == "__main__":
    main()
