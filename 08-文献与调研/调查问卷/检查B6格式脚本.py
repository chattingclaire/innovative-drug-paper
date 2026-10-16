#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查B6格式脚本
"""

from docx import Document

def check_b6_format():
    """检查B6排序题的格式"""
    print("="*60)
    print("检查B6排序题格式")
    print("="*60)

    # 检查问卷1的B6格式
    doc = Document("01_原始问卷文件/问卷001.docx")
    lines = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            lines.append(paragraph.text.strip())

    print("问卷1的内容:")
    for i, line in enumerate(lines):
        if 'B6' in line or '排序' in line or '维度' in line:
            print(f"行 {i+1}: {line}")
            # 显示接下来几行
            for j in range(1, 10):
                if i + j < len(lines):
                    print(f"行 {i+j+1}: {lines[i+j]}")
                else:
                    break
            break

if __name__ == "__main__":
    check_b6_format()
