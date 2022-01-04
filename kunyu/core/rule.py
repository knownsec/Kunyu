#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: rule.py
@Time: 2021/12/28 17:56
"""
import os
import yaml

from rich.table import Table
from rich.console import Console

from kunyu.core import conf
from kunyu.config.setting import RULE_INFO

console = Console(color_system="auto", record=True)
RULE_FILE_PATH = conf.get("rule", "path")

class YamlRule:
    def _all_path(self, dirname):
        result = []
        # Returns the paths to all files in the specified directory
        for maindir, subdir, file_name_list in os.walk(dirname):
            for filename in file_name_list:
                result.append(os.path.join(maindir, filename))  # Merge into a full path
        return result

    def _get_yaml_file(self, filename):
        # Read the information in the yaml file
        with open(filename, encoding="utf-8") as file:
            file_data = file.read()
        # Convert yaml file content to dictionary type
        return yaml.load(file_data, Loader=yaml.FullLoader)

    def get_yaml_list(self):
        yaml_params = []
        for file in self._all_path(RULE_FILE_PATH):
            yaml_params.append(self._get_yaml_file(file))
        return yaml_params