#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Apifox API文档处理工具包

包含以下模块：
- downloader: API文档下载器
- parser: llms.txt文件解析器  
- processor: 三阶段数据处理器
"""

from .downloader import ApiDownloader
from .parser import LlmsParser
from .processor import ApiProcessor

__version__ = "1.0.0"
__author__ = "Apifox Team"

__all__ = [
    'ApiDownloader',
    'LlmsParser', 
    'ApiProcessor'
]