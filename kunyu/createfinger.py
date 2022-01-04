#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: only.py
@Time: 2021/12/28 16:14
'''
import os

import yaml
from rich.console import Console

from kunyu.utils.log import logger

console = Console(color_system="auto", record=True)

logger.info("Generate fingerprint rule files:")

try:
    input_kxid = input("\033[32;32m请输入KXID信息:\033[0m")
    input_author = input("\033[32;32m请输入作者名称:\033[0m")
    input_kx_name = input("\033[32;32m请输入指纹名称:\033[0m")
    input_description = input("\033[32;32m请输入指纹简介:\033[0m")
    input_kx_query = input("\033[32;32m请输入指纹信息:\033[0m")
    input_createdate = input("\033[32;32m请输入指纹创建时间:\033[0m")
    input_source = input("\033[32;32m请输入指纹来源:\033[0m")

    query = '''{finger}'''.format(finger=input_kx_query)

    file_data = {
        "KXID": input_kxid,
        "author": input_author,
        "kx_name": input_kx_name,
        "description": input_description,
        "kx_query": query,
        "createDate": input_createdate,
        "source": input_source
    }
    logger.info("The content of the fingerprint rule file is as follows:")
    # Convert to YAML data
    data = yaml.dump(file_data, allow_unicode=True)
    # print yaml file data information
    console.print(f"{data}")

    # Gets the absolute path to the build file
    file_path = f"{os.path.abspath(os.path.dirname(os.path.dirname(__file__)))}/rule/{input_kxid}.yaml"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(data)

    logger.info("A fingerprint rule file has been generated:" + file_path)
except:
    print("")
    logger.warning("Exit!")

