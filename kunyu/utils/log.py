#!/usr/bin/env python
# encoding: utf-8
'''
@author: 风起
@contact: onlyzaliks@gmail.com
@File: log.py
@Time: 2021/6/15 15:54
'''

import logging
import colorlog  # 控制台日志输入颜色

logger = logging.getLogger("kunyu-log")
logger_console = logging.getLogger("kunyu-console")


def console():
    handler = logging.StreamHandler()
    log_colors_config = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }
    formatter = colorlog.ColoredFormatter(
        '%(log_color)s[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s',
        log_colors=log_colors_config,
        datefmt="%H:%M:%S",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def log_console():
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt='%(log_color)s%(message)s',
            datefmt="%H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'white',
                'WARNING': 'bold_yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            },
        )
    )
    logger_console.addHandler(handler)
    logger_console.setLevel(logging.DEBUG)


console()
log_console()
