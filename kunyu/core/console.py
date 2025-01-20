#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: console.py
@Time: 2021/7/19 22:35
'''

import os
import sys
import platform
import subprocess
from pathlib import Path

from colorama import init
from rich.console import Console

from kunyu.config import setting
from kunyu.lib.ipLookUpHelper import get_ip_location
from kunyu.utils.log import logger
from kunyu.core.rule import YamlRule
from kunyu.lib.export import createdir
from kunyu.core.zoomeye import ZoomEye
from kunyu.utils.tables import DisposeTables
from kunyu.utils import readineng as readline
from kunyu.config.__version__ import __introduction__
from kunyu.config.setting import COMMAND_INFO, OS_SYSTEM, RULE_FILE_PATH, RULE_INFO

init(autoreset=True)
PLATFORM = platform.system()

# Determine the operating system clear screen command
cmd = "cls" if PLATFORM == "Windows" else "clear"
console = Console(color_system="auto", record=True)


def readline_available():
    """
    Check if the readline is available. By default
    it is not in Python default installation on Windows
    """
    return readline._readline is not None


# TAB auto completion
def auto_completion(completion=None, console=None):
    if not readline_available():
        return
    readline.set_completer_delims(" ")
    readline.set_completer(console)
    readline.parse_and_bind('bind ^I rl_complete') if PLATFORM == "Darwin" else readline.parse_and_bind("tab: complete")

class CommandCompleter:
    module = "ZoomEye"
    command, line = None, None
    command_func_params = ["setter", "getter", "clear", "exit", "help", "set", "exportpath"]

    def __init__(self) -> None:
        self.module = CommandCompleter.module
        self.line = CommandCompleter.line

    def command_setter(self, line) -> bool:
        """"
        :line set options
        """
        args, _, number = line.strip().partition("=")
        args, number = args.strip(), number.strip()
        if hasattr(eval(self.module), args):
            setattr(eval(self.module), args, number)
        return True

    def command_getter(self, line):
        """"
        :return options value
        """
        return getattr(eval(self.module), line)

    def show_rule(*args, **kwargs) -> bool:
        tables = DisposeTables().result_table(RULE_INFO)
        # Display fingerprint file information
        for res in setting.RULE_PARMAS:
            tables.add_row(
                str(res["KXID"]), str(res["author"]), str(res["kx_name"]), str(res["description"]),
                str(res["kx_query"]), str(res["createDate"]), str(res["source"])
            )
        console.log("Finger Rule Info:", style="green")
        console.print(tables)
        return True

    @staticmethod
    def show_config(**kwargs) -> bool:
        # Display configuration file information
        config_file_path = os.path.expanduser('~/') + ".kunyu.ini"
        with open(config_file_path) as file:
            logger.info(file.read())
        return True

    def show(self):
        tables = DisposeTables().result_table(COMMAND_INFO)
        command_info = [
            ["page", self.command_getter("page"), "Set Search Page"],
            ["size", self.command_getter("size"), "Set Search Quantity Per Page"],
            ["fields", self.command_getter("fields"), "Set the response field information"],
            ["dtype", self.command_getter("dtype"), "Set Associated/Subdomain Search Schema"],
            ["stype", self.command_getter("stype"), "Set Data Type IPV4/IPV6 (Option V4/V6)"],
            ["btype", self.command_getter("btype"), "Set BatchFile Search Schema"],
            ["timeout", self.command_getter("timeout"), "Set HTTP Requests Timeout"],
            ["thread", self.command_getter("thread"), "Set PupilSearch Thread Number"],
            ["deep", self.command_getter("deep"), "Set PupilSearch Search Deep"],
            ["all", self.command_getter("all"), "PupilSearch Add All Url To Check List"],
            ["fuzz", self.command_getter("fuzz"), "PupilSearch Add Api To Check List"],
            ["proxy", self.command_getter("proxy"), "PupilSearch HTTP Proxy"]
        ]
        for info in command_info:
            tables.add_row(
                str(info[0]), str(info[1]), str(info[2])
            )
        console.log("Global Command Info:", style="green")
        console.print(tables)

    def command_clear(*args, **kwargs):
        subprocess.call(cmd, shell=True)

    def command_exit(*args, **kwargs):
        raise KeyboardInterrupt

    def command_help(self):
        console.print(eval(self.module).help)

    def command_set(self):
        return CommandCompleter.command_setter(self, CommandCompleter.line)

    def command_exportpath(*args, **kwargs):
        logger.info(setting.OUTPUT_PATH)


class BaseInterpreter(object):
    global_help = ""
    OUTPUT_PATH = None

    def __init__(self):
        self.module = CommandCompleter.module
        self.complet = eval(self.module).Command_Info
        self.setup()
        # Create output directory
        createdir()
        # Import rule file param
        if Path(setting.RULE_FILE_PATH).exists():
            setting.RULE_PARMAS = YamlRule().get_yaml_list()

        setting.API_URL = setting.MERGE_SEARCH_API if get_ip_location() else setting.MERGE_SEARCH_API_ABROAD

    def setup(self):
        """ Initialization of third-party libraries
        Setting appropriate completer function.
        """
        auto_completion(completion=4, console=self.complete)

    def parse_line(self, line):
        command, _, args = line.strip().partition(" ")
        return command, args.strip()

    @property
    def prompt(self):
        """ Returns prompt string """
        os.system("")
        return "Kunyu (\033[31;1m{moudle}\033[0m) > ".format(moudle=self.module)

    def get_command_handler(self, command):
        """ Parsing command and returning appropriate handler.
        :param command: command
        :return: command_handler
        """
        try:
            command_handler = getattr(eval(self.module), "command_{}".format(command))

        except AttributeError:
            logger.error("Unknown command: '{}'".format(command))
            return False

        return command_handler

    def complete(self, text, state):
        """Return the next possible completion for 'text'.
        If a command has not been entered, then complete against command list.
        Otherwise try to call complete_<command> to get list of completions.
        """
        if state == 0:
            start_index = readline.get_begidx()
            if start_index != 0:
                complete_function = self.default_completer
            else:
                complete_function = self.raw_command_completer

            self.completion_matches = complete_function(text)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def raw_command_completer(self, text):
        """ Complete command w/o any argument """
        return [command for command in self.complet if command.lower().startswith(text.lower())]

    def default_completer(self, *ignored):
        return []

    def auxiliary(self, command, line=None):
        """"Set how to handle basic commands
        :return True/False
        """
        CommandCompleter.line = line
        # show Global Command Info
        if command == "show":
            if line in ["rule", "config"]:
                return eval("CommandCompleter.{}_{}()".format(command, line))
            CommandCompleter().show()
            return True

        elif command in CommandCompleter.command_func_params:
            eval("CommandCompleter.command_{}(self)".format(command))
            return True

        elif command in OS_SYSTEM:
            command_os = "{} {}".format(command, line)
            os.system(command_os)
            return True

        return False

    def start(self):
        # logger_console(self.global_help)
        while True:
            self.setup()
            try:
                command, args = self.parse_line(input(self.prompt))
                command = command.lower()
                if self.auxiliary(command, args) or not command:
                    continue
                command_handler = self.get_command_handler(command)
                try:
                    command_handler(args)
                except KeyboardInterrupt:
                    print("")

            except KeyboardInterrupt:
                logger.info("kunyu Console mode stopped")
                try:
                    os.rmdir(setting.OUTPUT_PATH)
                except OSError:
                    pass
                sys.exit(0)

            except Exception as err:
                console.print(err)
                continue


class KunyuInterpreter(BaseInterpreter):

    def __init__(self):
        super().__init__()
        self.global_help = __introduction__.format(datil=eval(self.module).help)
        console.print(self.global_help)

    def main(self):
        super().start()
