from docx import Document

# 创建新文档
doc = Document()

# 设置默认字体为仿宋
style = doc.styles['Normal']
font = style.font
font.name = 'FangSong'

# 设置标题样式
for i in range(1, 7):
    try:
        heading_style = doc.styles[f'Heading {i}']
        heading_font = heading_style.font
        heading_font.name = 'FangSong'
    except:
        pass

# 保存模板
doc.save('template.docx')
print('已创建仿宋字体模板文档: template.docx') 