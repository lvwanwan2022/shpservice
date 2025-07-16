#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
书签分类器 - 按行号重新分类第11-291行的书签
将没有分类的书签根据内容主题归类到不同文件夹
"""

import re
from bs4 import BeautifulSoup
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def classify_bookmark(title, url):
    """根据书签标题和URL分类"""
    title_lower = title.lower()
    url_lower = url.lower()
    
    # 分类规则
    categories = {
        '前端开发': [
            'w3schools', 'html', 'css', 'javascript', 'vue', 'element', 'frontend',
            'web', 'bootstrap', 'jquery', 'react', 'angular', '前端', 'ui'
        ],
        '后端开发': [
            'python', 'c#', 'csharp', 'dotnet', '.net', 'api', 'flask', 'django',
            'java', 'php', 'node', 'express', 'backend', '后端', 'server'
        ],
        '编程与开发': [
            'github', 'gitee', 'programming', 'code', 'tutorial', 'csdn', 'blog',
            'stackoverflow', 'coding', '教程', '编程', '开发', 'fortran'
        ],
        'GIS与空间数据': [
            'gis', 'qgis', 'arcgis', 'spatial', 'map', 'geometry', 'rhino', 'grasshopper',
            'autocad', 'bentley', '地理', '空间', '制图', 'osgeo', 'ifc'
        ],
        '学习资源': [
            'mooc', 'course', 'learn', 'study', 'education', 'training', 'tutorial',
            '学习', '教学', '课程', '培训', 'university', 'college'
        ],
        '设计与创意': [
            'design', 'template', 'ppt', 'creative', 'art', 'wallpaper', 'icon',
            '设计', '模板', '创意', '艺术', '壁纸'
        ],
        '工具与资源': [
            'tool', 'utility', 'resource', 'download', 'free', 'search', 'converter',
            '工具', '资源', '导航', '搜索', '下载', '免费'
        ],
        '项目管理': [
            'project', 'management', 'team', 'collaboration', 'workflow', 'task',
            '项目', '管理', '协作', '工作流'
        ],
        '建筑工程': [
            'revit', 'bim', 'architecture', 'engineering', 'construction', 'cad',
            '建筑', '工程', '施工', 'hec-ras', 'hecras', '水利'
        ],
        '媒体娱乐': [
            'youtube', 'video', 'media', 'entertainment', 'music', 'movie',
            '视频', '娱乐', '媒体', '音乐', '电影'
        ],
        '文档与知识管理': [
            'document', 'wiki', 'knowledge', 'note', 'yuque', 'markdown',
            '文档', '知识', '笔记', '语雀'
        ],
        '科研学术': [
            'research', 'academic', 'paper', 'scholar', 'science', 'publication',
            '科研', '学术', '论文', '科学', 'sci-hub', 'connected'
        ]
    }
    
    # 检查每个分类的关键词
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title_lower or keyword in url_lower:
                return category
    
    return '其他'

def reorganize_bookmarks_by_lines():
    """重新组织第11-291行的书签"""
    input_file = 'favorites_2025_7_16.html'
    output_file = 'favorites_2025_7_16_整理后_分类报告.txt'
    
    try:
        # 读取HTML文件
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        logging.info(f"HTML文件总行数: {len(lines)}")
        
        # 提取第11-291行的书签
        bookmarks_to_classify = []
        
        for line_num in range(10, min(291, len(lines))):  # 第11行对应索引10
            line = lines[line_num].strip()
            
            # 检查是否是书签行
            if line.startswith('<DT><A HREF='):
                # 解析书签信息
                try:
                    soup = BeautifulSoup(line, 'html.parser')
                    link = soup.find('a')
                    if link:
                        url = link.get('href', '')
                        title = link.get_text(strip=True)
                        add_date = link.get('add_date', '')
                        icon = link.get('icon', '')
                        
                        if title and url:
                            bookmarks_to_classify.append({
                                'line_num': line_num + 1,  # 行号从1开始
                                'title': title,
                                'url': url,
                                'add_date': add_date,
                                'icon': icon,
                                'original_line': line
                            })
                except Exception as e:
                    logging.warning(f"解析第{line_num + 1}行失败: {e}")
                    continue
        
        logging.info(f"提取到 {len(bookmarks_to_classify)} 个书签需要分类")
        
        # 分类书签
        classified_bookmarks = {}
        
        for bookmark in bookmarks_to_classify:
            category = classify_bookmark(bookmark['title'], bookmark['url'])
            
            if category not in classified_bookmarks:
                classified_bookmarks[category] = []
            
            classified_bookmarks[category].append(bookmark)
        
        # 生成分类报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("书签分类报告 (第11-291行)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"总计处理书签: {len(bookmarks_to_classify)} 个\n")
            f.write(f"分类数量: {len(classified_bookmarks)} 个\n\n")
            
            # 按分类输出
            for category, bookmarks in sorted(classified_bookmarks.items()):
                f.write(f"\n【{category}】 ({len(bookmarks)} 个书签)\n")
                f.write("-" * 60 + "\n")
                
                for i, bookmark in enumerate(bookmarks, 1):
                    f.write(f"{i:2d}. 行号: {bookmark['line_num']:3d} | {bookmark['title'][:60]}\n")
                    f.write(f"    URL: {bookmark['url'][:80]}\n")
                    if len(bookmark['url']) > 80:
                        f.write(f"         {bookmark['url'][80:]}\n")
                    f.write("\n")
        
        # 生成重新组织的HTML文件
        output_html = 'favorites_2025_7_16_整理后.html'
        
        # 复制原始文件到新文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 找到书签列表的根DL标签
        root_dl = soup.find('dl')
        if root_dl:
            # 移除第11-291行对应的书签
            bookmarks_removed = 0
            for dt in root_dl.find_all('dt', recursive=False):
                link = dt.find('a')
                if link and not dt.find('h3'):  # 只移除直接的书签，不移除文件夹
                    dt.decompose()
                    bookmarks_removed += 1
            
            logging.info(f"移除了 {bookmarks_removed} 个未分类书签")
            
            # 在文件开头添加分类后的书签
            for category, bookmarks in sorted(classified_bookmarks.items()):
                # 创建文件夹
                folder_dt = soup.new_tag('dt')
                folder_h3 = soup.new_tag('h3', attrs={
                    'add_date': '1732534809',
                    'last_modified': '1732534809'
                })
                folder_h3.string = category
                folder_dt.append(folder_h3)
                
                # 创建文件夹内容
                folder_dl = soup.new_tag('dl')
                folder_dl.append(soup.new_tag('p'))
                
                # 添加书签到文件夹
                for bookmark in bookmarks:
                    bookmark_dt = soup.new_tag('dt')
                    bookmark_a = soup.new_tag('a', attrs={
                        'href': bookmark['url'],
                        'add_date': bookmark['add_date'],
                    })
                    if bookmark['icon']:
                        bookmark_a['icon'] = bookmark['icon']
                    
                    bookmark_a.string = bookmark['title']
                    bookmark_dt.append(bookmark_a)
                    folder_dl.append(bookmark_dt)
                
                folder_dl.append(soup.new_tag('p'))
                folder_dt.append(folder_dl)
                
                # 插入到根DL的开头
                first_child = root_dl.find()
                if first_child:
                    first_child.insert_before(folder_dt)
                else:
                    root_dl.append(folder_dt)
        
        # 保存整理后的HTML
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"分类报告已保存到: {output_file}")
        logging.info(f"整理后的HTML已保存到: {output_html}")
        
        # 输出统计信息
        print("\n书签分类统计:")
        print("=" * 50)
        for category, bookmarks in sorted(classified_bookmarks.items()):
            print(f"{category}: {len(bookmarks)} 个书签")
        print(f"\n总计: {len(bookmarks_to_classify)} 个书签已重新分类")
        
        return True
        
    except Exception as e:
        logging.error(f"处理失败: {e}")
        return False

if __name__ == "__main__":
    print("开始重新分类第11-291行的书签...")
    
    success = reorganize_bookmarks_by_lines()
    
    if success:
        print("\n✅ 书签分类完成！")
        print("\n生成的文件:")
        print("1. favorites_2025_7_16_整理后.html - 重新分类后的书签文件")
        print("2. favorites_2025_7_16_整理后_分类报告.txt - 详细分类报告")
    else:
        print("\n❌ 书签分类失败，请检查错误信息") 