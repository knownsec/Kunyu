#!/usr/bin/env python
# encoding: utf-8
"""
@author: 风起
@contact: onlyzaliks@gmail.com
@File: tables.py
@Time: 2022/3/17 11:05
"""

from rich.table import Table

class DisposeTables:
    def __init__(self) -> None:
        self.tables = Table(show_header=True, style="bold")

    def result_table(self, title, overflow="ignore"):
        for cloumn in title:
            self.tables.add_column(
                cloumn, justify="center", overflow=overflow
            )
        return self.tables
