#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from urllib.parse import urljoin, urlparse

class LlmsParser:
    """llms.txt文件解析器"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        
    def parse_llms_content(self, content):
        """解析llms.txt内容，提取所有MD文档链接（包括Docs和API Docs部分）"""
        print("开始解析llms.txt内容...")
        
        # 按行分割内容
        lines = content.strip().split('\n')
        
        # 提取所有MD链接
        all_links = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 检查是否是新的部分标题
            if line.startswith('## '):
                current_section = line[3:].strip()  # 去掉"## "
                print(f"找到部分: {current_section}")
                continue
            
            # 提取当前行的链接
            if line and current_section:
                link_info = self._extract_link_from_line(line)
                if link_info:
                    # 添加部分信息
                    link_info['section'] = current_section
                    all_links.append(link_info)
        
        print(f"解析完成，找到 {len(all_links)} 个文档链接")
        
        # 按部分统计
        section_counts = {}
        for link in all_links:
            section = link.get('section', 'Unknown')
            section_counts[section] = section_counts.get(section, 0) + 1
        
        print("各部分链接统计:")
        for section, count in section_counts.items():
            print(f"  - {section}: {count} 个链接")
        
        # 打印前几个链接作为示例
        if all_links:
            print("前5个链接示例:")
            for i, link in enumerate(all_links[:5]):
                section = link.get('section', 'Unknown')
                print(f"  {i+1}. [{section}] {link['title']} -> {link['url']}")
        
        return all_links
    
    def _extract_link_from_line(self, line):
        """从单行中提取链接信息"""
        # 匹配markdown链接格式: [标题](URL)，允许URL后面有冒号和空格
        markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        match = re.search(markdown_pattern, line)
        
        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
            
            # 清理URL，移除可能的尾部字符
            url = url.rstrip(':').strip()
            
            # 只处理.md文件
            if url.endswith('.md'):
                # 构建完整URL
                if not url.startswith('http'):
                    full_url = urljoin(self.base_url + '/', url)
                else:
                    full_url = url
                
                return {
                    'title': title,
                    'url': url,  # 保留原始相对路径
                    'full_url': full_url,
                    'line': line
                }
        
        # 匹配直接的URL（以.md结尾）
        url_pattern = r'(https?://[^\s]+\.md|[^\s]+\.md)'
        match = re.search(url_pattern, line)
        
        if match:
            url = match.group(1).strip()
            
            # 从URL推断标题
            title = self._extract_title_from_url(url)
            
            # 构建完整URL
            if not url.startswith('http'):
                full_url = urljoin(self.base_url + '/', url)
            else:
                full_url = url
            
            return {
                'title': title,
                'url': url,
                'full_url': full_url,
                'line': line
            }
        
        return None
    
    def _extract_title_from_url(self, url):
        """从URL中提取标题"""
        # 获取文件名（不含扩展名）
        filename = os.path.basename(url)
        if filename.endswith('.md'):
            filename = filename[:-3]
        
        # 替换常见的分隔符为空格
        title = filename.replace('-', ' ').replace('_', ' ')
        
        # 首字母大写
        title = ' '.join(word.capitalize() for word in title.split())
        
        return title or 'Unknown API'
    
    def filter_api_links(self, api_links, filters=None):
        """过滤API链接"""
        if not filters:
            return api_links
        
        filtered_links = []
        
        for link in api_links:
            include = True
            
            # 关键词过滤
            if 'keywords' in filters:
                keywords = filters['keywords']
                if keywords:
                    title_lower = link['title'].lower()
                    url_lower = link['url'].lower()
                    
                    # 检查是否包含任一关键词
                    has_keyword = any(
                        keyword.lower() in title_lower or keyword.lower() in url_lower
                        for keyword in keywords
                    )
                    
                    if not has_keyword:
                        include = False
            
            # URL模式过滤
            if 'url_patterns' in filters and include:
                patterns = filters['url_patterns']
                if patterns:
                    has_pattern = any(
                        re.search(pattern, link['url'], re.IGNORECASE)
                        for pattern in patterns
                    )
                    
                    if not has_pattern:
                        include = False
            
            # 排除模式
            if 'exclude_patterns' in filters and include:
                exclude_patterns = filters['exclude_patterns']
                if exclude_patterns:
                    has_exclude = any(
                        re.search(pattern, link['url'], re.IGNORECASE) or
                        re.search(pattern, link['title'], re.IGNORECASE)
                        for pattern in exclude_patterns
                    )
                    
                    if has_exclude:
                        include = False
            
            if include:
                filtered_links.append(link)
        
        print(f"过滤后剩余 {len(filtered_links)} 个链接")
        return filtered_links
    
    def validate_links(self, api_links):
        """验证链接的有效性"""
        valid_links = []
        invalid_links = []
        
        for link in api_links:
            # 基本验证
            if not link.get('url') or not link.get('title'):
                invalid_links.append({
                    'link': link,
                    'reason': '缺少URL或标题'
                })
                continue
            
            # URL格式验证
            url = link['url']
            if not (url.endswith('.md') and (url.startswith('http') or '/' in url)):
                invalid_links.append({
                    'link': link,
                    'reason': 'URL格式无效'
                })
                continue
            
            # 标题长度验证
            title = link['title']
            if len(title) < 2 or len(title) > 200:
                invalid_links.append({
                    'link': link,
                    'reason': '标题长度异常'
                })
                continue
            
            valid_links.append(link)
        
        print(f"链接验证完成: 有效 {len(valid_links)}, 无效 {len(invalid_links)}")
        
        if invalid_links:
            print("无效链接:")
            for invalid in invalid_links[:5]:  # 只显示前5个
                print(f"  - {invalid['link'].get('title', 'N/A')}: {invalid['reason']}")
        
        return valid_links, invalid_links
    
    def group_links_by_category(self, api_links):
        """根据URL路径对链接进行分组"""
        groups = {}
        
        for link in api_links:
            url = link['url']
            
            # 提取路径中的目录作为分类
            path_parts = url.split('/')
            
            # 寻找有意义的分类标识
            category = 'default'
            
            for part in path_parts:
                if part and part != '..' and not part.endswith('.md'):
                    # 跳过数字ID和常见的无意义目录
                    if not re.match(r'^\d+$', part) and part not in ['api', 'docs', 'md']:
                        category = part
                        break
            
            if category not in groups:
                groups[category] = []
            
            groups[category].append(link)
        
        print(f"链接分组完成: {len(groups)} 个分组")
        for category, links in groups.items():
            print(f"  - {category}: {len(links)} 个链接")
        
        return groups
    
    def export_links_summary(self, api_links, output_file):
        """导出链接摘要到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# API文档链接摘要\n\n")
                f.write(f"总链接数: {len(api_links)}\n")
                f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 按分组导出
                groups = self.group_links_by_category(api_links)
                
                for category, links in groups.items():
                    f.write(f"## {category} ({len(links)} 个)\n\n")
                    
                    for link in links:
                        f.write(f"- [{link['title']}]({link['url']})\n")
                    
                    f.write("\n")
            
            print(f"链接摘要已导出到: {output_file}")
            return True
            
        except Exception as e:
            print(f"导出链接摘要失败: {str(e)}")
            return False

if __name__ == "__main__":
    # 测试代码
    import time
    
    parser = LlmsParser("https://https://doubao.apifox.cn/")
    
    # 测试解析示例内容
    test_content = """
# API Docs

- [用户管理API](api/user/user.md)
- [订单管理API](api/order/order.md)
- [支付接口](api/payment/payment.md)

# Docs

- [使用说明](docs/usage.md)
- [FAQ](docs/faq.md)
"""
    
    try:
        api_links = parser.parse_llms_content(test_content)
        print(f"解析结果: {len(api_links)} 个链接")
        
        for link in api_links:
            print(f"  - {link['title']}: {link['url']}")
        
        # 测试验证
        valid_links, invalid_links = parser.validate_links(api_links)
        print(f"验证结果: 有效 {len(valid_links)}, 无效 {len(invalid_links)}")
        
        # 测试分组
        groups = parser.group_links_by_category(valid_links)
        print(f"分组结果: {len(groups)} 个分组")
        
    except Exception as e:
        print(f"测试失败: {e}")