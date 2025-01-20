#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: zoomeye.py
@Time: 2021/6/24 22:18
"""

import datetime
import json
import os
import platform
import re
import random
import sys

import requests
from rich.console import Console
from rich.live import Live

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
from kunyu.config.setting import UA, USER_INFO_API, MERGE_SEARCH_API, MERGE_SEARCH_API_ABROAD, ZOOMEYE_FIELDS_MERGE_SEARCH, DOMAIN_SEARCH_API, \
    HOST_SCAN_INFO, \
    ALIVE_SCAN_INFO
from kunyu.core.PupilMain import Pupil, ParaInit
from kunyu.core.createmap import create_data_map
from kunyu.utils.log import logger, logger_console
from kunyu.config.__version__ import __help__, init

console = Console(color_system="auto", record=True)
ZOOMEYE_KEY = conf.get("zoomeye", "apikey")
ZOOMEYE_TOKEN = conf.get("login", "token")
PLATFORM = platform.system()
params = {}


class ZoomeyeSearch(object):
    def __init__(self, method):
        self.fields = None
        self.auth = None
        self.search = None
        self.stype = None
        self.page = 1
        self.size = 10
        self.method = method
        self.headers = {
            "User-Agent": random.choice(UA),
            "Author": "ZoomEye Kunyu"
        }

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            nonlocal func
            req_list = []
            login_url = func(self, *args, **kwargs)
            params["sub_type"] = self.stype
            params["fields"] = str(self.fields)
            params['pagesize'] = self.size
            try:
                for num in range(int(self.page)):
                    params['qbase64'], params['page'] = self.search, (num + 1)
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
                data=json.dumps(data),
                headers=headers,
                timeout=time,
                verify=False
            )
        else:
            resp = requests.post(
                login_url,
                data=json.dumps(data),
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
@ZoomeyeSearch(method="POST")
def _dork_search(self, url, search, page, sub_type, size, fields):
    """"The logic layer of ZoomEye processes the requested data
        and feeds it back to the request layer to obtain the original data
    """
    try:
        if int(page) <= 0 or page is None:
            raise ArithmeticError
        self.page = page
        self.size = size
        self.search = search
        self.stype = sub_type.lower()
        self.fields = fields
        return url

    except ArithmeticError:
        return logger.warning("Please enter the correct number of queries!")
    except Exception:
        return logger.warning("Search for parameter exceptions!")


@ZoomeyeSearch(method="GET")
def _dork_search_domain(self, url):
    try:
        return url
    except Exception as e:
        logger.error(e)


@ZoomeyeSearch(method="POST")
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
    from kunyu.config.setting import ZOOMEYE_FIELDS_MERGE, ZOOMEYE_FIELDS_INFO, ZOOMEYE_FIELDS_DOMAIN
    from kunyu.utils.convert import convert
    ssl_data_params, raw_data_params, sensitive_params, scatter_params, scan_alive_params = {}, {}, [], [], []
    page, dtype, timeout, size, fields = 1, 0, 30, 10, "default"
    stype, btype = "v4", "host"
    thread, deep, all, fuzz, proxy = 10, 2, False, False, False

    # Global commands List
    help = """Global commands:
        info                                      Print User Info
        Search <Query>                            Comprehensive Information Search
        SearchIcon <File>/<URL>                   Query Based On Icon Image
        SearchBatch <File>                        Batch Query Assets In Files
        SearchCert <Domain>                       SSL Certificate Search
        SearchDomain <Domain>                     Domain Name Associated/Subdomain Search
        EncodeHash <Encryption> <Query>           Encryption Method Interface (Base64/HEX/MD5/mmh3)
        HostCrash <IP> <Domain>                   Host Header Scan Hidden Assets
        show <config>/<rule>                      Show Can Set Options Or Kunyu Config
        Seebug <Query>                            Search Seebug Vulnerability Information
        set <Option>                              Set Global Arguments Values
        view/views <ID>                           Look Over Banner Row Data Information
        Cscan <IP>/<Port>                         Scans Port Information About CobaltStrike
        PupilSearch <URL>/<ID>                    Example Query Sensitive Interfaces And Information
        CDNAnalysis <Domain>                      Identify Whether The Domain Name Is a CDN Asset
        Pocsuite3                                 Invoke The Pocsuite Component
        ExportPath                                Returns The Path Of The Output File
        CreateMap                                 Generate An IP Distribution Heat Map
        AliveScan                                 The Viability Of The Last Retrieval
        clear                                     Clear The Console Screen
        help                                      Print Help Info
        exit                                      Exit KunYu & """

    # ZoomEye Command List
    Command_Info = ["help", "info", "set", "Seebug", "Search", "SearchIcon", "HostCrash", "CDNAnalysis",
                    "SearchBatch", "SearchCert", "SearchDomain", "EncodeHash", "Pocsuite3", "ExportPath", "Cscan",
                    "show", "clear", "view", "DirectoryCrash", "AliveScan", "views", "PupilSearch", "CreateMap", "exit"]

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
        global total, result, FIELDS, table_fields
        result_type = "data"
        total, num = 0, 0
        export_list = []
        # Gets the API for the call
        FIELDS, fields_bool = self.ZOOMEYE_FIELDS_MERGE, ""
        if self.fields == "default":
            fields_bool = ",".join(ZOOMEYE_FIELDS_MERGE_SEARCH)
        else:
            fields_bool = self.fields
            FIELDS = fields_bool.split(',')
            FIELDS.insert(0, "ID")
        if types == "domain":
            result_type = "list"
            setting.API_URL, FIELDS = f"{DOMAIN_SEARCH_API}?q={search}&type={self.dtype}&page={self.page}", self.ZOOMEYE_FIELDS_DOMAIN
            dork_search_method = _dork_search_domain(setting.API_URL)
        else:
            dork_search_method = _dork_search(setting.API_URL, search, self.page, self.stype, self.size, fields_bool)
        table = DisposeTables().result_table(FIELDS)
        # Get data information
        for result in dork_search_method:
            try:
                total = result['total']
                for i in range(len(result[result_type])):
                    num += 1
                    title = ""
                    data = self.convert(result[result_type][i])
                    if setting.API_URL == MERGE_SEARCH_API or MERGE_SEARCH_API_ABROAD:
                        try:
                            if hasattr(data,"title"):
                                data["title"] = data.title[0] if data["title"] and data["title"] != [] else ""
                            if hasattr(data,"lat") and hasattr(data,"lon"):
                                # Set scatter_params info
                                self.scatter_params.append({
                                    "lng": str(data.lon), "lat": str(data.lat), "ip": data.ip
                                })
                            # Reset the <ssl raw Data Params> element
                            self.ssl_data_params[num] = data.ssl
                            # Reset the <raw Data Params> element
                            self.raw_data_params[num] = data.body
                            # Set the Latitude and longitude information
                            self.scan_alive_params.append({
                                "ip": data.ip,
                                "port": str(data.port)
                            })
                        except Exception:
                            pass
                        # 玄学bug之一，能跑就行哈哈哈。
                        try:
                            if hasattr(data, "update_time"):
                                data["update_time"] = data["update_time"].split("T")[0]
                        except Exception:
                            pass
                        if self.fields == "default":
                            # Set the output field
                            table_fields = [
                                str(num), data.ip, str(data.port), str(data.protocol),
                                str(data.service), str(data["isp.name"]), str(data["country.name"]),
                                str(data["city.name"]), str(data["title"]), str(data["update_time"])
                            ]
                        else:
                            table_fields = [str(num)]
                            for key in self.fields.split(','):
                                if key in data:
                                    table_fields.append(str(data[key]))
                        table.add_row(*table_fields)
                    elif types == "domain":
                        # Set the output field
                        table.add_row(
                            str(num), str(data.name), str(data.ip), str(data.timestamp)
                        )
                        # Set the exported fields
                        table_fields = [str(num), str(data.name), str(data.ip), str(data.timestamp)]
                    export_list.append(table_fields)
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
        from rich.pretty import pprint
        """ return user info"""
        info = cls.convert(_user_info()[0])
        # Calculate the total quota for the month
        search_subscription = int(info.data.subscription.points) + int(info.data.subscription.zoomeye_points)
        table = DisposeTables().result_table(cls.ZOOMEYE_FIELDS_INFO)
        end_date = None if info.data.subscription.end_date == "" else info.data.subscription.end_date
        console.log("User Information:", style="green")
        table.add_row(
            str(info.data.username), str(info.data.subscription.plan),
            str(search_subscription), str(end_date)
        )
        console.print(table)
        logger.info("User information retrieval is completed\n")

    @classmethod
    # ZoomEye host search method
    def command_search(cls, search):
        # Checks whether the fingerprint rule file exists
        if setting.RULE_PARMAS is not None:
            # Traverses to find whether the specified fingerprint rule number exists
            for item_dict in setting.RULE_PARMAS:
                if item_dict["KXID"] == search:
                    # Replace with the value in the specified fingerprint rule number
                    search = item_dict["kx_query"]
        return cls.__command_search(cls, encode.encode_base64(search))

    # @classmethod
    # # ZoomEye web search method
    # def command_searchweb(cls, search):
    #     return cls.__command_search(cls, search, types="web")

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
        # Use ZooEye batch query mode,Search: "ip=1.1.1.1 ip=2.2.2.2 ip=3.3.3.3"
        for ip in get_file(filename):
            search += "ip={} || ".format(ip)
        return cls.command_search(search.rstrip("||"))

    @classmethod
    # ZoomEye SSL Cert Search
    def command_searchcert(cls, hostname):
        """
            Associate assets by calculating the SSL serial number of the domain name
            :param hostname: Enter the domain name using the HTTPS protocol
        """
        cert_hex_encode = encode.cert_encode(hostname)
        if cert_hex_encode is not None:
            return cls.__command_search(cls, "ssl=" + str(cert_hex_encode))

    @classmethod
    # ZoomEye Icon Image Search
    def command_searchicon(cls, filename):
        """
            Calculate the hash through the icon icon to associate related assets
            According to the input parameters, judge and calculate the ico icon hash of the url or file path
            :param filename: Enter the specified URL or Icon file path
        """
        icon_hash = str(encode.encode_md5(filename))
        if icon_hash != "":
            logger.info("iconhash:" + icon_hash)
            return cls.command_search("iconhash=" + icon_hash)

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
            serials = 1 if serial == "" else serial
            raw_data = cls.raw_data_params.get(int(serials))
            # Check whether the returned result is None
            if raw_data is None:
                raise ArithmeticError
            # Check whether the returned result is ""
            elif raw_data == "":
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
            serials = 1 if serial == "" else serial
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
                raise ValueError
        except ArithmeticError:
            return logger.warning(
                "No retrieval operation is performed or the length of the dictionary key value is exceeded"
            )
        except KeyboardInterrupt:
            return logger.warning("PupilMain Terminate Operation!")
        except ValueError:
            return logger.warning("Please enter appropriate parameters!")
        except Exception as err:
            console.print(err)

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
            table = DisposeTables().result_table(HOST_SCAN_INFO)
            # Set output list content
            for res in result_list:
                table.add_row(
                    str(res[0]), str(res[1]), str(res[2])
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
        ip_port_params, num = cls.scan_alive_params, 0
        table = DisposeTables().result_table(ALIVE_SCAN_INFO)
        logger.info("IP Service Viability Scan:")
        try:
            # Polling output table content
            with Live(table, refresh_per_second=4):
                for data in ip_port_params:
                    num += 1
                    alive_status = cls.convert(Scan_Alive_Ip().scan_port_status(data["ip"], data["port"]))
                    table.add_row(
                        str(num), alive_status.ip, str(alive_status.port), str(alive_status.state)
                    )
        except Exception as e:
            return logger.error(e)
        logger.info("IP Service Viability Scan is completed\n")

    @classmethod
    def command_cscan(cls, args):
        try:
            # Check whether a parameter exists
            if args == "":
                raise ArithmeticError
            # Get args ip and search
            ip, _, port = args.strip().partition(" ")
            logger.info("Cscan Scan Results:")
            scan_result = Scan_Alive_Ip().scan_cobaltstrike_status(ip, port)
            console.print(scan_result)
            logger.info("Cobaltstrike Scan is completed\n")
        except ArithmeticError:
            return logger.warning("Please Input IP and Port")

    @classmethod
    def command_cdnanalysis(cls, args):
        exec_program = ""
        try:
            # Check whether a parameter exists
            if args == "":
                raise ArithmeticError
            if PLATFORM == "Darwin":
                exec_program = "darwin"
            elif PLATFORM == "Linux":
                exec_program = "linux"
            elif PLATFORM == "Windows":
                exec_program = "windows.exe"
            cdn_exec_program_path = str(
                os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + f"/lib/cdn/{exec_program}").replace(
                "\\", "/")
            logger.info("Domain CDN Analysis Results:")
            os.system(f'{cdn_exec_program_path} {args}')
            logger.info("CDN Analysis is completed\n")
        except ArithmeticError:
            return logger.warning("Please Enter The Domain Name You Want to Identify")
