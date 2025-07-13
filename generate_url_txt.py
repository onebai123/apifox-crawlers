#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.parser import LlmsParser

# 基于debug_parser.py的成功结果，直接生成url.txt文件
parser = LlmsParser("https://wddotnlfvy.apifox.cn")

# 读取llms.txt文件
with open('data/01/llms.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("开始解析llms.txt并生成url.txt...")

# 解析内容
api_links = parser.parse_llms_content(content)

if api_links:
    # 保存到url.txt
    url_file_path = 'data/01/url.txt'
    with open(url_file_path, 'w', encoding='utf-8') as f:
        f.write("# 解析出的API文档链接\n\n")
        for i, link in enumerate(api_links, 1):
            f.write(f"{i}. {link['title']}\n")
            f.write(f"   URL: {link['url']}\n")
            f.write(f"   完整URL: {link['full_url']}\n\n")
    
    print(f"✅ 成功生成url.txt文件，包含 {len(api_links)} 个链接")
    print(f"文件路径: {url_file_path}")
    
    # 显示链接列表
    print("\n解析出的链接:")
    for i, link in enumerate(api_links, 1):
        print(f"  {i}. {link['title']}")
        print(f"     -> {link['url']}")
else:
    print("❌ 解析失败，未找到任何链接")