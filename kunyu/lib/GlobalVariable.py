"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: GlobalVariable.py
@Time: 2022/3/18 15:53
"""

from typing import Any, Iterable, TypeVar

NameType = TypeVar('NameType', str, Iterable[str])
global globalVariables

class GlobalVariable:
    def __init__(self) -> None:
        pass

    def all(self):
        attrs = [i for i in dir(self)]
        attr = []
        for i in range(len(attrs)):
            if len(attrs[i]) > 1:
                if '__' == attrs[i][:2]:
                    continue
            if attrs[i] in ['all', 'add', 'rm', 'get']:
                continue

            attr.append(attrs[i])
        return attr

    def add(self, name: NameType, value: Any):
        if isinstance(name, Iterable) \
                and (not isinstance(value, Iterable)):
            raise TypeError("value should be Iterable when name is Iterable")
        if type(name) is str:
            name = [name]
            value = [value]

        for n, v in zip(name, value):
            exec('self.{}={}'.format(n, v))

    def rm(self, name: NameType):
        if type(name) is str:
            name = [name]
        for n in name:
            self.__delattr__(n)

    def get(self, name: NameType):
        if type(name) is str:
            return self.__getattribute__(name)
        else:
            attrs = []
            for n in name:
                attrs.append(self.__getattribute__(n))
            return attrs

try:
    tmp = globalVariables.all()
except NameError:
    globalVariables = GlobalVariable()
