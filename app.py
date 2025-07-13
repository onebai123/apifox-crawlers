#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS

# 添加父目录到路径，以便导入现有的处理模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入工具模块
from utils.downloader import ApiDownloader
from utils.parser import LlmsParser
from utils.processor import ApiProcessor

app = Flask(__name__)
CORS(app)

# 全局变量
current_task = None
task_status = {
    'stage': 0,
    'status': 'idle',
    'message': '',
    'progress': 0,
    'error': None
}

class TaskManager:
    def __init__(self):
        self.current_task = None
        self.status = {
            'stage': 0,
            'status': 'idle',
            'message': '',
            'progress': 0,
            'error': None,
            'results': {}
        }
    
    def update_status(self, stage=None, status=None, message=None, progress=None, error=None):
        if stage is not None:
            self.status['stage'] = stage
        if status is not None:
            self.status['status'] = status
        if message is not None:
            self.status['message'] = message
        if progress is not None:
            self.status['progress'] = progress
        if error is not None:
            self.status['error'] = error
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Stage {self.status['stage']}: {message}")
    
    def reset(self):
        self.status = {
            'stage': 0,
            'status': 'idle',
            'message': '',
            'progress': 0,
            'error': None,
            'results': {}
        }

task_manager = TaskManager()

@app.route('/')
def index():
    """返回主页面"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Apifox抓取工具</title></head>
        <body>
            <h1>Apifox API文档抓取工具</h1>
            <p>请确保index.html文件存在</p>
        </body>
        </html>
        """

@app.route('/api/status')
def get_status():
    """获取当前任务状态"""
    return jsonify(task_manager.status)

@app.route('/api/stage1', methods=['POST'])
def stage1_download():
    """阶段1: 下载llms.txt和MD文件"""
    try:
        data = request.get_json()
        api_url = data.get('url')
        
        if not api_url:
            return jsonify({'error': '缺少URL参数'}), 400
        
        # 清理旧数据目录
        task_manager.update_status(stage=1, status='running', message='清理旧数据...', progress=0)
        cleanup_old_data()
        
        task_manager.update_status(message='开始下载数据...', progress=5)
        
        # 创建下载器实例
        downloader = ApiDownloader(base_url=api_url, output_dir='data/01')
        
        # 下载llms.txt
        task_manager.update_status(message='下载llms.txt...', progress=10)
        llms_content = downloader.download_llms_txt()
        
        # 解析API文档链接
        task_manager.update_status(message='解析API文档链接...', progress=30)
        parser = LlmsParser(api_url)
        
        # 添加调试信息
        print(f"DEBUG: llms_content长度: {len(llms_content)}")
        print(f"DEBUG: llms_content前200字符: {llms_content[:200]}")
        
        api_links = parser.parse_llms_content(llms_content)
        
        print(f"DEBUG: 解析结果: {api_links}")
        print(f"DEBUG: 解析结果类型: {type(api_links)}")
        if api_links:
            print(f"DEBUG: 链接数量: {len(api_links)}")
        
        # 保存解析出的链接到url.txt文件
        if api_links:
            url_file_path = os.path.join('data/01', 'url.txt')
            with open(url_file_path, 'w', encoding='utf-8') as f:
                f.write("# 解析出的API文档链接\n\n")
                for i, link in enumerate(api_links, 1):
                    f.write(f"{i}. {link['title']}\n")
                    f.write(f"   URL: {link['url']}\n")
                    f.write(f"   完整URL: {link['full_url']}\n\n")
            
            task_manager.update_status(message=f'解析完成，保存了{len(api_links)}个链接到url.txt', progress=40)
            print(f"链接已保存到: {url_file_path}")
        else:
            task_manager.update_status(message='解析失败，未找到API文档链接', progress=40)
            print("警告: 未解析出任何链接")
        
        # 批量下载MD文件
        if api_links:
            task_manager.update_status(message=f'下载{len(api_links)}个MD文件...', progress=50)
            downloaded_files = downloader.download_md_files(api_links)
        else:
            downloaded_files = []
        
        task_manager.update_status(
            status='completed', 
            message=f'下载完成: {len(downloaded_files)}个文件', 
            progress=100
        )
        
        task_manager.status['results']['stage1'] = {
            'downloaded_files': len(downloaded_files),
            'api_links': len(api_links)
        }
        
        return jsonify({
            'success': True,
            'downloaded_files': len(downloaded_files),
            'api_links': len(api_links)
        })
        
    except Exception as e:
        task_manager.update_status(status='error', error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/stage2', methods=['POST'])
def stage2_process():
    """阶段2: MD清洗和YAML转换"""
    try:
        task_manager.update_status(stage=2, status='running', message='开始数据清洗...', progress=0)
        
        # 创建数据处理器
        processor = ApiProcessor(
            base_dir='data'
        )
        
        # 处理MD文件并转换为YAML
        task_manager.update_status(message='处理MD文件并转换为YAML...', progress=20)
        stage2_result = processor.stage2_clean_and_convert()
        
        if stage2_result and 'processed' in stage2_result:
            processed_count = stage2_result['processed']
            valid_count = stage2_result['valid']
            docs_zip = stage2_result.get('docs_zip')
            
            message = f'处理完成: {processed_count}个文件，有效{valid_count}个'
            if docs_zip:
                message += f'，文档ZIP: {docs_zip}'
            
            task_manager.update_status(
                status='completed',
                message=message,
                progress=100
            )
            
            task_manager.status['results']['stage2'] = {
                'processed_files': processed_count,
                'valid_files': valid_count,
                'docs_zip': docs_zip
            }
        else:
            raise Exception("阶段2处理失败")
        
        return jsonify({
            'success': True,
            'processed_files': processed_count,
            'valid_files': valid_count
        })
        
    except Exception as e:
        task_manager.update_status(status='error', error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/stage3', methods=['POST'])
def stage3_merge():
    """阶段3: 最终YAML合并"""
    try:
        task_manager.update_status(stage=3, status='running', message='开始合并YAML文件...', progress=0)
        
        # 创建数据处理器
        processor = ApiProcessor(
            base_dir='data'
        )
        
        # 合并所有YAML文件
        task_manager.update_status(message='合并YAML文件...', progress=30)
        result = processor.stage3_merge_final()
        
        if result and 'merged_files' in result:
            merged_count = result['merged_files']
            final_file = result.get('final_file', 'data/final/merged_apis.yml')
            
            task_manager.update_status(
                status='completed',
                message=f'合并完成: {merged_count}个文件',
                progress=100
            )
            
            task_manager.status['results']['stage3'] = {
                'merged_files': merged_count,
                'final_file': final_file
            }
            
            return jsonify({
                'success': True,
                'merged_files': merged_count,
                'final_file': final_file
            })
        else:
            raise Exception("阶段3处理失败")
        
    except Exception as e:
        task_manager.update_status(status='error', error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/complete.yaml')
def download_complete_yaml():
    """下载最终的完整YAML文件"""
    try:
        # 查找final目录中的YAML文件
        final_dir = 'data/final'
        if os.path.exists(final_dir):
            yml_files = [f for f in os.listdir(final_dir) if f.endswith('.yml') or f.endswith('.yaml')]
            if yml_files:
                final_file = os.path.join(final_dir, yml_files[0])
                return send_file(
                    final_file,
                    as_attachment=True,
                    download_name='apifox_complete_api.yaml',
                    mimetype='text/yaml'
                )
        
        return jsonify({'error': '文件不存在，请先完成处理流程'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/docs.zip')
def download_docs_zip():
    """下载文档ZIP文件"""
    try:
        # 查找final目录中的ZIP文件
        final_dir = 'data/final'
        if os.path.exists(final_dir):
            zip_files = [f for f in os.listdir(final_dir) if f.endswith('.zip')]
            if zip_files:
                # 获取最新的ZIP文件
                zip_files.sort(reverse=True)  # 按文件名倒序排列，获取最新的
                final_file = os.path.join(final_dir, zip_files[0])
                return send_file(
                    final_file,
                    as_attachment=True,
                    download_name='apifox_docs.zip',
                    mimetype='application/zip'
                )
        
        return jsonify({'error': 'ZIP文件不存在，请先完成处理流程'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_task():
    """重置任务状态"""
    task_manager.reset()
    return jsonify({'success': True, 'message': '任务状态已重置'})

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载生成的文件"""
    try:
        # 检查文件类型
        if filename.endswith('.yml'):
            # YAML文件在final目录
            file_path = os.path.join('data', 'final', filename)
            if not os.path.exists(file_path):
                # 尝试查找实际的YAML文件
                final_dir = os.path.join('data', 'final')
                if os.path.exists(final_dir):
                    yml_files = [f for f in os.listdir(final_dir) if f.endswith('.yml')]
                    if yml_files:
                        file_path = os.path.join(final_dir, yml_files[0])
                        filename = yml_files[0]
                    else:
                        return jsonify({'error': '文件不存在，请先完成处理流程'}), 404
                else:
                    return jsonify({'error': '文件不存在，请先完成处理流程'}), 404
            
            return send_file(file_path, as_attachment=True, download_name=filename)
            
        elif filename.endswith('.zip'):
            # ZIP文件在final目录
            file_path = os.path.join('data', 'final', filename)
            if not os.path.exists(file_path):
                return jsonify({'error': '文件不存在，请先完成处理流程'}), 404
            
            return send_file(file_path, as_attachment=True, download_name=filename)
        
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件服务"""
    return send_file(f'static/{filename}')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

def cleanup_old_data():
    """清理旧数据目录"""
    import shutil
    try:
        if os.path.exists('data'):
            shutil.rmtree('data')
            print("已清理旧数据目录")
    except Exception as e:
        print(f"清理数据目录失败: {str(e)}")

def create_directories():
    """创建必要的目录"""
    directories = [
        'data/01/md',
        'data/02/md',
        'data/02/yml',
        'data/final',
        'data/final/md',
        'static/css',
        'static/js',
        'templates',
        'utils'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("目录结构创建完成")

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Apifox API文档抓取工具")
    print("=" * 50)
    
    # 创建必要的目录
    create_directories()
    
    print("服务器启动中...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )