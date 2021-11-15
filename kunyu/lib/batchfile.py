#!/usr/bin/env python
# -*- coding: utf-8 -*-
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: batchfile.py
@Time: 2021/6/16 21:05
'''

import sys
import re

from functools import wraps

from kunyu.config.setting import IP_ADDRESS_REGEX, DOMAIN_CHECK_REGEX
from kunyu.utils.log import logger


def getresult(func):


    @wraps(func)
    def getfile(file):
        """
            Read the content in the txt file that meets the requirements of the processing layer
            Determine whether it is a txt file
            :param file: The path of the file to be read
        """
        __ip_list = []
        try:
            # Check File Type
            if file.endswith(".txt"):
                logger.info("File load successful")
            else:
                logger.warning("Only input TXT type files are allowed")
                raise Exception

            with open(file, "r", encoding='utf-8') as ip_text:
                for line in ip_text:
                    __ip_list.append(line.strip())
            return filter(func, __ip_list)
        except Exception:
            # ([LRE])Hidden garbled code appearing before the file path can also cause an error.
            # Copy from right to left will lead to appear [LRE] tabs,Whereas not.
            return logger.error("please check the file name is correct")

    return getfile


@getresult
def __check_file_ip(ip):
    # Check IP legitimacy
    return True if re.search(IP_ADDRESS_REGEX, ip) else logger.warning(ip + ":It's an illegal IP address")


@getresult
def __check_file_domain(domain):
    # Check DOMAIN legitimacy
    return True if re.search(DOMAIN_CHECK_REGEX, domain) else logger.warning(domain + ":It's an illegal Domain")


# Get the contents of the Domain list.
def get_domain_file(*args, **kwargs):
    _ip_list = []
    try:
        for i in __check_file_domain(*args, **kwargs):
            _ip_list.append(i)
        return _ip_list

    except KeyboardInterrupt:
        return
    except Exception:
        logger.error("Failed to get IP list content! Please check if the IP file name is abnormal")


# Get the contents of the IP list.
def get_file(*args, **kwargs):
    _ip_list = []
    try:
        for i in __check_file_ip(*args, **kwargs):
            _ip_list.append(i)
        return _ip_list

    except KeyboardInterrupt:
        return
    except Exception:
        logger.error("Failed to get IP list content! Please check if the IP file name is abnormal")
