#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: crash.py
@Time: 2021/9/2 17:54
'''
import re
import json
import random
import sys

import grequests
import requests

from kunyu.core import conf
from rich.console import Console
from kunyu.utils.log import logger
from kunyu.utils.convert import convert
from kunyu.lib.batchfile import get_domain_file, get_file
from kunyu.config.setting import UA, DOMAIN_SEARCH_API, DOMAIN_CHECK_REGEX, IP_ADDRESS_REGEX

console = Console(color_system="auto", record=True)
ZOOMEYE_KEY = conf.get("zoomeye", "apikey")
ZOOMEYE_TOKEN = conf.get("login", "token")
SERVERLESS_API = conf.get("Serverapi", "serverless")


class HostScan:
    def __init__(self):
        self.headers = {
            "User-Agent": random.choice(UA)
        }
        self.params = {"type": 1}
        self.IP_STATUS = 0
        self.__get_login()

    # Check whether the HTTP request returns an error
    def __check_error(self, resp):
        if resp.get("error"):
            raise requests.HTTPError(resp.get("message"))

    # Dynamically obtain user credentials according to the initialized configuration file
    def __get_login(self):
        if ZOOMEYE_KEY == "None":
            self.headers["Authorization"] = "JWT %s" % ZOOMEYE_TOKEN
        else:
            self.headers["API-KEY"] = ZOOMEYE_KEY

    # Get ZoomEye Doamin List
    def __get_zoomeye_domain(self):
        """
            Return to the result set of the reverse search through the zoomeye domain name library
            First get the number of result sets in the first HTTP request
            Perform calculations based on the number of result sets to dynamically obtain all results
        """
        domain_list = []
        try:
            def request_get():
                resp = requests.get(
                    DOMAIN_SEARCH_API,
                    data=self.params,
                    headers=self.headers,
                    verify=False
                )
                self.__check_error(json.loads(resp.text))
                return resp.json()

            result = request_get()
            # Dynamically calculate the number of pages that need to be queried to obtain all result sets
            count = int(result["total"] / 30)
            page = count if (result["total"] % 30) == 0 else count + 1
            # Get ZoomEye Domain result
            for i in range(page):
                self.params["page"] = str(i + 1)
                result = request_get()
                for num in range(len(result["list"])):
                    data = convert(result["list"][num])
                    domain_list.append(data.name)
            # Remove duplicate domain names
            domain_list = list(set(domain_list))
            console.log("Host Header Scan Domain Total: ", len(domain_list), style="green")
            return domain_list

        except requests.HTTPError as err:
            logger.error(err)

    def __is_valid_domain(self, search):
        """
            Return whether or not given value is a valid domain.
            If the value is valid domain name this function returns ``True``, otherwise False
            :param search: domain string to validate
        """
        pattern = re.compile(DOMAIN_CHECK_REGEX)
        return True if pattern.match(search) else False

    def __is_valid_ip(self, ip):
        """
            Return whether or not given value is a valid ip address.
            If the value is valid ip address this function returns ``True``, otherwise False
            :param ip: ip string to validate
        """
        pattern = re.compile(IP_ADDRESS_REGEX)
        return True if pattern.match(ip) else False

    def _get_file(self, search):
        """
            Get the array of domain names required for HOST collision
            If it is the main domain name, check it through the zoomeye interface
            Otherwise, read the result through the file path
            :param search: Enter the main domain name or domain name file path
        """
        domain_list = []
        # Check the logic of obtaining the domain name result
        if self.__is_valid_domain(search):
            domain_list = self.__get_zoomeye_domain()
        else:
            for domain in get_domain_file(search):
                domain_list.append(str(domain))
            # Return to the domain name combing in the file
            console.log("Host Header Scan Domain Total: ", len(domain_list), style="green")
        return domain_list

    def _get_ip_file(self, ip):
        """
            Get the array of ip address required for HOST collision
            If it is IP, directly HOST collision
            Otherwise, read the file to obtain the IP address
            :param ip: Enter the main ip address or ip address file path
        """
        ip_list = []
        if self.__is_valid_ip(ip):
            ip_list.append(ip)
        else:
            for ip_address in get_file(ip):
                ip_list.append(ip_address)
        return ip_list

    def host_scan(self, search, ip):
        """
            Obtain hidden assets through HOST collision
            :param search: Ways to obtain domain names
            :param ip: IP address to be collided
        """
        resp, crash_list = [], []
        tmp_list = []
        status = False
        if SERVERLESS_API != "None": status = True
        # http and https protocol collision
        protocol = ['http://{}/', 'https://{}/']
        self.params["q"] = search
        domain_list = self._get_file(search)
        url = self._get_ip_file(ip)
        for server in protocol:
            for ip_address in url:
                urls = server.format(ip_address)
                resp_url = SERVERLESS_API if status else urls
                for domain in domain_list:
                    headers = {
                        'User-Agent': random.choice(UA),
                        'ip': urls,
                    }
                    # The cloud function sets header hosts
                    if status:headers["hosts"] = domain.strip()
                    else:headers["host"] = domain.strip()
                    # Concurrent requests through the encapsulated coroutine module
                    resp.append(grequests.get(
                        resp_url, headers=headers, timeout=5, verify=False)
                    )

        res_list = grequests.map(resp)
        for res in res_list:
            try:
                # Determine the HTTP status code that needs to be obtained
                if res.status_code == 200 or res.status_code == 302 or res.status_code == 301:
                    if res.text != "false":
                        res.encoding = 'gbk2312'
                        # Get the title of the returned result
                        title = re.findall('<title>(.+)</title>', res.text)
                        tmp_list = [res.request.headers['ip'], title[0]]
                        if status:
                            tmp_list.append(res.request.headers['hosts'])
                            # Unicode decoding of the information returned by cloud functions
                            tmp_list[1] = title[0].encode('utf8').decode('unicode_escape')
                        else:tmp_list.append(res.request.headers['host'])
                        crash_list.append(tmp_list)
            except Exception:
                continue

        return crash_list

