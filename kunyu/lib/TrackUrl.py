"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: TrackUrl.py
@Time: 2022/3/18 15:53
"""

import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from urllib import parse
from rich.console import Console
from requests_html import HTMLSession
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from kunyu.utils.log import logger
from kunyu.config.setting import UA
import kunyu.lib.SerachData as SerachData
import kunyu.lib.ExportHandler as ExportHandler
from kunyu.lib.GlobalVariable import globalVariables as gbv

requests.packages.urllib3.disable_warnings()
console = Console(color_system="auto", record=True)

class Track:
    def __init__(self):

        self.headers = {
            'User-Agent': random.choice(UA),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Upgrade-Insecure-Requests': '1'
        }
        self.proxy = gbv.proxy

        if self.proxy:
            console.print(self.proxy)
            scheme = parse.urlparse(gbv.proxy).scheme
            self.proxy={
                scheme:self.proxy
            }
        self.requests = HTMLSession(verify=False)

    # requestsRequest method
    def req(self, url):
        try:
            response = self.requests.get(
                url, headers=self.headers, proxies=self.proxy,timeout=5
            )
            # Record the successfully queried url into the history table,
            # output the results on the one hand, and prevent repeated queries on the other hand
            gbv.trackhistory.append(url)
            content=SerachData.DataHandler(url, response).main()
            console.print('URL:{}   STATUS:{}'.format(url, response.status_code))
            return response
        except Exception as e:
            gbv.trackhistory.append(url)
            return False

    # Backtrack according to backtracking rules
    def track_search(self):
        # Traverse the tarck list for backtracking, dynamically add urls in the middle,
        # gbv.track list is of the form [[layer 0],[layer 1 traceback],[layer 2]]

        for deepurl in gbv.track:
            # Although the maximum traceability depth has not been reached, new data cannot be traced
            if not deepurl:
                logger.warning("Fixed at depth {} and no new data can be found".format(gbv.trackdeep - 1))
                return False
            # Determine whether the backtracking depth reaches the maximum backtracking depth
            if gbv.trackdeep > gbv.deep:
                return False
            # You can continue to trace if it is not there.
            gbv.trackdeep = gbv.trackdeep + 1
            gbv.track.append([])
            # It needs to be rendered for the first time to prevent some pages from being formed by js and not loaded.
            # This is especially common in webpack
            # Because this rendering is an asynchronous operation, it is not easy to use threads, so it is a bit redundant to extract it separately.
            if gbv.trackdeep == 1:
                url = deepurl[0]
                response = self.requests.get(
                    url=url, headers=self.headers, proxies=self.proxy, verify=False, timeout=5
                )
                #response = self.requests.get(url=url, headers=self.headers, verify=False,timeout=5)
                # Rendering incurable diseases, if it doesn't work, it will not be rendered.
                try:
                    response.html.render(timeout=5)
                except Exception:
                    pass
                gbv.trackhistory.append(url)
                SerachData.DataHandler(url, response).main()

            # Multithreading
            else:
                with ThreadPoolExecutor(max_workers=gbv.thread) as thread:
                    for url in deepurl:
                        # Avoid duplicate queries
                        if url in gbv.trackhistory:
                            continue
                        thread.submit(self.req, url)

    def main(self):
        self.track_search()
        ExportHandler.ExportHandler().main()
