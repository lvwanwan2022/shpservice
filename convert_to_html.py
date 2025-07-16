#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown文档转换为HTML的简化工具
"""

import os
import re
import markdown
from pathlib import Path
from jinja2 import Template
from datetime import datetime
import base64
import mimetypes

class MarkdownToHTML:
    def __init__(self, input_file, output_dir="output"):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 读取Markdown内容
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.md_content = f.read()
        
        # 配置Markdown扩展
        self.md = markdown.Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code'
            ],
            extension_configs={
                'markdown.extensions.codehilite': {
                    'css_class': 'highlight'
                },
                'markdown.extensions.toc': {
                    'toc_depth': 4
                }
            }
        )
    
    def process_images(self, content):
        """处理图片路径，将相对路径转换为base64编码"""
        def replace_image(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # 相对路径转换为绝对路径
            if not img_path.startswith(('http://', 'https://', 'data:')):
                abs_path = self.input_file.parent / img_path
                if abs_path.exists():
                    try:
                        # 转换为base64编码
                        with open(abs_path, 'rb') as img_file:
                            img_data = img_file.read()
                            mime_type, _ = mimetypes.guess_type(str(abs_path))
                            if mime_type:
                                b64_data = base64.b64encode(img_data).decode()
                                img_path = f"data:{mime_type};base64,{b64_data}"
                            else:
                                print(f"无法识别图片类型: {abs_path}")
                    except Exception as e:
                        print(f"处理图片失败 {abs_path}: {e}")
                else:
                    print(f"图片文件不存在: {abs_path}")
            
            return f"![{alt_text}]({img_path})"
        
        # 匹配Markdown图片语法
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(pattern, replace_image, content)
    
    def get_html_template(self):
        """获取HTML模板"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Source Han Sans CN", 
                         "Noto Sans CJK SC", "WenQuanYi Micro Hei", Arial, sans-serif;
            line-height: 1.7;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #fff;
            color: #333;
            font-size: 16px;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 2.5em;
            margin-bottom: 1em;
            font-weight: 600;
            line-height: 1.3;
        }
        
        h1 {
            font-size: 2.8em;
            border-bottom: 4px solid #3498db;
            padding-bottom: 0.5em;
            text-align: center;
            margin-bottom: 2em;
            margin-top: 0;
            page-break-after: avoid;
        }
        
        h2 {
            font-size: 2.2em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.3em;
            margin-top: 3em;
            page-break-after: avoid;
        }
        
        h3 {
            font-size: 1.8em;
            color: #2980b9;
            border-left: 4px solid #3498db;
            padding-left: 20px;
            page-break-after: avoid;
        }
        
        h4 {
            font-size: 1.4em;
            color: #34495e;
            margin-top: 2em;
            page-break-after: avoid;
        }
        
        h5 {
            font-size: 1.2em;
            color: #5a6c7d;
            page-break-after: avoid;
        }
        
        h6 {
            font-size: 1.1em;
            color: #6c7b7f;
            page-break-after: avoid;
        }
        
        p {
            margin-bottom: 1.2em;
            text-align: justify;
            text-justify: inter-ideograph;
            line-height: 1.8;
        }
        
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 30px auto;
            border-radius: 8px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            page-break-inside: avoid;
        }
        
        /* 图片说明样式 */
        p:has(> strong:only-child) {
            text-align: center;
            font-size: 0.9em;
            color: #666;
            margin-top: -20px;
            margin-bottom: 30px;
            font-style: italic;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            background-color: #fff;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
            page-break-inside: avoid;
        }
        
        th, td {
            border: 1px solid #e0e0e0;
            padding: 15px 12px;
            text-align: left;
            vertical-align: top;
        }
        
        th {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            font-weight: 600;
            font-size: 0.95em;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f4f8;
            transition: background-color 0.3s ease;
        }
        
        code {
            background-color: #f1f3f4;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: "Consolas", "Monaco", "Source Code Pro", "Courier New", monospace;
            font-size: 0.9em;
            color: #d73a49;
            border: 1px solid #e1e4e8;
        }
        
        pre {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 25px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 30px 0;
            border-left: 4px solid #3498db;
            page-break-inside: avoid;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
            color: inherit;
            border: none;
            font-size: 0.9em;
        }
        
        blockquote {
            border-left: 5px solid #3498db;
            margin: 30px 0;
            padding: 15px 25px;
            background-color: #f8f9fa;
            font-style: italic;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        ul, ol {
            margin-bottom: 1.5em;
            padding-left: 2.5em;
        }
        
        li {
            margin-bottom: 0.8em;
            line-height: 1.7;
        }
        
        li ul, li ol {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }
        
        .toc {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border: 2px solid #dee2e6;
            border-radius: 12px;
            padding: 25px;
            margin: 30px 0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .toc h2 {
            margin-top: 0;
            color: #495057;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc > ul > li {
            margin: 8px 0;
        }
        
        .toc ul ul {
            padding-left: 20px;
            margin-top: 5px;
        }
        
        .toc a {
            text-decoration: none;
            color: #3498db;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .toc a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        .footer {
            margin-top: 4em;
            padding-top: 2em;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }
        
        .highlight {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1.5em;
            margin: 1.5em 0;
            border-left: 4px solid #17a2b8;
        }
        
        /* 强调样式 */
        strong {
            color: #2c3e50;
            font-weight: 600;
        }
        
        em {
            color: #34495e;
            font-style: italic;
        }
        
        /* 链接样式 */
        a {
            color: #3498db;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        a:hover {
            color: #2980b9;
            text-decoration: underline;
        }
        
        /* 打印样式 */
        @media print {
            body {
                padding: 0;
                background-color: white;
                font-size: 12pt;
                line-height: 1.5;
            }
            
            h1 {
                font-size: 24pt;
            }
            
            h2 {
                font-size: 20pt;
            }
            
            h3 {
                font-size: 16pt;
            }
            
            h4 {
                font-size: 14pt;
            }
            
            img {
                max-width: 100%;
                page-break-inside: avoid;
                box-shadow: none;
            }
            
            h1, h2, h3, h4, h5, h6 {
                page-break-after: avoid;
            }
            
            table, blockquote, pre {
                page-break-inside: avoid;
            }
            
            .footer {
                page-break-before: always;
            }
        }
        
        /* 移动端样式 */
        @media (max-width: 768px) {
            body {
                padding: 15px;
                font-size: 14px;
            }
            
            h1 {
                font-size: 2.2em;
            }
            
            h2 {
                font-size: 1.8em;
            }
            
            h3 {
                font-size: 1.5em;
                padding-left: 15px;
            }
            
            h4 {
                font-size: 1.3em;
            }
            
            table {
                font-size: 12px;
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }
            
            th, td {
                padding: 10px 8px;
            }
            
            .toc {
                padding: 15px;
            }
            
            pre {
                padding: 15px;
                font-size: 13px;
            }
        }
        
        /* 小屏幕设备 */
        @media (max-width: 480px) {
            body {
                padding: 10px;
                font-size: 13px;
            }
            
            h1 {
                font-size: 1.8em;
            }
            
            h2 {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        {{ content }}
        <div class="footer">
            <p><strong>生成时间:</strong> {{ timestamp }}</p>
            <p><strong>转换工具:</strong> Markdown Converter v1.0</p>
            <p><em>本文档由Markdown自动转换生成</em></p>
        </div>
    </div>
    
    <script>
        // 为表格添加响应式滚动
        document.addEventListener('DOMContentLoaded', function() {
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                const wrapper = document.createElement('div');
                wrapper.style.overflowX = 'auto';
                wrapper.style.marginBottom = '20px';
                table.parentNode.insertBefore(wrapper, table);
                wrapper.appendChild(table);
            });
        });
    </script>
</body>
</html>"""
    
    def convert(self):
        """转换为HTML格式"""
        print("开始处理Markdown文档...")
        
        # 处理图片
        print("正在处理图片...")
        processed_content = self.process_images(self.md_content)
        
        # 转换为HTML
        print("正在转换为HTML...")
        html_content = self.md.convert(processed_content)
        
        # 提取标题
        title = "研究文档"
        lines = self.md_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        
        print(f"文档标题: {title}")
        
        # 使用模板
        template = Template(self.get_html_template())
        final_html = template.render(
            title=title,
            content=html_content,
            timestamp=datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        )
        
        # 保存HTML文件
        output_file = self.output_dir / f"{self.input_file.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        print(f"✅ HTML文件已生成: {output_file}")
        
        # 显示文件大小
        file_size = output_file.stat().st_size
        print(f"📄 文件大小: {file_size / 1024:.1f} KB")
        
        return output_file

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python convert_to_html.py <markdown文件> [输出目录]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    if not Path(input_file).exists():
        print(f"❌ 错误: 文件 {input_file} 不存在")
        sys.exit(1)
    
    converter = MarkdownToHTML(input_file, output_dir)
    converter.convert() 