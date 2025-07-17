import sys
import os
import markdown
import pypandoc

def md_to_html(md_path, html_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    html = markdown.markdown(text, extensions=['extra', 'toc', 'tables'])
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"已生成HTML: {html_path}")
    return html

def md_to_word(md_path, docx_path):
    output = pypandoc.convert_file(md_path, 'docx', outputfile=docx_path)
    print(f"已生成Word文档: {docx_path}")
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