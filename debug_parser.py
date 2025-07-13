#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.parser import LlmsParser

# 测试解析器
parser = LlmsParser("https://wddotnlfvy.apifox.cn")

# 读取llms.txt文件
with open('data/01/llms.txt', 'r', encoding='utf-8') as f:
    content = f.read()

print("=== llms.txt内容 ===")
print(content)
print("\n=== 开始解析 ===")

# 解析内容
api_links = parser.parse_llms_content(content)

print(f"\n=== 解析结果 ===")
print(f"找到 {len(api_links) if api_links else 0} 个链接")

if api_links:
    for i, link in enumerate(api_links):
        print(f"{i+1}. {link['title']} -> {link['url']}")
else:
    print("没有找到任何链接")

# 测试单行解析
print("\n=== 测试单行解析 ===")
test_line = "- 用法2-代码：3.5/4.0接口测试 [直接拷贝，下方py/java代码例子）](https://wddotnlfvy.apifox.cn/225958553e0.md): "
result = parser._extract_link_from_line(test_line)
print(f"测试行: {test_line}")
print(f"解析结果: {result}")