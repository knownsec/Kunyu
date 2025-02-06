# -*- coding: utf8 -*-
import requests


def main_handler(event, context):
    headers = event["headers"]
    ip = headers["ip"]
    header_new = {
        "Host": headers["hosts"],
        "User-Agent": headers["user-agent"],
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,ko;q=0.8",
        "Connection": "close"
    }
    try:
        r = requests.get(ip, headers=header_new, timeout=10, verify=False)
        if r.status_code == 200:
            r.encoding = "gbk2312"
            return r.text
    except Exception as err:
        print(err)

    return False
