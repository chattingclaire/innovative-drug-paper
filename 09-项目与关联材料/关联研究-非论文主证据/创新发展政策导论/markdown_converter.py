from docx import Document
import os

def convert_table_to_markdown(table):
    """
    将Word表格转换为Markdown格式
    
    @param {Table} table - Word文档中的表格对象
    @return {string} - 转换后的markdown表格文本
    """
    markdown_table = []
    
    # 添加表头
    header = '|'
    separator = '|'
    for cell in table.rows[0].cells:
        header += f" {cell.text.strip()} |"
        separator += ' --- |'
    markdown_table.append(header)
    markdown_table.append(separator)
    
    # 添加表格内容
    for row in table.rows[1:]:
        row_text = '|'
        for cell in row.cells:
            row_text += f" {cell.text.strip()} |"
        markdown_table.append(row_text)
    
    return '\n'.join(markdown_table) + '\n\n'

def convert_docx_to_markdown(input_file, output_file):
    """
    将Word文档转换为Markdown格式，包括表格转换
    
    @param {string} input_file - 输入的Word文档路径
    @param {string} output_file - 输出的Markdown文件路径
    """
    # 打开Word文档
    doc = Document(input_file)
    
    # 创建markdown内容
    markdown_content = []
    
    # 遍历文档中的所有元素
    for element in doc.element.body:
        # 处理段落
        if isinstance(element, Document._Document):
            for paragraph in doc.paragraphs:
                if paragraph.style.name.startswith('Heading'):
                    level = paragraph.style.name[-1]
                    markdown_content.append('#' * int(level) + ' ' + paragraph.text + '\n\n')
                elif paragraph.text.strip():
                    markdown_content.append(paragraph.text + '\n\n')
        
        # 处理表格
        for table in doc.tables:
            markdown_content.append(convert_table_to_markdown(table))
    
    # 写入markdown文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(markdown_content)

def main():
    input_path = "/Users/moonshot/Desktop/生产ppt/创新药领域政策工具与实施效果研究报告.docx"
    output_path = "/Users/moonshot/Desktop/生产ppt/创新药领域政策工具与实施效果研究报告.md"
    
    try:
        convert_docx_to_markdown(input_path, output_path)
        print(f"转换成功！Markdown文件已保存至: {output_path}")
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main() 