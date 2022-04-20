#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: scanalive.py
@Time: 2022/2/24 10:47
"""
import os

import nmap

class Scan_Alive_Ip:
    def __init__(self):
        self.alive_data_params = {}
    def scan_port_status(self, ip, port):
        nm = nmap.PortScanner()
        # Semi-open scan using TCP SYN
        nm.scan(ip, port, "-sS")
        for host in nm.all_hosts():
            for proto in nm[host].all_protocols():
                for port in nm[host][proto].keys():
                    self.alive_data_params = {"ip": ip, "port":port, "state":nm[host][proto][port]['state']}
        return self.alive_data_params

    def scan_cobaltstrike_status(self, ip, port):
        nm = nmap.PortScanner()
        nse_path = str(os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + "/lib/grab_beacon_config").replace("\\","/")
        result = nm.scan(ip, port, "--script={}".format(nse_path))
        return result