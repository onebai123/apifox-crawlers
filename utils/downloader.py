#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import re

class ApiDownloader:
    """API文档下载器"""
    
    def __init__(self, base_url, output_dir='data/01', max_workers=5):
        self.base_url = base_url.rstrip('/')
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 创建输出目录
        os.makedirs(os.path.join(self.output_dir, 'md'), exist_ok=True)
        
        print(f"下载器初始化完成 - 基础URL: {self.base_url}")
        print(f"输出目录: {self.output_dir}")
        print(f"最大并发数: {self.max_workers}")
    
    def download_llms_txt(self):
        """下载llms.txt文件"""
        llms_url = f"{self.base_url}/llms.txt"
        output_file = os.path.join(self.output_dir, 'llms.txt')
        
        print(f"开始下载llms.txt: {llms_url}")
        
        try:
            response = self.session.get(llms_url, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"llms.txt下载成功: {len(response.text)} 字符")
            return response.text
            
        except requests.exceptions.RequestException as e:
            error_msg = f"下载llms.txt失败: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def download_single_md(self, url, filename=None):
        """下载单个MD文件"""
        if not filename:
            # 从URL提取文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.md'):
                filename += '.md'
        
        output_path = os.path.join(self.output_dir, 'md', filename)
        
        try:
            # 构建完整URL
            if not url.startswith('http'):
                full_url = urljoin(self.base_url + '/', url)
            else:
                full_url = url
            
            print(f"下载: {filename} <- {full_url}")
            
            response = self.session.get(full_url, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            return {
                'filename': filename,
                'url': full_url,
                'size': len(response.text),
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"下载失败 {filename}: {str(e)}"
            print(error_msg)
            return {
                'filename': filename,
                'url': full_url if 'full_url' in locals() else url,
                'error': str(e),
                'success': False
            }
        except Exception as e:
            error_msg = f"处理文件失败 {filename}: {str(e)}"
            print(error_msg)
            return {
                'filename': filename,
                'url': url,
                'error': str(e),
                'success': False
            }
    
    def download_md_files(self, api_links, progress_callback=None):
        """批量下载MD文件"""
        print(f"开始批量下载 {len(api_links)} 个MD文件...")
        
        downloaded_files = []
        failed_files = []
        
        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有下载任务
            future_to_link = {}
            for i, link_info in enumerate(api_links):
                url = link_info.get('url', '')
                title = link_info.get('title', f'api_{i}')
                
                # 生成安全的文件名
                safe_filename = self._generate_safe_filename(title, url)
                
                future = executor.submit(self.download_single_md, url, safe_filename)
                future_to_link[future] = link_info
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_link):
                result = future.result()
                completed += 1
                
                if result['success']:
                    downloaded_files.append(result)
                    print(f"✓ [{completed}/{len(api_links)}] {result['filename']} ({result['size']} 字符)")
                else:
                    failed_files.append(result)
                    print(f"✗ [{completed}/{len(api_links)}] {result['filename']} - {result['error']}")
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(completed, len(api_links))
                
                # 添加小延迟避免过于频繁的请求
                time.sleep(0.1)
        
        print(f"\n下载完成统计:")
        print(f"成功: {len(downloaded_files)} 个文件")
        print(f"失败: {len(failed_files)} 个文件")
        
        if failed_files:
            print("\n失败的文件:")
            for failed in failed_files:
                print(f"  - {failed['filename']}: {failed['error']}")
        
        return downloaded_files
    
    def _generate_safe_filename(self, title, url):
        """生成安全的文件名"""
        # 从URL提取ID
        url_match = re.search(r'(\d+[a-zA-Z]\d+)\.md', url)
        if url_match:
            file_id = url_match.group(1)
        else:
            file_id = str(hash(url))[-8:]
        
        # 清理标题，移除特殊字符
        safe_title = re.sub(r'[^\w\u4e00-\u9fff\-_\(\)]', '_', title)
        safe_title = re.sub(r'_+', '_', safe_title).strip('_')
        
        # 限制长度
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        
        # 组合文件名
        filename = f"{file_id}_{safe_title}.md"
        
        return filename
    
    def verify_downloads(self):
        """验证下载的文件"""
        md_dir = os.path.join(self.output_dir, 'md')
        
        if not os.path.exists(md_dir):
            return {'total': 0, 'valid': 0, 'invalid': []}
        
        files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
        valid_files = []
        invalid_files = []
        
        for filename in files:
            filepath = os.path.join(md_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单验证：检查是否包含基本的markdown内容
                if len(content) > 100 and ('```' in content or '#' in content):
                    valid_files.append(filename)
                else:
                    invalid_files.append(filename)
                    
            except Exception as e:
                invalid_files.append(f"{filename} (读取错误: {str(e)})")
        
        result = {
            'total': len(files),
            'valid': len(valid_files),
            'invalid': invalid_files
        }
        
        print(f"\n文件验证结果:")
        print(f"总文件数: {result['total']}")
        print(f"有效文件: {result['valid']}")
        print(f"无效文件: {len(result['invalid'])}")
        
        if result['invalid']:
            print("无效文件列表:")
            for invalid in result['invalid']:
                print(f"  - {invalid}")
        
        return result
    
    def get_download_stats(self):
        """获取下载统计信息"""
        md_dir = os.path.join(self.output_dir, 'md')
        llms_file = os.path.join(self.output_dir, 'llms.txt')
        
        stats = {
            'llms_exists': os.path.exists(llms_file),
            'md_files_count': 0,
            'total_size': 0
        }
        
        if os.path.exists(md_dir):
            md_files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
            stats['md_files_count'] = len(md_files)
            
            for filename in md_files:
                filepath = os.path.join(md_dir, filename)
                try:
                    stats['total_size'] += os.path.getsize(filepath)
                except:
                    pass
        
        if stats['llms_exists']:
            try:
                stats['total_size'] += os.path.getsize(llms_file)
            except:
                pass
        
        return stats

if __name__ == "__main__":
    # 测试代码
    downloader = ApiDownloader("https://api-gpt-ge.apifox.cn", "test_output")
    
    try:
        # 测试下载llms.txt
        content = downloader.download_llms_txt()
        print(f"下载内容长度: {len(content)}")
        
        # 获取统计信息
        stats = downloader.get_download_stats()
        print(f"统计信息: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")