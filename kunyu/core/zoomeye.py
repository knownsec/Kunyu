#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: zoomeye.py
@Time: 2021/6/24 22:18
'''

import json
import random
import sys
import re

import requests
from rich.table import Table
from rich.console import Console

from kunyu.core import conf
from kunyu.config.setting import UA
import kunyu.lib.encode as encode
from kunyu.lib.export import export_xls
from kunyu.lib.batchfile import get_file
from kunyu.core.seebug import Seebug
from kunyu.utils.log import logger, logger_console
from kunyu.config.__version__ import __help__, init


console = Console(color_system="auto", record=True)

# ZoomEye API
USER_INFO_API = "https://api.zoomeye.org/resources-info"
HOST_SEARCH_API = "https://api.zoomeye.org/host/search"
WEB_SEARCH_API = "https://api.zoomeye.org/web/search"
BOTH_SEARCH_API = "https://api.zoomeye.org/both/search"
DOMAIN_SEARCH_API = "https://api.zoomeye.org/domain/search"

ZOOMEYE_KEY = conf.get("zoomeye", "apikey")
ZOOMEYE_TOKEN = conf.get("login", "token")

params = {}


class ZoomeyeSearch(object):
    def __init__(self, method):
        self.auth = None
        self.search = None
        self.page = 1
        self.method = method
        self.headers = {
            "User-Agent": random.choice(UA)
        }

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            nonlocal func
            req_list = []
            login_url = func(self, *args, **kwargs)
            try:
                for num in range(int(self.page)):
                    params['query'], params['page'] = self.search, (num + 1)
                    req_list.append(self.__request(login_url, data=params, headers=self.headers))
            except requests.HTTPError as err:
                logger.warning(err)
            except requests.exceptions.ConnectionError:
                logger.error("Network timeout")
            return req_list

        return wrapper

    def __request(self, login_url, data=None, headers=None):
        self.__get_login()
        """"As the request layer,
            the processed data is received and returned to the original data,
            which is displayed on the terminal after processing by the presentation layer.
        """
        # The API is not available for tourist users
        if self.method == "GET":
            resp = requests.get(
                login_url,
                data=data,
                headers=headers,
                timeout=5
            )
        else:
            resp = requests.post(
                login_url,
                data=data,
                headers=headers,
                timeout=5
            )
        self.check_status(resp)
        self.check_error(resp.json())
        # return query data
        return json.loads(resp.text)

    # Check return http status code
    def check_status(self, resp):
        # check http status code 500 or 503
        if resp.status_code in [500, 503]:
            raise requests.HTTPError("ZoomEye Server Error, Status: {}".format(resp.status_code))
        elif resp.status_code in [401]:
            logger.error("The token has expired, please re-initialize")
            print(__help__.format(datil=init))
            sys.exit(0)

    # Check return error info
    def check_error(self, resp):
        if resp.get("error"):
            raise requests.HTTPError(resp.get("message"))

    def __get_login(self):
        """"Obtain the user login credentials and use them dynamically.
            It is recommended to use the API-KEY method to log in,
            because the user name/password requires an additional HTTP request,
            so in theory the API-KEY method is more efficient.
        """
        if ZOOMEYE_KEY == "None":
            self.headers["Authorization"] = "JWT %s" % ZOOMEYE_TOKEN
        else:
            self.headers["API-KEY"] = ZOOMEYE_KEY


# After the SDK public,The interface to get the data.
@ZoomeyeSearch(method="GET")
def _dork_search(self, url, search, page):
    """"The logic layer of ZoomEye processes the requested data
        and feeds it back to the request layer to obtain the original data
    """
    try:
        if int(page) <= 0 or page is None:
            raise ArithmeticError
        self.page = page
        self.search = search
        return url

    except ArithmeticError:
        return logger.warning("Please enter the correct number of queries!")
    except Exception:
        return logger.warning("Search for parameter exceptions!")


@ZoomeyeSearch(method="GET")
# Get ZoomEye User Info
def _user_info(self):
    return USER_INFO_API


# The Display class of the tool
class ZoomEye:
    from kunyu.config.setting import ZOOMEYE_FIELDS_HOST, ZOOMEYE_FIELDS_WEB, ZOOMEYE_FIELDS_INFO, ZOOMEYE_FIELDS_DOMAIN
    from kunyu.utils.convert import convert
    page = 1
    dtype = 0
    btype = "host"
    
    help = """Global commands:
        info                                      Print User info
        SearchHost <query>                        Basic Host search
        SearchWeb <query>                         Basic Web search
        SearchIcon <File>/<URL>                   Icon Image search
        SearchBatch <File>                        Batch search Host
        SearchCert <Domain>                       SSL certificate Search
        SearchDomain <Domain>                     Domain name associated/subdomain search
        Seebug <Query>                            Search Seebug vulnerability information
        set <Option>                              Set arguments values
        ExportPath                                Returns the path of the output file 
        clear                                     Clear the console screen
        show                                      Show can set options
        help                                      Print Help info
        exit                                      Exit KunYu & """

    # ZoomEye Command List
    Command_Info = ["help", "info", "set", "Seebug", "SearchWeb", "SearchHost", "SearchIcon", "SearchBatch", "SearchCert", "SearchDomain", "ExportPath", "show", "clear", "exit"]

    def __init__(self):
        self.fields_tables = None

    def __command_search(self, search, types="host"):
        """"The raw data obtained is processed and finally displayed on the terminal,
            which is also one of the most core codes
        """
        table = Table(show_header=True, style="bold")
        global total, api_url, result, FIELDS, export_host
        total, num = 0, 0
        result_type = "matches"
        export_list = []

        # Gets the API for the call
        api_url, FIELDS = HOST_SEARCH_API, self.ZOOMEYE_FIELDS_HOST
        if types == "web":
            api_url, FIELDS = WEB_SEARCH_API, self.ZOOMEYE_FIELDS_WEB
        elif types == "domain":
            result_type = "list"
            params['q'], params['type'] = search, self.dtype
            api_url, FIELDS = DOMAIN_SEARCH_API, self.ZOOMEYE_FIELDS_DOMAIN

        try:
            for cloumn in FIELDS:
                table.add_column(cloumn, justify="center", overflow="ignore")
        except Exception:
            return logger.warning("Please enter the correct field")

        # Get data information
        for result in _dork_search(api_url, search, self.page):
            try:
                total = result['total']
                webapp_name, server_name, db_name, system_os, language = "", "", "", "", ""
                for i in range(len(result[result_type])):
                    num += 1
                    title,lat,lon = "", "", ""
                    data = self.convert(result[result_type][i])
                    if api_url == HOST_SEARCH_API:
                        if data.portinfo.title:
                            title = data.portinfo.title[0]
                        if data.geoinfo.location:
                            lat = data.geoinfo.location.lat
                            lon = data.geoinfo.location.lon
                        # Set the output field
                        table.add_row(str(num), data.ip, str(data.portinfo.port), str(data.portinfo.service),
                                      str(data.portinfo.app), str(data.geoinfo.isp), str(data.geoinfo.country.names.en),
                                      str(data.geoinfo.city.names.en),str(title), str(lat),str(lon))

                        # Set the exported fields
                        export_host = [str(num), data.ip, str(data.portinfo.port), str(data.portinfo.service),
                                      str(data.portinfo.app), str(data.geoinfo.isp), str(data.geoinfo.country.names.en),
                                      str(data.geoinfo.city.names.en),str(title), str(lat),str(lon)]

                    elif api_url == WEB_SEARCH_API:
                        # Because of the problem of returning the default value of the field
                        if data.webapp:
                            webapp = self.convert(data.webapp[0])
                            webapp_name = webapp.name
                        if data.server:
                            server = self.convert(data.server[0])
                            server_name = server.name
                        if data.db:
                            db = self.convert(data.db[0])
                            db_name = db.name
                        if data.language:
                            language = data.language[0]
                        if data.system:
                            system = self.convert(data.system[0])
                            system_os = system.name

                        # Set the output field
                        table.add_row(str(num), data.ip[0], str(data.site), str(data.title),
                                      str(system_os), str(webapp_name), str(db_name),
                                      str(language), str(server_name))

                        # Set the exported fields
                        export_host = [str(num), data.ip[0], str(data.site), str(data.title),
                                       str(system_os), str(webapp_name), str(db_name),
                                       str(language), str(server_name)]

                    elif types == "domain":
                        # Set the output field
                        table.add_row(str(num), str(data.name), str(data.ip), str(data.timestamp))

                        # Set the exported fields
                        export_host = [str(num), str(data.name), str(data.ip), str(data.timestamp)]
                    export_list.append(export_host)

                if export_list:
                    export_xls(export_list, FIELDS)
            except Exception:
                continue

        if total > 0:
            console.log("search result amount:", total, style="green")
            console.print(table)
            logger.info("Search information retrieval is completed\n")
        else:
            logger.error("The query result is empty\n")
        return console

    @classmethod
    def command_info(cls, *args):
        """" return user info"""
        table = Table(show_header=True, style="bold")
        info = cls.convert(_user_info()[0])
        for column in cls.ZOOMEYE_FIELDS_INFO:
            table.add_column(column, justify="center", overflow="ignore")

        console.log("User Information:", style="green")
        table.add_row(str(info.plan), str(info.resources.search), str(info.resources.stats),
                      str(info.resources.interval))
        console.print(table)
        logger.info("User information retrieval is completed\n")

    @classmethod
    def command_searchhost(cls, search):
        return cls.__command_search(cls, search)

    @classmethod
    def command_searchweb(cls, search):
        return cls.__command_search(cls, search, types="web")

    @classmethod
    # domain name associated / subdomain Search
    def command_searchdomain(cls, search):
        return cls.__command_search(cls, search, types="domain")

    @classmethod
    # ZoomEye batch search IP method
    def command_searchbatch(cls, filename):
        search = ""
        # Use ZooEye batch query mode,Search: "ip:1.1.1.1 ip:2.2.2.2 ip:3.3.3.3"
        for ip in get_file(filename):
            search += "ip:{} ".format(ip)
        if cls.btype == "host":
            return cls.command_searchhost(search)

        return cls.command_searchweb(search)

    @classmethod
    # ZoomEye SSL Cert Search
    def command_searchcert(cls, hostname):
        if encode.cert_encode(hostname) is not None:
            return cls.__command_search(cls, "ssl:" + str(encode.cert_encode(hostname)))

    @classmethod
    # ZoomEye Icon Image Search
    def command_searchicon(cls, filename):
        icon_hash = str(encode.encode_mmh3(filename))
        if icon_hash != "":
            logger.info("iconhash:"+icon_hash)
            return cls.command_searchhost("iconhash:" + icon_hash)

    @classmethod
    # Get SeeBug vulnerability information
    def command_seebug(cls, search):
        total = Seebug.search(search).get("total")
        data = Seebug.search(search)
        logger.info("Number of relevant vulnerabilities: {}".format(total))
        for vuln in data["results"]:
            vuln = cls.convert(vuln)
            logger_console.info('[{}] - [{}]'.format(vuln.name, vuln.id))

        logger.info("Seebug Search retrieval is completed\n")



