"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: GlobalVariable.py
@Time: 2025/1/16 15:53
"""
import json
import requests


def get_ip_location():
    ip_lookup_url = f"https://ipapi.co/json"
    resp = json.loads(requests.get(ip_lookup_url,timeout=30).text)
    if "CN" in resp.get("country") or "China" in resp.get("country_name"):
        return True
    return False