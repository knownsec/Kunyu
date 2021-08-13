#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: encode.py
@Time: 2021/6/15 15:40
'''

import re
import os
import base64
import codecs
import hashlib
import socket

import ssl
import mmh3
import requests

from tld import get_fld
from kunyu.utils.log import logger
from kunyu.config.setting import IP_ADDRESS_REGEX, HTTP_CHECK_REGEX


class EncodeHash:
    """"
        According to different search engines,
        Select the appropriate ICO icon encryption method.
        ZoomEye, for example, supports both MMH3 and MD5,But FoFa only supports MMH3.
        Through the ICO icon search Related assets,It's very always efficient.
        Security researchers can also modify code files as needed.
    """

    def __init__(self, func):
        self.filename = None
        self.status = False
        self.func = func

    def __call__(self, *args, **kwargs):
        self.filename, self.status = self.func(*args, **kwargs)
        icohash = EncodeHash.http_encode(self) if self.check_http() else self.file_encode()
        return icohash if icohash is not None else logger.warning("The hash was not successfully computed")

    def check_http(self):
        # Determine if it is valid URL.
        if re.search(IP_ADDRESS_REGEX, self.filename):
            return True

        if re.findall(HTTP_CHECK_REGEX, self.filename):
            if get_fld(self.filename):
                return True
            return False

    # Get File favicon Images Encode Hash
    def file_encode(self):
        # MD5 encrypted files.
        if os.path.isfile(self.filename):
            fp = open(self.filename, 'rb')
            contents = fp.read()
            fp.close()
        else:
            return logger.warning("No Such File or URL!")

        # Select an encryption mode
        return hashlib.md5(contents).hexdigest() if self.status else mmh3.hash(
            codecs.lookup('base64').encode(contents)[0])

    # Get HTTP favicon Images Encode Hash
    def http_encode(self):
        try:
            # Select an encryption mode
            if self.status:
                return hashlib.md5(requests.get(self.filename, timeout=0.5).content).hexdigest()
            else:
                return mmh3.hash(codecs.lookup('base64').encode(requests.get(self.filename, timeout=0.5).content)[0])
        except:
            return


# Calculate md5 Hash
@EncodeHash
def encode_md5(filename):
    return filename, True


# Calculate mmh3 Hash
@EncodeHash
def encode_mmh3(filename):
    return filename, False


# encode hex
def encode_hex(string):
    return int(string, 16)


# encode base64
def encode_base64(string):
    bytes_str = string.encode("utf-8")
    return str(base64.b64encode(bytes_str).decode("utf-8"))


# Cert series number calculate Hash
def cert_encode(hostname):
    try:
        c = ssl.create_default_context()
        host = re.sub(HTTP_CHECK_REGEX, '', hostname)
        s = c.wrap_socket(socket.socket(), server_hostname=host)
        s.settimeout(5)
        s.connect((host, 443))
        # Return Hexadecimal code
        return encode_hex(s.getpeercert()["serialNumber"])

    except Exception:
        return logger.warning("Please confirm that the target uses HTTPS or is accessible")



