#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缺失B6问卷详细脚本
"""

import os
import re
from docx import Document

def check_questionnaire_b6(questionnaire_num):
    """检查单个问卷的B6数据"""
    file_path = f'01_原始问卷文件/问卷{questionnaire_num:03d}.docx'

    if not os.path.exists(file_path):
        print(f"问卷{questionnaire_num}: 文件不存在")
        return False

    try:
        doc = Document(file_path)
        lines = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                lines.append(paragraph.text.strip())

        print(f"\n=== 问卷{questionnaire_num} ===")

        # 查找B6部分
        b6_started = False
        b6_lines = []

        for i, line in enumerate(lines):
            if 'B6' in line and '排序' in line:
                b6_started = True
                print(f"找到B6排序题开始: {line}")
                continue

            if b6_started:
                if 'Part C' in line:
                    break
                b6_lines.append(line)

        print(f"B6部分内容 ({len(b6_lines)}行):")
        for i, line in enumerate(b6_lines):
            print(f"  {i+1}: {line}")

        # 检查是否有排序数据
        has_ranking = False
        for line in b6_lines:
            # 检查各种排序格式
            if re.search(r'[1-5]', line) and ('维度' in line or '安全' in line or '有效' in line or '经济' in line or '创新' in line or '公平' in line):
                has_ranking = True
                break

        if has_ranking:
            print(f"✅ 问卷{questionnaire_num} 有B6排序数据")
        else:
            print(f"❌ 问卷{questionnaire_num} 没有B6排序数据")

        return has_ranking

    except Exception as e:
        print(f"问卷{questionnaire_num} 读取失败: {e}")
        return False

def main():
    """主函数"""
    missing_questionnaires = [29, 71, 73, 91, 92, 93, 94, 95, 96, 98, 99, 100]

    print("检查缺失B6数据的12个问卷...")

    found_data = []
    no_data = []

    for num in missing_questionnaires:
        has_data = check_questionnaire_b6(num)
        if has_data:
            found_data.append(num)
        else:
            no_data.append(num)

    print(f"\n=== 检查结果 ===")
    print(f"有B6数据的问卷: {found_data}")
    print(f"没有B6数据的问卷: {no_data}")
    print(f"总计: {len(found_data)}个有数据, {len(no_data)}个无数据")

if __name__ == "__main__":
    main()
