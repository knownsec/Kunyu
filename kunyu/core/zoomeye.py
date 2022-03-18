#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: zoomeye.py
@Time: 2021/6/24 22:18
"""

import os
import sys
import json
import random
import datetime

import requests
import platform
from rich.live import Live
from rich.console import Console

try:
    import pocsuite3
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), os.path.pardir)))
from pocsuite3 import set_paths
from pocsuite3.cli import check_environment, module_path
from pocsuite3.lib.core.interpreter import PocsuiteInterpreter
from pocsuite3.lib.core.option import init_options

from kunyu.core import conf
from kunyu.config import setting
import kunyu.lib.encode as encode
from kunyu.core.seebug import Seebug
from kunyu.core.crash import HostScan
from kunyu.lib.export import export_xls
from kunyu.lib.batchfile import get_file
from kunyu.utils.tables import DisposeTables
from kunyu.core.scanalive import Scan_Alive_Ip
from kunyu.config.setting import UA, USER_INFO_API, HOST_SEARCH_API, WEB_SEARCH_API, DOMAIN_SEARCH_API, HOST_SCAN_INFO, \
    SEMSITIVE_INFO, RULE_PARMAS, ALIVE_SCAN_INFO
from kunyu.core.PupilMain import Pupil, ParaInit
from kunyu.core.createmap import create_data_map
from kunyu.utils.log import logger, logger_console
from kunyu.config.__version__ import __help__, init

console = Console(color_system="auto", record=True)
overflow = "fold" if platform.system() == "Darwin" else "ignore"

ZOOMEYE_KEY = conf.get("zoomeye", "apikey")
ZOOMEYE_TOKEN = conf.get("login", "token")

params = {}


class ZoomeyeSearch(object):
    def __init__(self, method):
        self.auth = None
        self.search = None
        self.stype = None
        self.page = 1
        self.method = method
        self.headers = {
            "User-Agent": random.choice(UA),
            "author": "ZoomEye KunYu"
        }

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            nonlocal func
            req_list = []
            login_url = func(self, *args, **kwargs)
            params["sub_type"] = self.stype
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
        time = int(GlobalVar.get_timeout_resp())
        # The API is not available for tourist users
        if self.method == "GET":
            resp = requests.get(
                login_url,
                data=data,
                headers=headers,
                timeout=time,
                verify=False
            )
        else:
            resp = requests.post(
                login_url,
                data=data,
                headers=headers,
                timeout=time,
                verify=False
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
def _dork_search(self, url, search, page, sub_type):
    """"The logic layer of ZoomEye processes the requested data
        and feeds it back to the request layer to obtain the original data
    """
    try:
        if int(page) <= 0 or page is None:
            raise ArithmeticError
        self.page = page
        self.search = search
        self.stype = sub_type.lower()
        return url

    except ArithmeticError:
        return logger.warning("Please enter the correct number of queries!")
    except Exception:
        return logger.warning("Search for parameter exceptions!")


@ZoomeyeSearch(method="GET")
# Get ZoomEye User Info
def _user_info(self):
    return USER_INFO_API


# Set Global variate
class GlobalVar:
    timeout_resp = 30

    def set_timeout_resp(timeout_resp):
        GlobalVar.timeout_resp = timeout_resp

    def get_timeout_resp(*args):
        return GlobalVar.timeout_resp


# The Display class of the tool
class ZoomEye:
    from kunyu.config.setting import ZOOMEYE_FIELDS_HOST, ZOOMEYE_FIELDS_WEB, ZOOMEYE_FIELDS_INFO, ZOOMEYE_FIELDS_DOMAIN
    from kunyu.utils.convert import convert
    ssl_data_params, raw_data_params, sensitive_params, scatter_params, scan_alive_params = {}, {}, [], [], []
    page, dtype, timeout = 1, 0, 30
    stype, btype = "v4", "host"
    thread, deep, all, fuzz, proxy = 10, 2, False, False, False

    # Global commands List
    help = """Global commands:
        info                                      Print User info
        SearchHost <query>                        Basic Host search
        SearchWeb <query>                         Basic Web search
        SearchIcon <File>/<URL>                   Icon Image search
        SearchBatch <File>                        Batch search Host
        SearchCert <Domain>                       SSL certificate Search
        SearchDomain <Domain>                     Domain name associated/subdomain search
        EncodeHash <encryption> <query>           Encryption method interface (base64/hex/md5/mmh3)
        HostCrash <IP> <Domain>                   Host Header Scan hidden assets
        show <config>/<rule>                      Show can set options or Kunyu config
        Seebug <query>                            Search Seebug vulnerability information
        set <option>                              Set Global arguments values
        view/views <ID>                           Look over banner row data information
        PupilSearch <URL>/<ID>                    Example Query sensitive interfaces and information
        Pocsuite3                                 Invoke the pocsuite component
        ExportPath                                Returns the path of the output file
        CreateMap                                 Generate an IP distribution heat map
        AliveScan                                 The viability of the last retrieval
        clear                                     Clear the console screen
        help                                      Print Help info
        exit                                      Exit KunYu & """

    # ZoomEye Command List
    Command_Info = ["help", "info", "set", "Seebug", "SearchWeb", "SearchHost", "SearchIcon", "HostCrash",
                    "SearchBatch", "SearchCert", "SearchDomain", "EncodeHash", "Pocsuite3", "ExportPath",
                    "show", "clear", "view", "DirectoryCrash", "AliveScan","views", "PupilSearch", "CreateMap", "exit"]

    def __init__(self):
        self.fields_tables = None

    def __params_clear(self):
        # Resetting array contents
        self.raw_data_params.clear()
        self.ssl_data_params.clear()
        self.sensitive_params.clear()
        self.scatter_params.clear()
        self.scan_alive_params.clear()

    def __command_search(self, search, types="host"):
        """"The raw data obtained is processed and finally displayed on the terminal,
            which is also one of the most core codes
            :param search: zoomeye grammar search statement
            :param types: Dynamically set according to the interface used
        """
        self.__params_clear(self)
        GlobalVar.set_timeout_resp(self.timeout)
        global total, api_url, result, FIELDS, export_host
        result_type = "matches"
        total, num = 0, 0
        export_list = []

        # Gets the API for the call
        api_url, FIELDS = HOST_SEARCH_API, self.ZOOMEYE_FIELDS_HOST
        if types == "web":
            api_url, FIELDS = WEB_SEARCH_API, self.ZOOMEYE_FIELDS_WEB
        elif types == "domain":
            result_type = "list"
            params['q'], params['type'] = search, self.dtype
            api_url, FIELDS = DOMAIN_SEARCH_API, self.ZOOMEYE_FIELDS_DOMAIN

        table = DisposeTables().result_table(FIELDS, overflow)
        # Get data information
        for result in _dork_search(api_url, search, self.page, self.stype):
            try:
                total = result['total']
                webapp_name, server_name, db_name, system_os, language = "", "", "", "", ""
                for i in range(len(result[result_type])):
                    num += 1
                    title, data_isp = "", ""
                    data = self.convert(result[result_type][i])
                    if api_url == HOST_SEARCH_API:
                        if data.portinfo.title:
                            title = data.portinfo.title[0]

                        try:
                            data_isp = data.geoinfo.isp
                            # Reset the <raw Data Params> element
                            self.raw_data_params[num] = data.portinfo.banner
                            # Reset the <ssl raw Data Params> element
                            self.ssl_data_params[num] = data.ssl
                        except:
                            pass

                        # Set the Latitude and longitude information
                        if data.geoinfo.location:
                            lat = data.geoinfo.location.lat
                            lon = data.geoinfo.location.lon

                        # Set the output field
                        table.add_row(str(num), data.ip, str(data.portinfo.port), str(data.portinfo.service),
                                      str(data.portinfo.app), str(data_isp), str(data.geoinfo.country.names.en),
                                      str(data.geoinfo.city.names.en), str(title), str(data.timestamp).split("T")[0])

                        # Set the exported fields
                        export_host = [str(num), data.ip, str(data.portinfo.port), str(data.portinfo.service),
                                       str(data.portinfo.app), str(data_isp), str(data.geoinfo.country.names.en),
                                       str(data.geoinfo.city.names.en), str(title), str(data.timestamp).split("T")[0]]

                        # Set scatter_params info
                        self.scatter_params.append({
                            "lng": str(lon), "lat": str(lat), "ip": data.ip
                        })

                        self.scan_alive_params.append({
                                "ip":data.ip,
                                "port":str(data.portinfo.port)
                        })

                    elif api_url == WEB_SEARCH_API:
                        # Because of the problem of returning the default value of the field
                        if data.webapp:
                            webapp_name = self.convert(data.webapp[0]).name
                        if data.server:
                            server_name = self.convert(data.server[0]).name
                        if data.db:
                            db_name = self.convert(data.db[0]).name
                        if data.language:
                            language = data.language[0]
                        if data.system:
                            system_os = self.convert(data.system[0]).name

                        # Set the output field
                        table.add_row(
                            str(num), data.ip[0], str(data.site), str(data.title),
                            str(system_os), str(webapp_name), str(db_name),
                            str(language), str(server_name), str(data.timestamp).split("T")[0]
                        )

                        # Set the exported fields
                        export_host = [str(num), data.ip[0], str(data.site), str(data.title),
                                       str(system_os), str(webapp_name), str(db_name),
                                       str(language), str(server_name), str(data.timestamp).split("T")[0]]

                        try:
                            # Reset the <raw Data Params> element
                            self.raw_data_params[num] = data.raw_data
                            self.ssl_data_params[num] = data.ssl
                        except:
                            pass

                    elif types == "domain":
                        # Set the output field
                        table.add_row(
                            str(num), str(data.name), str(data.ip), str(data.timestamp)
                        )
                        # Set the exported fields
                        export_host = [str(num), str(data.name), str(data.ip), str(data.timestamp)]
                    export_list.append(export_host)

                if export_list:
                    export_xls(export_list, FIELDS)
            except Exception as err:
                logger.error(err)
                continue

        # Check if the result set is empty
        if total > 0:
            console.log("search result amount:", total, style="green")
            console.print(table)
            logger.info("Search information retrieval is completed\n")
        else:
            logger.error("The query result is empty\n")
        # console.print(self.raw_data_params)
        return console

    @classmethod
    def command_info(cls, *args):
        """ return user info"""
        info = cls.convert(_user_info()[0])
        # Calculate the total quota for the month
        search_quota = int(info.quota_info.remain_free_quota) + int(info.quota_info.remain_pay_quota)
        table = DisposeTables().result_table(cls.ZOOMEYE_FIELDS_INFO, overflow)
        info.user_info.expired_at = None if info.user_info.expired_at == "" else info.user_info.expired_at
        console.log("User Information:", style="green")
        table.add_row(
            str(info.user_info.name), str(info.user_info.role),
            str(search_quota), str(info.user_info.expired_at)
        )
        console.print(table)
        logger.info("User information retrieval is completed\n")

    @classmethod
    # ZoomEye host search method
    def command_searchhost(cls, search):
        # Checks whether the fingerprint rule file exists
        if setting.RULE_PARMAS is not None:
            # Traverses to find whether the specified fingerprint rule number exists
            for item_dict in setting.RULE_PARMAS:
                if item_dict["KXID"] == search:
                    # Replace with the value in the specified fingerprint rule number
                    search = item_dict["kx_query"]
        return cls.__command_search(cls, search)

    @classmethod
    # ZoomEye web search method
    def command_searchweb(cls, search):
        return cls.__command_search(cls, search, types="web")

    @classmethod
    # domain name associated / subdomain Search
    def command_searchdomain(cls, search):
        return cls.__command_search(cls, search, types="domain")

    @classmethod
    # ZoomEye batch search IP method
    def command_searchbatch(cls, filename):
        """
            Batch query related result sets by reading the IP address in the file
            File name only supports txt type
            :param filename: Accept the IP file path as a parameter
        """
        search = ""
        # Use ZooEye batch query mode,Search: "ip:1.1.1.1 ip:2.2.2.2 ip:3.3.3.3"
        for ip in get_file(filename):
            search += "ip:{} ".format(ip)
        # Determine the type of interface used
        if cls.btype == "host":
            return cls.command_searchhost(search)

        return cls.command_searchweb(search)

    @classmethod
    # ZoomEye SSL Cert Search
    def command_searchcert(cls, hostname):
        """
            Associate assets by calculating the SSL serial number of the domain name
            :param hostname: Enter the domain name using the HTTPS protocol
        """
        cert_hex_encode = encode.cert_encode(hostname)
        if cert_hex_encode is not None:
            return cls.__command_search(cls, "ssl:" + str(cert_hex_encode))

    @classmethod
    # ZoomEye Icon Image Search
    def command_searchicon(cls, filename):
        """
            Calculate the hash through the icon icon to associate related assets
            According to the input parameters, judge and calculate the ico icon hash of the url or file path
            :param filename: Enter the specified URL or Icon file path
        """
        icon_hash = str(encode.encode_mmh3(filename))
        if icon_hash != "":
            logger.info("iconhash:" + icon_hash)
            return cls.command_searchhost("iconhash:" + icon_hash)

    @classmethod
    # Encode hex/md5/mmh3/base64 Hash
    def command_encodehash(cls, args):
        """
            Characters can be encrypted by this command
            Encryption parameters according to the specified encryption method
            :param args: Obtain the encryption method and the parameters that need to be encrypted
        """
        try:
            command, _, args = args.strip().partition(" ")
            # Check whether a parameter exists
            if args == "":
                raise ArithmeticError
            command_handler = getattr(encode, "encode_{}".format(command))
            # Return the encrypted result
            logger.info("{} : {}".format(
                command,
                command_handler(args.strip())
            ))

        except ArithmeticError:
            return logger.warning("Please specify the encryption mode")

        except Exception as err:
            return logger.warning(err)

    @classmethod
    # Get SeeBug vulnerability information
    def command_seebug(cls, search):
        """
            Get the historical vulnerabilities of the specified framework
            You can use this command to query the historical vulnerabilities of related frameworks
            :param search: Used to obtain parameters for querying related framework vulnerabilities
        """
        # Get Number of result sets of vulnerabilities
        total = Seebug.search(search).get("total")
        logger.info("Number of relevant vulnerabilities: {}".format(total))
        # Get vulnerabilities result
        for vuln in Seebug.search(search)["results"]:
            vuln = cls.convert(vuln)
            # Print Result set of framework history vulnerabilities
            logger_console.info('[{}] - [{}]'.format(vuln.name, vuln.id))

        logger.info("Seebug Search retrieval is completed\n")

    @classmethod
    # Invoke the pocsuite component
    def command_pocsuite3(cls, *args, **kwargs):
        check_environment()
        set_paths(module_path())
        init_options()
        # Set the directory to store the poc
        poc = PocsuiteInterpreter(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/pocs")
        poc.start()

    @classmethod
    # look over row_data info
    def command_view(cls, serial):
        """
            View raw data information
            You can view any raw data by entering the serial number
            :param serial: Please enter serial number ID
        """
        try:
            # If the key parameter is not specified, the key parameter is automatically set to 1
            serials = 1 if serial is "" else serial
            raw_data = cls.raw_data_params.get(int(serials))
            # Check whether the returned result is None
            if raw_data is None:
                raise ArithmeticError
            # Check whether the returned result is ""
            elif raw_data is "":
                logger.warning("Banner information is empty")
            else:
                console.log("Banner Information is:\n", style="green")
                console.print(raw_data)

        except ArithmeticError:
            return logger.warning(
                "No retrieval operation is performed or the length of the dictionary key value is exceeded"
            )

        finally:
            print()

    @classmethod
    # look over ssl row_data info
    def command_views(cls, serial):
        """
            View ssl raw data information
            You can views any ssl raw data by entering the serial number
            :param serial: Please enter serial number ID
        """
        try:
            # If the key parameter is not specified, the key parameter is automatically set to 1
            serials = 1 if serial is "" else serial
            ssl_raw_data = cls.ssl_data_params.get(int(serials))
            # Check whether the returned result is None
            if ssl_raw_data is None:
                raise ArithmeticError
            else:
                console.log("SSL Banner Information is:\n", style="green")
                console.print(ssl_raw_data)
        except ArithmeticError:
            return logger.warning("SSL Banner information is empty")

        finally:
            print()

    @classmethod
    def command_pupilsearch(cls, url):
        """
            Sensitive Data Retrieval
            You can retrieve sensitive information leaks by entering a URL or ID
            :param url: Please enter URL or ID
        """
        import re
        from kunyu.config.setting import HTTP_CHECK_REGEX, NUMBER_CHECK_REGEX
        try:
            ParaInit(url, int(cls.thread), int(cls.deep), cls.all, cls.fuzz).main()
            # Check if parameter is URL
            if re.search(HTTP_CHECK_REGEX, url):
                Pupil().main(cls.proxy)
            # Check if parameter is Number
            elif re.search(NUMBER_CHECK_REGEX, url):
                # Get the banner information of the surveying and mapping data by ID
                raw_data = cls.raw_data_params.get(int(url))
                if raw_data is None:
                    raise ArithmeticError
                Pupil().response_main(raw_data)
            else:
                raise Exception
        except ArithmeticError:
            return logger.warning(
                "No retrieval operation is performed or the length of the dictionary key value is exceeded"
            )
        except Exception as err:
            print(err)
            return logger.warning("Please enter appropriate parameters!")

    @classmethod
    def command_createmap(cls, *args, **kwargs):
        """
            Create a network space asset distribution map
            You can use the CreateMap command to generate a resource distribution map after a search
        """
        # Check whether Scatter Params is empty
        if len(cls.scatter_params) == 0: return logger.warning("Asset List is Empty,Please search and try again")
        from kunyu.config import setting
        # Generating an export path
        path = os.path.join(setting.OUTPUT_PATH,
                            datetime.datetime.now().strftime("ScatterGram_%H%M%S.html"))
        create_data_map(cls.scatter_params, path)
        # Output Export path
        logger.info(path)

    @classmethod
    def command_hostcrash(cls, args):
        """
            HOST Header Crash function,Obtaining hidden Assets
            You can use the master domain name reverse lookup or file to obtain the domain name list
            :param args: The IP address and domain name to be queried
        """
        try:
            # Check whether a parameter exists
            if args == "":
                raise ArithmeticError
            # Get args ip and search
            ip, _, search = args.strip().partition(" ")
            result_list = HostScan().host_scan(search, ip)
            # Determines whether the result set is empty
            if not result_list:
                return logger.warning("The query result is empty\n")
            table = DisposeTables().result_table(HOST_SCAN_INFO, overflow)
            # Set output list content
            for res in result_list:
                table.add_row(
                    str(res[0]), str(res[1]),str(res[2])
                )
            # Output table list to console
            console.print(table)
            logger.info("Host Header Scan is completed\n")
            # Export HOSTS collision results
            export_xls(result_list, HOST_SCAN_INFO)
            # End of function execution
        except ArithmeticError:
            return logger.warning("Please Host IP and Domain")

    @classmethod
    def command_alivescan(cls, *args, **kwargs):
        """
        Verify the current viability of the last retrieval result
        """
        from kunyu.utils.convert import convert
        ip_port_params, num = cls.scan_alive_params, 0
        table = DisposeTables().result_table(ALIVE_SCAN_INFO ,overflow)
        logger.info("IP Service Viability Scan:")
        # Polling output table content
        with Live(table, refresh_per_second=4):
            for data in ip_port_params:
                try:
                    num += 1
                    alive_status = convert(Scan_Alive_Ip().scan_port_status(data["ip"], data["port"]))
                    table.add_row(
                        str(num), alive_status.ip, str(alive_status.port), str(alive_status.state)
                    )
                except Exception:
                    continue
        logger.info("IP Service Viability Scan is completed\n")

