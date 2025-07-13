#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import yaml
import json
import shutil
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class ApiProcessor:
    """API文档处理器 - 三阶段处理流程"""
    
    def __init__(self, base_dir='data'):
        self.base_dir = base_dir
        self.stage1_dir = os.path.join(base_dir, '01')
        self.stage2_dir = os.path.join(base_dir, '02')
        self.final_dir = os.path.join(base_dir, 'final')
        
        # 创建目录结构
        self._create_directories()
        
        print(f"API处理器初始化完成")
        print(f"阶段1目录: {self.stage1_dir}")
        print(f"阶段2目录: {self.stage2_dir}")
        print(f"最终目录: {self.final_dir}")
    
    def _create_directories(self):
        """创建必要的目录结构"""
        directories = [
            os.path.join(self.stage1_dir, 'md'),
            os.path.join(self.stage2_dir, 'md'),
            os.path.join(self.stage2_dir, 'yml'),
            self.final_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def stage1_store_raw_files(self, source_dir):
        """阶段1：存储原始MD文件"""
        print("\n=== 阶段1：存储原始MD文件 ===")
        
        source_md_dir = os.path.join(source_dir, 'md')
        target_md_dir = os.path.join(self.stage1_dir, 'md')
        
        if not os.path.exists(source_md_dir):
            raise Exception(f"源目录不存在: {source_md_dir}")
        
        # 复制所有MD文件
        md_files = [f for f in os.listdir(source_md_dir) if f.endswith('.md')]
        
        if not md_files:
            raise Exception(f"源目录中没有找到MD文件: {source_md_dir}")
        
        copied_count = 0
        for filename in md_files:
            source_file = os.path.join(source_md_dir, filename)
            target_file = os.path.join(target_md_dir, filename)
            
            try:
                shutil.copy2(source_file, target_file)
                copied_count += 1
            except Exception as e:
                print(f"复制文件失败 {filename}: {str(e)}")
        
        print(f"阶段1完成: 复制了 {copied_count} 个MD文件")
        return copied_count
    
    def stage2_clean_and_convert(self, progress_callback=None):
        """阶段2：清洗MD文件并转换为YAML"""
        print("\n=== 阶段2：清洗和转换 ===")
        
        source_md_dir = os.path.join(self.stage1_dir, 'md')
        target_md_dir = os.path.join(self.stage2_dir, 'md')
        target_yml_dir = os.path.join(self.stage2_dir, 'yml')
        
        md_files = [f for f in os.listdir(source_md_dir) if f.endswith('.md')]
        
        if not md_files:
            raise Exception(f"阶段1目录中没有MD文件: {source_md_dir}")
        
        processed_count = 0
        valid_count = 0
        
        for i, filename in enumerate(md_files):
            source_file = os.path.join(source_md_dir, filename)
            
            try:
                # 处理单个文件
                result = self._process_single_md_file(source_file, target_md_dir, target_yml_dir)
                
                if result['success']:
                    valid_count += 1
                    print(f"✓ [{i+1}/{len(md_files)}] {filename}")
                else:
                    print(f"✗ [{i+1}/{len(md_files)}] {filename} - {result['error']}")
                
                processed_count += 1
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(processed_count, len(md_files))
                    
            except Exception as e:
                print(f"处理文件失败 {filename}: {str(e)}")
        
        # 复制Docs文档到final/md目录
        self._copy_docs_to_final()
        
        # 生成文档ZIP文件
        docs_zip_path = self._create_docs_zip()
        
        print(f"阶段2完成: 处理了 {processed_count} 个文件，有效 {valid_count} 个")
        print(f"文档ZIP文件: {docs_zip_path}")
        
        return {
            'processed': processed_count,
            'valid': valid_count,
            'docs_zip': docs_zip_path
        }
    
    def _process_single_md_file(self, source_file, target_md_dir, target_yml_dir):
        """处理单个MD文件"""
        filename = os.path.basename(source_file)
        
        try:
            # 读取原始文件
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取YAML内容
            yaml_content = self._extract_yaml_from_md(content)
            
            if not yaml_content:
                return {'success': False, 'error': '未找到YAML内容'}
            
            # 验证YAML格式
            try:
                parsed_yaml = yaml.safe_load(yaml_content)
                if not parsed_yaml or 'paths' not in parsed_yaml:
                    return {'success': False, 'error': 'YAML格式无效或缺少paths'}
            except yaml.YAMLError as e:
                return {'success': False, 'error': f'YAML解析错误: {str(e)}'}
            
            # 清洗MD内容
            cleaned_content = self._clean_md_content(content)
            
            # 保存清洗后的MD文件
            target_md_file = os.path.join(target_md_dir, filename)
            with open(target_md_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            # 保存YAML文件
            yml_filename = filename.replace('.md', '.yml')
            target_yml_file = os.path.join(target_yml_dir, yml_filename)
            with open(target_yml_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            return {'success': True, 'yaml_size': len(yaml_content)}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_yaml_from_md(self, content):
        """从MD内容中提取YAML（参考convert_to_postman.py逻辑）"""
        # 查找YAML代码块
        yaml_pattern = r'```ya?ml\n(.*?)\n```'
        matches = re.findall(yaml_pattern, content, re.DOTALL)
        
        if matches:
            return matches[0]
        return None
    
    def _clean_md_content(self, content):
        """清洗MD内容"""
        # 移除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 移除行尾空格
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        return '\n'.join(cleaned_lines)
    
    def stage3_merge_final(self, progress_callback=None):
        """阶段3：最终合并（参考merge_all_directories_fixed.py）"""
        print("\n=== 阶段3：最终合并 ===")
        
        try:
            yml_dir = os.path.join(self.stage2_dir, 'yml')
            
            if not os.path.exists(yml_dir):
                raise Exception(f"阶段2 YAML目录不存在: {yml_dir}")
            
            yml_files = [f for f in os.listdir(yml_dir) if f.endswith('.yml')]
            
            if not yml_files:
                raise Exception(f"阶段2目录中没有YAML文件: {yml_dir}")
            
            print(f"找到 {len(yml_files)} 个YAML文件")
            
            # 按目录分类合并
            categories = self._categorize_by_directory(yml_dir)
            print(f"分类结果: {len(categories)} 个分类")
            
            merged_count = 0
            success_count = 0
            
            for category_name, file_list in categories.items():
                try:
                    print(f"正在合并分类: {category_name} ({len(file_list)} 个文件)")
                    result = self._merge_category_files(category_name, file_list, yml_dir)
                    
                    if result and result.get('success', False):
                        merged_count += 1
                        success_count += 1
                        print(f"✓ 合并成功: {category_name} - {result.get('api_count', 0)} 个API")
                    else:
                        error_msg = result.get('error', '未知错误') if result else '返回结果为空'
                        print(f"✗ 合并失败: {category_name} - {error_msg}")
                        
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(merged_count, len(categories))
                        
                except Exception as e:
                    print(f"合并分类异常 {category_name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            print(f"阶段3完成: 成功合并 {success_count}/{len(categories)} 个分类")
            
            # 返回结果字典
            result = {
                'merged_files': success_count,
                'total_categories': len(categories),
                'final_file': os.path.join(self.final_dir, 'apiall.yaml') if success_count > 0 else None
            }
            
            print(f"返回结果: {result}")
            return result
            
        except Exception as e:
            print(f"阶段3处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
    
    def _categorize_by_directory(self, yml_dir):
        """按目录分类YAML文件（参考merge_by_directory_generate_fixed.py）"""
        directory_mapping = self._get_directory_mapping()
        categories = {}
        
        yml_files = [f for f in os.listdir(yml_dir) if f.endswith('.yml')]
        
        for filename in yml_files:
            file_path = os.path.join(yml_dir, filename)
            
            # 提取YAML内容进行分类
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml_content = f.read()
                
                parsed = yaml.safe_load(yaml_content)
                if not parsed or 'paths' not in parsed:
                    continue
                
                # 根据内容特征进行分类
                category = self._classify_api_content(parsed, filename)
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append(filename)
                
            except Exception as e:
                print(f"分类文件失败 {filename}: {str(e)}")
                # 默认分类
                if 'default' not in categories:
                    categories['default'] = []
                categories['default'].append(filename)
        
        return categories
    
    def _classify_api_content(self, parsed_yaml, filename):
        """根据API内容进行分类"""
        # 简化的分类逻辑，可以根据需要扩展
        paths = parsed_yaml.get('paths', {})
        
        # 根据路径特征分类
        for path in paths.keys():
            if '/chat' in path.lower():
                return '聊天模型'
            elif '/image' in path.lower() or '/vision' in path.lower():
                return '图像处理'
            elif '/audio' in path.lower() or '/speech' in path.lower():
                return '音频处理'
            elif '/embed' in path.lower():
                return '向量嵌入'
            elif '/model' in path.lower():
                return '模型管理'
            elif '/file' in path.lower():
                return '文件处理'
        
        # 根据文件名分类
        filename_lower = filename.lower()
        if 'chat' in filename_lower:
            return '聊天模型'
        elif 'image' in filename_lower or 'vision' in filename_lower:
            return '图像处理'
        elif 'audio' in filename_lower or 'speech' in filename_lower:
            return '音频处理'
        elif 'embed' in filename_lower:
            return '向量嵌入'
        elif 'model' in filename_lower:
            return '模型管理'
        elif 'file' in filename_lower:
            return '文件处理'
        
        return 'default'
    
    def _get_directory_mapping(self):
        """获取目录映射关系（参考merge_by_directory_generate_fixed.py）"""
        return {
            '聊天模型': [
                '列出可用模型', '聊天接口', '聊天补全', 'Claude', 'Gemini', 'GPTs'
            ],
            '图像处理': [
                '图片生成', '图片编辑', '图片分析', 'DALL-E', 'Midjourney'
            ],
            '音频处理': [
                '语音合成', '语音识别', '音频转换', 'TTS', 'STT'
            ],
            '向量嵌入': [
                '文本嵌入', '向量搜索', 'Embedding'
            ],
            '模型管理': [
                '模型列表', '模型信息', '模型配置'
            ],
            '文件处理': [
                '文件上传', '文件下载', '文件分析'
            ]
        }
    
    def _merge_category_files(self, category_name, file_list, yml_dir):
        """合并同一分类的文件"""
        try:
            merged_yaml = {
                'openapi': '3.1.0',
                'info': {
                    'title': f'{category_name} API',
                    'description': f'{category_name}相关的API接口',
                    'version': '1.0.0'
                },
                'servers': [
                    {'url': 'https://api.gpt.ge', 'description': '生产环境'}
                ],
                'paths': {}
            }
            
            # 合并所有文件的paths
            for filename in file_list:
                file_path = os.path.join(yml_dir, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml_content = f.read()
                
                parsed = yaml.safe_load(yaml_content)
                if parsed and 'paths' in parsed:
                    # 合并paths，避免重复
                    for path, methods in parsed['paths'].items():
                        if path not in merged_yaml['paths']:
                            merged_yaml['paths'][path] = methods
                        else:
                            # 合并HTTP方法
                            for method, details in methods.items():
                                merged_yaml['paths'][path][method] = details
            
            # 保存合并后的文件
            output_filename = f"{category_name.replace(' ', '_')}.yml"
            output_path = os.path.join(self.final_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(merged_yaml, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            
            return {
                'success': True,
                'output_file': output_filename,
                'api_count': len(merged_yaml['paths'])
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_processing_stats(self):
        """获取处理统计信息"""
        stats = {
            'stage1': {'md_files': 0},
            'stage2': {'md_files': 0, 'yml_files': 0},
            'final': {'yml_files': 0}
        }
        
        # 阶段1统计
        stage1_md_dir = os.path.join(self.stage1_dir, 'md')
        if os.path.exists(stage1_md_dir):
            stats['stage1']['md_files'] = len([f for f in os.listdir(stage1_md_dir) if f.endswith('.md')])
        
        # 阶段2统计
        stage2_md_dir = os.path.join(self.stage2_dir, 'md')
        stage2_yml_dir = os.path.join(self.stage2_dir, 'yml')
        
        if os.path.exists(stage2_md_dir):
            stats['stage2']['md_files'] = len([f for f in os.listdir(stage2_md_dir) if f.endswith('.md')])
        
        if os.path.exists(stage2_yml_dir):
            stats['stage2']['yml_files'] = len([f for f in os.listdir(stage2_yml_dir) if f.endswith('.yml')])
        
        # 最终统计
        if os.path.exists(self.final_dir):
            stats['final']['yml_files'] = len([f for f in os.listdir(self.final_dir) if f.endswith('.yml')])
        
        return stats
    
    def _copy_docs_to_final(self):
        """复制纯文档MD文件到final/md目录（只复制无法转换为YAML的MD文件）"""
        print("\n=== 复制纯文档MD文件到final/md目录 ===")
        
        # 创建final/md目录
        final_md_dir = os.path.join(self.final_dir, 'md')
        os.makedirs(final_md_dir, exist_ok=True)
        
        copied_count = 0
        
        # 获取已转换为YAML的文件列表
        stage2_yml_dir = os.path.join(self.stage2_dir, 'yml')
        converted_files = set()
        if os.path.exists(stage2_yml_dir):
            for yml_file in os.listdir(stage2_yml_dir):
                if yml_file.endswith('.yml'):
                    # 从YAML文件名推导出对应的MD文件名
                    md_filename = yml_file.replace('.yml', '.md')
                    converted_files.add(md_filename)
        
        print(f"已转换为YAML的文件数量: {len(converted_files)}")
        
        # 从stage1/md目录复制未转换的MD文件（纯文档）
        stage1_md_dir = os.path.join(self.stage1_dir, 'md')
        if os.path.exists(stage1_md_dir):
            for filename in os.listdir(stage1_md_dir):
                if filename.endswith('.md'):
                    # 只复制没有对应YAML文件的MD文件（纯文档）
                    if filename not in converted_files:
                        source_path = os.path.join(stage1_md_dir, filename)
                        target_path = os.path.join(final_md_dir, filename)
                        
                        try:
                            shutil.copy2(source_path, target_path)
                            copied_count += 1
                            print(f"复制纯文档: {filename}")
                        except Exception as e:
                            print(f"复制失败 {filename}: {str(e)}")
                    else:
                        print(f"跳过已转换文档: {filename}")
        else:
            print(f"警告: 阶段1 MD目录不存在 {stage1_md_dir}")
        
        print(f"纯文档复制完成: 共复制 {copied_count} 个纯文档文件到 {final_md_dir}")
    
    def _create_docs_zip(self):
        """创建文档ZIP文件"""
        print("\n=== 创建文档ZIP文件 ===")
        
        final_md_dir = os.path.join(self.final_dir, 'md')
        
        if not os.path.exists(final_md_dir):
            print(f"警告: 文档目录不存在 {final_md_dir}")
            return None
        
        # 生成ZIP文件名（包含时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"apifox_docs_{timestamp}.zip"
        zip_path = os.path.join(self.final_dir, zip_filename)
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 只添加纯文档MD文件到ZIP
                for filename in os.listdir(final_md_dir):
                    if filename.endswith('.md'):
                        file_path = os.path.join(final_md_dir, filename)
                        # 在ZIP中保持相对路径结构
                        arcname = os.path.join('docs', filename)
                        zipf.write(file_path, arcname)
                        print(f"添加纯文档到ZIP: {filename}")
            
            print(f"纯文档ZIP文件创建完成: {zip_path}")
            return zip_filename
            
        except Exception as e:
            print(f"创建ZIP文件失败: {str(e)}")
            return None
    
    def cleanup_intermediate_files(self):
        """清理中间文件"""
        try:
            # 清理阶段1和阶段2的文件
            if os.path.exists(self.stage1_dir):
                shutil.rmtree(self.stage1_dir)
            
            if os.path.exists(self.stage2_dir):
                shutil.rmtree(self.stage2_dir)
            
            print("中间文件清理完成")
            return True
            
        except Exception as e:
            print(f"清理中间文件失败: {str(e)}")
            return False

if __name__ == "__main__":
    # 测试代码
    processor = ApiProcessor("test_data")
    
    try:
        # 获取统计信息
        stats = processor.get_processing_stats()
        print(f"处理统计: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")