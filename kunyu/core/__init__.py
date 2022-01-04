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

import grequests
import requests
import configparser

from kunyu.utils import *
from kunyu.config import setting
from kunyu.config.__version__ import usage, init, __title__, __help__

parser = argparse.ArgumentParser(prog=__title__)

# console pattern subcommand
subparsers = parser.add_subparsers()
parser_group_console = subparsers.add_parser('console', help='Enter Console Mode',
                                             description=__help__.format(datil=usage),
                                             formatter_class=argparse.RawDescriptionHelpFormatter,
                                             usage=argparse.SUPPRESS, add_help=True)

# Initial Configuration
parser_init_console = subparsers.add_parser('init', help='Enter init information',
                                            description=__help__.format(datil=init),
                                            formatter_class=argparse.RawDescriptionHelpFormatter,
                                            usage=argparse.SUPPRESS, add_help=True)


parser_init_console.add_argument("--seebug", help='Seebug API Key')
parser_init_console.add_argument("--apikey", help='ZoomEye API Key')
parser_init_console.add_argument("--username", help='ZoomEye Username')
parser_init_console.add_argument("--password", help='ZoomEye Password')
parser_init_console.add_argument("--rule", help='Set Rule File Path')
parser_init_console.add_argument("--output", help='Set Output File Path')
parser_init_console.add_argument("--serverless", help='Set Serverless API')

args = parser.parse_args()

# Gets the absolute path of the project
path = os.path.expanduser("~/")
conf = configparser.ConfigParser()

__path = os.path.join(path, ".kunyu.ini")

# Read config.user.ini
conf.read(__path)

def initial_config():
    """
        Determine whether the parameters in the configuration file exist
        If it does not exist, create a parameter and set the initial value to None
    """
    if not conf.has_section("zoomeye") and not conf.has_section("login"):
        conf.add_section('zoomeye')
        conf.set("zoomeye", "apikey", "None")
        conf.add_section('login')
        conf.set("login", "token", "None")

    if not conf.has_section("seebug"):
        conf.add_section('seebug')
        conf.set("seebug", "apikey", "None")

    # The path of the output file
    if not conf.has_section("path"):
        conf.add_section("path")
        conf.set("path", "output", setting.OUTPUT_PATH)

    # Set Serverless API Address Config
    if not conf.has_section("Serverapi"):
        conf.add_section("Serverapi")
        conf.set("Serverapi", "serverless", "None")

    if not conf.has_section("rule"):
        conf.add_section("rule")
        conf.set("rule", "path", setting.RULE_FILE_PATH)

# Verify the login status of the ZoomEye account
def _get_login():
    param = '{{"username": "{}", "password": "{}"}}'.format(args.username, args.password)
    resp = requests.post(
        "https://api.zoomeye.org/user/login",
        data=param,
        timeout=15
    )
    resp = json.loads(resp.text)
    try:
        if resp["error"]:
            raise requests.HTTPError(resp.get("message"))
    except:
        pass
    conf.set("login", "token", resp["access_token"])


try:
    # Initialize the configuration file
    initial_config()
    if args.apikey:
        conf.set("zoomeye", "apikey", args.apikey)

    elif args.username and args.password:
        _get_login()

    if args.seebug:
        conf.set("seebug", "apikey", args.seebug)

    # set output file path
    if args.output:
        conf.set("path", "output", args.output)

    # Used for CrashHost function
    if args.serverless:
        conf.set("Serverapi", "serverless", args.serverless)

    # Used for rule directory path
    if args.rule:
        conf.set("rule", "path", args.rule)

except requests.HTTPError as err:
    print("\033[31;1m{}\033[0m".format(err))
    print(__help__.format(datil=init))
    sys.exit(0)

except Exception:
    pass

with open(__path, "w+") as f:
    conf.write(f)





