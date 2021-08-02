#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: __init__.py
@Time: 2021/6/21 16:26
'''


import os
import sys
import json
import argparse

import requests
import configparser

from kunyu.utils import *
from kunyu.config.__version__ import usage, init, __title__, __help__

parser = argparse.ArgumentParser(prog=__title__)

# console pattern subcommand
subparsers = parser.add_subparsers()
parser_group_console = subparsers.add_parser('console', help='Enter Console Mode',
                                             description=__help__.format(datil=usage),
                                             formatter_class=argparse.RawDescriptionHelpFormatter,
                                             usage=argparse.SUPPRESS, add_help=True)

# Initial Configuration
parser_init_console = subparsers.add_parser('init', help='Enter console mode',
                                            description=__help__.format(datil=init),
                                            formatter_class=argparse.RawDescriptionHelpFormatter,
                                            usage=argparse.SUPPRESS, add_help=True)

parser_init_console.add_argument("--apikey", help='ZoomEye API Key')
parser_init_console.add_argument("--username", help='ZoomEye Username')
parser_init_console.add_argument("--password", help='ZoomEye Password')
parser_init_console.add_argument("--seebug", help='ZoomEye Password')

args = parser.parse_args()

# Gets the absolute path of the project
path = os.path.expanduser("~/")
conf = configparser.ConfigParser()

__path = os.path.join(path, ".kunyu.ini")

# Read config.user.ini
conf.read(__path)

def initial_config():
    if not conf.has_section("zoomeye") and not conf.has_section("login"):
        conf.add_section('zoomeye')
        conf.set("zoomeye", "apikey", "None")
        conf.add_section('login')
        conf.set("login", "token", "None")

    if not conf.has_section("seebug"):
        conf.add_section('seebug')
        conf.set("seebug", "apikey", "None")

def _get_login():
    param = '{{"username": "{}", "password": "{}"}}'.format(args.username, args.password)
    resp = requests.post(
        "https://api.zoomeye.org/user/login",
        data=param,
        timeout=5
    )
    resp = json.loads(resp.text)
    try:
        if resp["error"]:
            raise requests.HTTPError(resp.get("message"))
    except:
        pass
    conf.set("login", "token", resp["access_token"])


try:
    initial_config()
    if args.apikey:
        conf.set("zoomeye", "apikey", args.apikey)

    elif args.username and args.password:
        _get_login()

    if args.seebug:
        conf.set("seebug", "apikey", args.seebug)

except requests.HTTPError as err:
    print("\033[31;1m{}\033[0m".format(err))
    print(__help__.format(datil=init))
    sys.exit(0)

except Exception:
    pass

with open(__path, "w+") as f:
    conf.write(f)





