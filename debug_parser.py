#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试HTML解析问题
"""

from bs4 import BeautifulSoup

def debug_html_structure():
    """调试HTML结构解析"""
    
    with open("favorites_2025_7_16.html", 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("文件长度:", len(content))
    print("文件开头100字符:")
    print(content[:100])
    print("\n" + "="*50)
    
    soup = BeautifulSoup(content, 'html.parser')
    print("BeautifulSoup解析完成")
    
    # 查找各种可能的DL标签
    dl_tags = soup.find_all('dl')
    print(f"小写dl标签数量: {len(dl_tags)}")
    
    if dl_tags:
        root_dl = dl_tags[0]  # 第一个dl应该是根DL
        print(f"找到根DL标签: {root_dl.name}")
        
        # 查找子元素 - 包括所有类型
        all_children = [child for child in root_dl.children if child.name]
        print(f"根DL下的所有子元素数量: {len(all_children)}")
        
        # 查找直接的dt子元素
        all_dt = root_dl.find_all('dt', recursive=False)
        print(f"根DL下的直接dt子元素数量: {len(all_dt)}")
        
        # 查看根DL的内容结构
        print("\n根DL的前20个子元素:")
        for i, child in enumerate(all_children[:20]):
            if child.name == 'dt':
                h3 = child.find('h3')
                a = child.find('a')
                if h3:
                    print(f"  {i+1}. DT-文件夹: {h3.get_text()}")
                elif a:
                    title = a.get_text()[:50] + "..." if len(a.get_text()) > 50 else a.get_text()
                    print(f"  {i+1}. DT-书签: {title}")
                else:
                    print(f"  {i+1}. DT-其他")
            elif child.name == 'dl':
                print(f"  {i+1}. DL子容器 (可能包含书签)")
            else:
                print(f"  {i+1}. {child.name}")
        
        # 查找所有链接
        all_links = soup.find_all('a')
        print(f"\n整个文档中的链接总数: {len(all_links)}")
        
        # 统计文件夹和书签
        folders = soup.find_all('h3')
        print(f"文件夹数量 (h3标签): {len(folders)}")
        
        # 分析每个文件夹的内容
        if folders:
            print("\n详细文件夹分析:")
            for i, folder in enumerate(folders):
                folder_name = folder.get_text()
                # 找到这个文件夹对应的DL容器
                dt_parent = folder.find_parent('dt')
                if dt_parent:
                    next_dl = dt_parent.find_next_sibling('dl')
                    if next_dl:
                        links_in_folder = next_dl.find_all('a')
                        print(f"  {i+1}. {folder_name}: {len(links_in_folder)}个书签")
                    else:
                        print(f"  {i+1}. {folder_name}: 未找到对应的书签容器")

if __name__ == "__main__":
    debug_html_structure() 