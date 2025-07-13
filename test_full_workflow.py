#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from utils.downloader import ApiDownloader
from utils.parser import LlmsParser
from utils.processor import ApiProcessor

def test_full_workflow():
    """测试完整的三阶段工作流程"""
    
    base_url = "https://wddotnlfvy.apifox.cn"
    
    print("=" * 60)
    print("🚀 开始测试完整工作流程")
    print("=" * 60)
    
    # 阶段1：下载和解析
    print("\n📥 阶段1：下载llms.txt并解析API链接")
    print("-" * 40)
    
    downloader = ApiDownloader(base_url)
    parser = LlmsParser(base_url)
    
    # 下载llms.txt
    print("正在下载llms.txt...")
    if downloader.download_llms_txt():
        print("✅ llms.txt下载成功")
    else:
        print("❌ llms.txt下载失败")
        return False
    
    # 解析链接
    print("正在解析API链接...")
    with open('data/01/llms.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    api_links = parser.parse_llms_content(content)
    if api_links:
        print(f"✅ 解析成功，找到 {len(api_links)} 个API链接")
        
        # 保存链接到url.txt
        with open('data/01/url.txt', 'w', encoding='utf-8') as f:
            f.write("# 解析出的API文档链接\n\n")
            for i, link in enumerate(api_links, 1):
                f.write(f"{i}. {link['title']}\n")
                f.write(f"   URL: {link['url']}\n")
                f.write(f"   完整URL: {link['full_url']}\n\n")
        print("✅ url.txt文件已生成")
    else:
        print("❌ 解析失败")
        return False
    
    # 下载MD文件
    print("正在下载MD文件...")
    downloaded_files = downloader.download_md_files(api_links)
    success_count = len(downloaded_files)
    total_count = len(api_links)
    print(f"✅ MD文件下载完成：{success_count}/{total_count}")
    
    # 阶段2：处理和转换
    print("\n🔄 阶段2：MD文件清洗和YAML转换")
    print("-" * 40)
    
    processor = ApiProcessor()
    
    # 处理MD文件
    # 处理MD文件
    print("正在处理MD文件...")
    stage2_result = processor.stage2_clean_and_convert()
    if stage2_result and 'processed' in stage2_result:
        print(f"✅ 阶段2处理完成：{stage2_result['processed']} 个文件")
        print(f"✅ 有效文件：{stage2_result['valid']} 个")
    else:
        print("❌ 阶段2处理失败")
        return False
    
    # 阶段3：最终合并
    print("\n📋 阶段3：最终YAML合并")
    print("-" * 40)
    
    print("正在合并YAML文件...")
    stage3_result = processor.stage3_merge_final()
    
    # 检查返回结果格式
    if isinstance(stage3_result, dict) and 'merged_files' in stage3_result:
        merged_count = stage3_result['merged_files']
        total_categories = stage3_result.get('total_categories', merged_count)
        print(f"✅ 阶段3合并完成：{merged_count}/{total_categories} 个分类")
        
        # 检查最终输出文件
        final_files = []
        if os.path.exists(processor.final_dir):
            final_files = [f for f in os.listdir(processor.final_dir) if f.endswith('.yml')]
        print(f"📁 最终文件数量：{len(final_files)} 个")
        
        # 只要有成功合并的分类就算成功
        if merged_count > 0:
            stage3_result = merged_count  # 为了后续统计显示
        else:
            print("❌ 阶段3合并失败：没有成功合并任何分类")
            return False
    else:
        print("❌ 阶段3合并失败")
        return False
    print("\n" + "=" * 60)
    print("🎉 完整工作流程测试成功！")
    print("=" * 60)
    
    # 显示结果统计
    print(f"\n📊 处理统计：")
    print(f"   - API链接数量：{len(api_links)}")
    print(f"   - MD文件下载：{success_count}/{total_count}")
    print(f"   - YAML文件处理：{stage2_result['processed']}")
    print(f"   - 最终合并分类：{stage3_result}")
    
    return True

if __name__ == "__main__":
    test_full_workflow()