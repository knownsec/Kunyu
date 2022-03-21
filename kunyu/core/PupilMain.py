"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: PupilMain.py
@Time: 2022/3/18 15:53
"""

import re
import time

from rich.console import Console

from kunyu.lib import TrackUrl
from kunyu.utils.log import logger
import kunyu.lib.SerachData as SerachData
from kunyu.lib.GlobalVariable import globalVariables as gbv

console = Console(color_system="auto", record=True)

class ParaInit:
    def __init__(self, url, thread, trackdeep, mode, fuzz):
        # There should be some / not less, for example,
        # the target domain name is aaa.com/sso/, and it cannot be lazy as aaa.com/sso
        self.url = url
        gbv.url=url
        gbv.thread = thread
        gbv.apiresult = []
        gbv.track = []  # add dynamically
        # 0 means to search only for the current url without backtracking other urls,
        # 1 means backtracking the url of the result obtained from the current url,
        # 2 means to continue
        self.trackdeep = trackdeep
        gbv.urlresult = []
        # Whether to traverse all URLs found. Choose carefully, it's a bit long
        gbv.searchany = mode
        # Whether to add the interface to the backtracking queue
        gbv.fuzz = fuzz
        gbv.trackhistory = []  # Record already processed urls to prevent repeated queries
        gbv.Sensitiveinformation = {"Jwt": [], "Ip": [], "Email": [], "ChinaIdCard": [], "AccessKey": [],
                                    "SecretKey": [], "AppId": [], "UserName": [], "PassWord": [],
                                    "SSHKey": [], "RSAKey": [], "GithubAccessKey": []}
        # Backtracking depth
        gbv.trackdeep = 0  # current depth
        gbv.deep = trackdeep  # allow depth
        gbv.track.append([])
        gbv.track[0].append(url)

    def url_handler(self):
        # Fill in the url, the url cannot be www.aaa.com, it needs to be www.aaa.com/,
        # because the data of the first and last / will be deleted later for js concatenation.
        # If it is not added, the host will be removed.
        pattern = re.compile('/')
        if len(re.findall(pattern, self.url[:])) == 2:
            self.url = self.url + "/"

    def main(self):
        self.url_handler()
        return self.url, self.trackdeep


class Pupil:
    def __init__(self) -> None:
        console.log("PupilSearch KeyWord Start:", style="green")

    def main(self, proxy):
        start_time = time.time()
        gbv.proxy = proxy
        TrackUrl.Track().main()
        logger.info("PupilSearch Total time:{}".format(time.time() - start_time))

    def response_main(self, raw_data):
        start_time = time.time()
        SerachData.DataHandler("http://www.kunyu.com/", raw_data).main()
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
        logger.info("PupilSearch Total time:{}".format(time.time() - start_time))
