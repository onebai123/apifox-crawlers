#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
from test_full_workflow import test_full_workflow

def cleanup_data():
    """清理旧数据目录"""
    try:
        if os.path.exists('data'):
            shutil.rmtree('data')
            print("✅ 已清理旧数据目录")
        else:
            print("ℹ️  数据目录不存在，无需清理")
    except Exception as e:
        print(f"❌ 清理数据目录失败: {str(e)}")
        return False
    return True

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_with_cleanup.py <URL>")
        print("示例: python test_with_cleanup.py https://wddotnlfvy.apifox.cn/")
        return
    
    url = sys.argv[1]
    print("=" * 60)
    print("🧹 清理旧数据并测试新URL")
    print("=" * 60)
    print(f"目标URL: {url}")
    
    # 清理旧数据
    if not cleanup_data():
        print("❌ 数据清理失败，退出测试")
        return
    
    # 修改测试脚本中的URL
    import test_full_workflow
    test_full_workflow.test_full_workflow.__globals__['base_url'] = url
    
    # 运行测试
    print("\n🚀 开始测试...")
    try:
        success = test_full_workflow.test_full_workflow()
        if success:
            print("\n🎉 测试成功完成！")
        else:
            print("\n❌ 测试失败！")
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()