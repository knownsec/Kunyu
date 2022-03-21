"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: ExportHandler.py
@Time: 2022/3/18 15:53
"""

import re

from rich.console import Console
from kunyu.utils.log import logger
from kunyu.lib.GlobalVariable import globalVariables as gbv

console = Console(color_system="auto", record=True)

class ExportHandler:
    def __int__(self) -> None:
        pass

    def handler_sensitiveinformation(self, data):
        """
            Clears empty key-value pairs in dictionary deduplication
        """
        for k in list(data.keys()):
            if not data[k]:
                del data[k]
        for k in data.keys():
            data[k] = list(set(data[k]))

    # Remove dirty data from matched ip
    # First match the internal network ip, and then filter the external network ip.
    # As long as there are two segments with more than 10 digits, it is considered to be an ip.
    def handler_ip(self):
        a_pattern = "10\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])"
        b_pattern = "172\.(1[6789]|2[0-9]|3[01])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])"
        c_pattern = "192\.168\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[0-9])"
        d_pattern = "127.0.0.1"
        pattern = re.compile("{}|{}|{}|{}".format(a_pattern, b_pattern, c_pattern, d_pattern))
        removeip = []
        for ip in gbv.Sensitiveinformation["Ip"]:
            # Non-intranet ip for processing
            if not re.search(pattern, ip):
                sign = 0
                for number in re.split("\.", ip):
                    # Remove ip1 like 008.054.012.095, 084.043.126.085
                    if (len(number)) > 0 and int(number[0]) == 0:
                        removeip.append(ip)
                        break
                    if int(number) > 10:
                        sign = sign + 1
                if sign < 2:
                    removeip.append(ip)
        removeip = list(set(removeip))
        for ip in removeip:
            gbv.Sensitiveinformation["Ip"].remove(ip)

    def main(self):

        self.handler_sensitiveinformation(gbv.Sensitiveinformation)
        try:
            self.handler_ip()
        except Exception:
            pass

        if gbv.apiresult:
            logger.warning("Retrieving results API:")
            console.print(list(set(gbv.apiresult)))
            print("")
        if gbv.urlresult:
            logger.warning("Retrieving results URL:")
            console.print((list(set(gbv.urlresult))))
            print("")
        if gbv.Sensitiveinformation:
            logger.warning("Retrieving results KeyWord:")
            console.print(gbv.Sensitiveinformation)
