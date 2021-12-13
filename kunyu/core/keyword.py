#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: keyword.py
@Time: 2021/11/12 9:23
'''
import re

from rich.table import Table
from rich.console import Console

console = Console(color_system="auto", record=True)
EMAIL_REGEX = r"([\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+)"
PHONE_REGEX = r"^1[358]\d{9}$|^147\d{8}$|^179\d{8}$"
DOMAIN_REGEX = r'<a\s*href=\"(.*?)\"'
IDENTITY_REGEX = r"[1-9]\d{5}(?:18|19|(?:[23]\d))\d{2}(?:(?:0[1-9])|(?:10|11|12))(?:(?:[0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]"
IP_ADDRESS_REGEX = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
DOMAIN_CHECK_REGEX = r'<a\s*href=\"(.*?)\"'


class SearchKeyWord:
    def __init__(self):
        self.sensitive_params = []

    def __check_email(self, banner):
        email_mod = re.compile(EMAIL_REGEX)
        items = email_mod.findall(banner)
        return items

    # Check whether it is valid phone number
    def __check_phone(self, banner):
        phone_mod = re.compile(PHONE_REGEX)
        items = phone_mod.findall(banner)
        return items

    """
        # Check whether it is valid domain address
        def __check_domain_address(self, banner):
            domain_mod = re.compile(DOMAIN_REGEX)
            items = domain_mod.findall(banner)
            return items
    """

    # Check whether it is valid ip address
    def __check_ip_address(self, banner):
        ip_mod = re.compile(IP_ADDRESS_REGEX)
        items = ip_mod.findall(banner)
        return items

    """
        # Check whether it is valid identity card
        def __check_identity(self, banner):
            identity_mod = re.compile(IDENTITY_REGEX)
            items = identity_mod.findall(banner)
            return items
    """

    def get_keyword_sensitive(self, banner):
        # Obtain email information in the banner
        for email in self.__check_email(banner):
            self.sensitive_params.append(email[0])

        # Obtain phone number information in the banner
        for phone in self.__check_phone(banner):
            self.sensitive_params.append(phone[0])

        """ 
            # Obtain domain information in the banner
            for domain in self.__check_domain_address(banner):
                self.sensitive_params.append(domain[0])

            # Obtain identity card information in the banner
            for identity in self.__check_identity(banner):
                self.sensitive_params.append(identity[0])
        """

        # Obtain ip address information in the banner
        for ip in self.__check_ip_address(banner):
            self.sensitive_params.append(ip)

        if self.sensitive_params:
            return self.sensitive_params
