#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: seebug.py
@Time: 2021/7/20 16:42
'''
import json
from urllib.parse import urlencode

import requests

from kunyu.core import conf
from kunyu.utils.log import logger


SEARCH_API = "https://www.seebug.org/api/get_open_vuls_by_component"
SEARCH_VUL_API = "https://www.seebug.org/api/get_vul_detail_by_id"

SEEBUG_KEY = conf


class Seebug:
    """Obtain component related historical vulnerabilities
       through the Seebug interface
    """
    headers = {
        "Content-Type": "application/json"
    }

    def __init__(self):
        self.__get_login()
        self.param = {}

    # Get Seebug user login
    def __get_login(self):
        if SEEBUG_KEY is not None:
            self.headers["Authorization"] = "Token {}".format(SEEBUG_KEY)

    @classmethod
    def search(cls, search):
        try:
            cls.param = {
                "app_name": search
            }
            login_url = "%s?%s" % (SEARCH_API, urlencode(cls.param))
            resp = requests.get(
                login_url,
                headers=cls.headers
            )
            return json.loads(resp.text)

        except Exception:
            return logger.error("Failed to get SeeBug vulnerability information")










