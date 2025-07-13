#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from utils.downloader import ApiDownloader
from utils.parser import LlmsParser
from utils.processor import ApiProcessor

def test_apifox_url(base_url):
    """
    测试指定的Apifox URL的完整工作流程
    
    Args:
        base_url (str): Apifox文档的基础URL，如 https://wddotnlfvy.apifox.cn/
    """
    
    print("=" * 80)
    print(f"🚀 测试Apifox URL: {base_url}")
    print("=" * 80)
    
    try:
        # 清理URL格式
        base_url = base_url.rstrip('/')
        
        # 阶段1：下载和解析
        print("\n📥 阶段1：下载llms.txt并解析所有MD链接")
        print("-" * 60)
        
        # 初始化下载器和解析器
        downloader = ApiDownloader(base_url)
        parser = LlmsParser(base_url)
        
        # 下载llms.txt
        print("正在下载llms.txt...")
        if not downloader.download_llms_txt():
            print("❌ llms.txt下载失败")
            return False
        print("✅ llms.txt下载成功")
        
        # 解析所有链接
        print("正在解析所有MD链接...")
        with open('data/01/llms.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_links = parser.parse_llms_content(content)
        if not all_links:
            print("❌ 解析失败，未找到任何链接")
            return False
        
        print(f"✅ 解析成功，找到 {len(all_links)} 个文档链接")
        
        # 保存链接到url.txt
        with open('data/01/url.txt', 'w', encoding='utf-8') as f:
            f.write(f"# 从 {base_url} 解析出的所有MD文档链接\n\n")
            for i, link in enumerate(all_links, 1):
                section = link.get('section', 'Unknown')
                f.write(f"{i}. [{section}] {link['title']}\n")
                f.write(f"   URL: {link['url']}\n")
                f.write(f"   完整URL: {link['full_url']}\n\n")
        print("✅ url.txt文件已生成")
        
        # 下载所有MD文件
        print("正在下载所有MD文件...")
        downloaded_files = downloader.download_md_files(all_links)
        success_count = len(downloaded_files)
        total_count = len(all_links)
        print(f"✅ MD文件下载完成：{success_count}/{total_count}")
        
        if success_count == 0:
            print("❌ 没有成功下载任何文件")
            return False
        
        # 阶段2：处理和转换
        print("\n🔄 阶段2：MD文件清洗和YAML转换")
        print("-" * 60)
        
        processor = ApiProcessor()
        print("正在处理MD文件...")
        stage2_result = processor.stage2_clean_and_convert()
        
        if stage2_result and 'processed' in stage2_result:
            processed_count = stage2_result['processed']
            valid_count = stage2_result['valid']
            print(f"✅ 阶段2处理完成：{processed_count} 个文件")
            print(f"✅ 包含API规范：{valid_count} 个文件")
            print(f"📄 纯文档：{processed_count - valid_count} 个文件（教程、配置等）")
        else:
            print("❌ 阶段2处理失败")
            return False
        
        # 阶段3：最终合并
        print("\n📋 阶段3：最终YAML合并")
        print("-" * 60)
        
        if valid_count > 0:
            print("正在合并YAML文件...")
            stage3_result = processor.stage3_merge_final()
            
            if isinstance(stage3_result, int) and stage3_result >= 0:
                print(f"✅ 阶段3合并完成：{stage3_result} 个分类")
                
                # 检查最终输出文件
                final_files = []
                if os.path.exists(processor.final_dir):
                    final_files = [f for f in os.listdir(processor.final_dir) if f.endswith('.yml')]
                print(f"📁 最终YAML文件：{len(final_files)} 个")
                
                if final_files:
                    print("生成的YAML文件:")
                    for file in final_files:
                        file_path = os.path.join(processor.final_dir, file)
                        file_size = os.path.getsize(file_path)
                        print(f"  - {file} ({file_size} 字节)")
            else:
                print("❌ 阶段3合并失败")
                return False
        else:
            print("⚠️  跳过阶段3：没有找到API规范文档")
        
        # 最终统计
        print("\n" + "=" * 80)
        print("🎉 测试完成！")
        print("=" * 80)
        
        print(f"\n📊 处理统计：")
        print(f"   - 基础URL：{base_url}")
        print(f"   - 文档链接数量：{len(all_links)}")
        print(f"   - MD文件下载：{success_count}/{total_count}")
        print(f"   - 处理文件数：{processed_count}")
        print(f"   - API规范文件：{valid_count}")
        print(f"   - 最终YAML分类：{stage3_result if valid_count > 0 else 0}")
        
        # 按部分统计
        section_counts = {}
        for link in all_links:
            section = link.get('section', 'Unknown')
            section_counts[section] = section_counts.get(section, 0) + 1
        
        print(f"\n📋 各部分统计：")
        for section, count in section_counts.items():
            print(f"   - {section}：{count} 个文档")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python test_with_url.py <apifox_url>")
        print("示例: python test_with_url.py https://wddotnlfvy.apifox.cn/")
        sys.exit(1)
    
    base_url = sys.argv[1]
    success = test_apifox_url(base_url)
    
    if success:
        print("\n✅ 测试成功完成！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()