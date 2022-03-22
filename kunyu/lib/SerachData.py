"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: SerachData.py
@Time: 2022/3/18 15:53
"""

import os
import re
import threading
from urllib import parse

from bs4 import BeautifulSoup

from kunyu.lib.GlobalVariable import globalVariables as gbv

class DataHandler:

    def __init__(self, url, response):

        # Determine if rendering is required
        # response.html.render(5)
        response_parameter = str(response) if url == "http://www.kunyu.com/" else response.html.html
        self.soup = BeautifulSoup(response_parameter, "lxml")
        # Get the url path,
        # ① and the result of search_js are spliced into a complete url for backtracking
        # ② Compare with the result of search_url, and keep the url of the current domain name for backtracking.
        self.baseurl = url
        self.url = re.split(re.compile('/'), url[::-1], 1)[1][::-1] + "/"
        self.response = response_parameter

    # find data function
    def search_data(self, pattern,flag=0):
        tmplist = []
        # Iterate over the string of all tags, while removing blank lines.
        result = re.finditer(pattern, self.response)
        # Some modules require iterators, some don't, depending on this flag to determine the return data type
        if flag:
            return result
        for match in result:
            tmplist.append(match.group())
        # go back
        return set(tmplist)

    # Check if the current url may be the url of webpack, try to get the map
    def webpack_map(self, url):
        # Suspected to be js packaged by webpack, try to get map
        pattern = re.compile("sourceMappingURL=.+.map$")
        map_param = self.search_data(pattern)
        if map_param:
            sourceMappingURL = (re.compile("=").split(list(map_param)[0])[1])
            gbv.track[gbv.trackdeep].append(self.url + sourceMappingURL)
        elif url not in gbv.trackhistory:
            webpackjs = ["main", "vend", "app", "chunk"]
            for i in webpackjs:
                if i in url:
                    # The address of the map may be src.35edfdbe.map or src.35edfdbe.js.map
                    gbv.track[gbv.trackdeep].append(url + ".map")

    # html naturally has script tags, but js files do not exist, so only js in html can be extracted
    # js of other files will be detected by searchurl
    def search_js(self):
        scheme = parse.urlparse(self.url).scheme
        host = parse.urlparse(self.url).netloc
        if host== "":
            host= parse.urlparse(self.baseurl).netloc

        # Set the filter of find_all to filter js tags but no innerhtml script (no innerhtml means remote scritp)
        def is_script_but_no_innerhtml(tag):
            return tag.string is None and tag.name == "script" and tag.has_attr("src")

        self.webpack_map(self.baseurl)
        # Get the js that needs to be accessed again, in list form
        # Among them, if it is in the form of http, the probability is an external link, and no traceback
        """
            js is divided into the following three types, which need to be filled in a targeted manner
            ../../js/xxx.js fill protocol + domain name + path ^(\.\.|\.)
            //aaaaa.com/js/xxx.js padding protocol ^(//)
            /js/xxx.js Fill protocol + domain name ^(/)(?!/)
            js/xxx.js fill in the protocol + domain name + path + / and put it in the last elif
        """
        pattern1 = re.compile('^(\.\.|\.)')
        pattern2 = re.compile('^(//)')
        pattern3 = re.compile('^(/)(?!/)')
        for script_item in self.soup.find_all(is_script_but_no_innerhtml):
            if re.search(pattern1, script_item.attrs["src"]):
                url = self.url + script_item.attrs["src"]
            elif re.search(pattern2, script_item.attrs["src"]):
                url = scheme + ":" + script_item.attrs["src"]
            elif re.search(pattern3, script_item.attrs["src"]):
                url = scheme + "://" + host + script_item.attrs["src"]
            elif "http" not in script_item.attrs["src"]:
                url = self.url + script_item.attrs["src"]
            # If it is not the above situation, then basically only the external link with http or subdomain name is left to store js.
            # In this case, we extract the main domain name or deal with it according to the specific situation (user input)
            # Or we don't care, check them all
            else:
                url = script_item.attrs["src"]
            gbv.track[gbv.trackdeep].append(url)

    # Looking for interfaces, mainly in js, not in html, and basically no interfaces
    def search_api(self):
        pattern = re.compile("[\'\"][/]+[-A-Za-z0-9+&@#/%?=~_|!:.;]+")
        apilist = self.search_data(pattern)
        # Save the result stripped quotes to the global api list
        for i in apilist:
            if i[1:]== "//" or i[1:]== "/#":
                continue
            gbv.apiresult.append(i[1:])
            if gbv.fuzz:
                url=parse.urlparse(self.url).scheme+"://"+parse.urlparse(self.url).netloc+i[1:]
                gbv.track[gbv.trackdeep].append(url)

    # Find url (domain name or ip can match)
    # Use the url of the current domain name for backtracking, and output other urls
    def search_url(self):
        # Extract the domain name in the url, and then use it to determine whether the url result should be used for backtracking
        host = parse.urlparse(self.url).netloc
        blacklist = [".png", ".gif", ".css", ".jpg", ".video", ".mp4",".ico",".ttf",".svg",".woff2",".woff",".m4s"]
        pattern = re.compile(r"(https?|ftp|file|ssh|smb|mysql)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
        urllist = self.search_data(pattern)
        # remove some references to external sites
        pattern2 = re.compile(
            "(lodash.com|feross.org|gov.cn|github.com|github.io|vuejs.org|w3.org|mozilla.org|nodejs.org|google.com|chromium.org|w3help.org|whatwg.org|stackoverflow.com|ecma-international.org|underscorejs.org|flow.org|wikipedia.org|baidu.com)"
        )
        for i in urllist:
            # Do not in the domain name blacklist list
            if re.search(pattern2, i):
                continue
            # Remove front-end resources such as images and css
            _, file_suffix = os.path.splitext(parse.urlparse(i).path)
            if file_suffix in blacklist:
                continue
            # Save the url of the current domain name to the track list for backtracking
            # If global search is enabled, all of them will be added to the backtracking queue, otherwise only the current domain name will be added.
            gbv.urlresult.append(i)
            if gbv.searchany:
                gbv.track[gbv.trackdeep].append(i)
            elif host in i:
                gbv.track[gbv.trackdeep].append(i)


    # https://bacde.me/post/Extract-API-Keys-From-Regex/
    # https://www.cnblogs.com/timelesszhuang/p/5014595.html
    # accesskey、appid、password、proxy token、
    def search_other(self):
        # Use the regex capture group to get data ownership
        Jwt = "(?P<Jwt>(ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]{10,}\.[A-Za-z0-9._-]{10,}|ey[A-Za-z0-9_\/+-]{10,}\.[A-Za-z0-9._\/+-]{10,}\.[A-Za-z0-9._-]{10,}))"
        Ip = "(?P<Ip>[\"\'\s/(]((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3})[\"\'\s/:\)]"
        Email = "(?P<Email>([a-zA-Z0-9][_|\.])*[a-zA-Z0-9]+@([a-zA-Z0-9][-|_|\.])*[a-zA-Z0-9]+\.((?!js|css|jpg|jpeg|png|ico|webp)[a-zA-Z]{2,}))"
        ChinaIdCard = "(?P<ChinaIdCard>[1-8][1-7]\d{4}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dX])"
        ChinaMobile = "(?P<ChinaMobile>[^\w]((?:(?:\+|00)86)?1(?:(?:3[\d])|(?:4[5-79])|(?:5[0-35-9])|(?:6[5-7])|(?:7[0-8])|(?:8[\d])|(?:9[189]))\d{8})[^\w])"
        AccessKey = "(?P<AccessKey>([Aa](ccess|CCESS)_?[Kk](ey|EY)|[Aa](ccess|CCESS)_?[sS](ecret|ECRET)|[Aa](ccess|CCESS)_?(id|ID|Id)|[Aa](ccess|CCESS)[A-Za-z0-9_-]{5,10})[A-Za-z0-9\"'\s]{0,10}[=:][\s\"\']{1,5}[A-Za-z0-9]{2,30}[\"'])"
        SecretKey = "(?P<SecretKey>([Ss](ecret|ECRET)_?[Kk](ey|EY)|[Ss](ecret|ECRET)_?(id|ID|Id)|[Ss](ecret|ECRET))[^)(|]{0,10}[=:][A-Za-z0-9\"'\s]{2,30}[\"'])"
        AppId = "(?P<AppId>([Aa](pp|PP)_?[Ii][dD]|[Aa](pp|PP)_?[Kk](ey|EY)|[Aa](pp|PP)_?[Ss](ecret|ECRET))[^)(|]{0,10}[=:][\s\"\']{1,5}[^):'\"+(|]{5,30}[\"'])"
        UserName = "(?P<UserName>([Uu](ser|SER)_?[Nn](ame|AME))[^)(|,\"'\+]{0,10}[=:][\s\"\']{1,5}[^)(|\s=,]{2,30}[\"'])"
        PassWord = "(?P<PassWord>([Pp](ass|ASS)_?[Ww](ord|ORD|D|d))[^)(|,\"'\+]{0,10}[=:][\s\"\']{1,5}[^)(|\s=]{2,30}[\"'])"

        # did not test
        SSHKey = "(?P<SSHKey>-----BEGIN PRIVATE KEY-----[a-zA-Z0-9\\S]{100,}-----END PRIVATE KEY——)"
        RSAKey = "(?P<RSAKey>-----BEGIN RSA PRIVATE KEY-----[a-zA-Z0-9\\S]{100,}-----END RSA PRIVATE KEY-----)"
        GithubAccessKey = "(?P<GithubAccessKey>[a-zA-Z0-9_-]*:[a-zA-Z0-9_\\-]+@github\\.com*)"

        pattern = re.compile("{Jwt}|{Ip}|{Email}|{ChinaIdCard}|{ChinaMobile}|{AccessKey}|{SecretKey}|{AppId}|{UserName}|{PassWord}|{SSHKey}|{RSAKey}|{GithubAccessKey}".format(Jwt=Jwt, Ip=Ip,Email = Email,ChinaIdCard=ChinaIdCard,ChinaMobile=ChinaMobile  , AccessKey=AccessKey, SecretKey=SecretKey, AppId=AppId, UserName=UserName,PassWord=PassWord ,SSHKey=SSHKey ,RSAKey=RSAKey , GithubAccessKey=GithubAccessKey))
        result = self.search_data(pattern,1)
        for i in result:
            if i.group("Jwt"):
                gbv.Sensitiveinformation["Jwt"].append(i.group("Jwt"))
            elif i.group("Ip"):
                gbv.Sensitiveinformation["Ip"].append(i.group("Ip"))
            elif i.group("Email"):
                gbv.Sensitiveinformation["Email"].append(i.group("Email"))
            elif i.group("ChinaIdCard"):
                gbv.Sensitiveinformation["ChinaIdCard"].append(i.group("ChinaIdCard"))
            elif i.group("AccessKey"):
                gbv.Sensitiveinformation["AccessKey"].append(i.group("AccessKey"))
            elif i.group("SecretKey"):
                gbv.Sensitiveinformation["SecretKey"].append(i.group("SecretKey"))
            elif i.group("AppId"):
                gbv.Sensitiveinformation["AppId"].append(i.group("AppId"))
            elif i.group("UserName"):
                gbv.Sensitiveinformation["UserName"].append(i.group("UserName"))
            elif i.group("PassWord"):
                gbv.Sensitiveinformation["PassWord"].append(i.group("PassWord"))
            elif i.group("SSHKey"):
                gbv.Sensitiveinformation["SSHKey"].append(i.group("SSHKey"))
            elif i.group("RSAKey"):
                gbv.Sensitiveinformation["RSAKey"].append(i.group("RSAKey"))
            elif i.group("GithubAccessKey"):
                gbv.Sensitiveinformation["GithubAccessKey"].append(i.group("GithubAccessKey"))
            else:
                pass

    def main(self):
        t = threading.Thread(target=self.search_url)
        t.start()
        t1 = threading.Thread(target=self.search_js)
        t1.start()
        t2 = threading.Thread(target=self.search_api)
        t2.start()
        t.join()
        t1.join()
        t2.join()
        t3 = threading.Thread(target=self.search_other)
        t3.start()
        t3.join()
        return len(self.response)
