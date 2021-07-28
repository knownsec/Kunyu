#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: convert.py
@Time: 2021/7/3 0:47
'''


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


# Dict conversion object
def convert(dictObj):
    if not isinstance(dictObj, dict):
        return dictObj
    json = Dict()
    for k, v in dictObj.items():
        json[k] = convert(v)
    return json
