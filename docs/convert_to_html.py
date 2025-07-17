import sys
import os
import markdown
import pypandoc

def md_to_html(md_path, html_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text, extensions=['extra', 'toc', 'tables'])
    
    # 添加CSS样式，设置字体为仿宋
    html_with_style = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>基于多格式GIS数据的Web地图服务集成平台研究</title>
    <style>
        body {{
            font-family: "FangSong", "仿宋", "SimSun", serif;
            line-height: 1.6;
            margin: 40px;
            background-color: #fff;
        }}
        h1, h2, h3, h4, h5, h6 {{
            font-family: "FangSong", "仿宋", "SimSun", serif;
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }}
        .center {{
            text-align: center;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_with_style)
    print(f"已生成HTML: {html_path}")
    return html_with_style

def md_to_word(md_path, docx_path):
    # 设置pandoc额外参数，指定字体为仿宋
    extra_args = [
        '--reference-doc=template.docx' if os.path.exists('template.docx') else '',
        '--filter=pandoc-crossref',
    ]
    # 过滤空参数
    extra_args = [arg for arg in extra_args if arg]
    
    try:
        output = pypandoc.convert_file(
            md_path, 
            'docx', 
            outputfile=docx_path,
            extra_args=extra_args
        )
    except:
        # 如果带参数转换失败，回退到基本转换
        output = pypandoc.convert_file(md_path, 'docx', outputfile=docx_path)
    
    print(f"已生成Word文档: {docx_path}")
    print("提示：Word文档字体需要在Word中手动设置为仿宋，或使用模板文档")
    return output

def main():
    if len(sys.argv) < 2:
        print("用法: python convert_to_html.py <md文件路径>")
        return
    md_path = sys.argv[1]
    base = os.path.splitext(md_path)[0]
    html_path = base + '.html'
    docx_path = base + '.docx'
    md_to_html(md_path, html_path)
    md_to_word(md_path, docx_path)

if __name__ == '__main__':
    main() 