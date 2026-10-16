#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查副本B6数据脚本
"""

import os
import re
import pandas as pd
from docx import Document

def check_copy_questionnaire_b6(questionnaire_num):
    """检查副本问卷的B6数据"""
    file_path = f'01_原始问卷文件/副本问卷{questionnaire_num:03d}.docx'

    if not os.path.exists(file_path):
        print(f"副本问卷{questionnaire_num}: 文件不存在")
        return False, {}

    try:
        doc = Document(file_path)
        lines = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                lines.append(paragraph.text.strip())

        print(f"\n=== 副本问卷{questionnaire_num} ===")

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
        dimension_ranks = {}
        for line in b6_lines:
            # 检查各种排序格式
            # 格式1: _1_ 安全维度 或 __2_ 安全维度
            match1 = re.match(r'_+(\d+)_+\s*(.+)', line)
            if match1:
                rank = int(match1.group(1))
                dimension = match1.group(2).strip()
                dimension_ranks[dimension] = rank
                print(f"  格式1: {line} -> {dimension}: {rank}")
                continue

            # 格式2: ___ 安全维度1 (数字在维度名后面)
            match2 = re.match(r'_+\s*(.+?)(\d+)$', line)
            if match2:
                dimension = match2.group(1).strip()
                rank = int(match2.group(2))
                dimension_ranks[dimension] = rank
                print(f"  格式2: {line} -> {dimension}: {rank}")
                continue

            # 格式3: 1___ 安全维度 (数字在前，下划线在后)
            match3 = re.match(r'(\d+)_+\s*(.+)', line)
            if match3:
                rank = int(match3.group(1))
                dimension = match3.group(2).strip()
                dimension_ranks[dimension] = rank
                print(f"  格式3: {line} -> {dimension}: {rank}")
                continue

        if len(dimension_ranks) == 5:
            print(f"✅ 副本问卷{questionnaire_num} 有完整B6排序数据: {dimension_ranks}")
            return True, dimension_ranks
        else:
            print(f"❌ 副本问卷{questionnaire_num} B6数据不完整: {len(dimension_ranks)}/5个维度")
            return False, dimension_ranks

    except Exception as e:
        print(f"副本问卷{questionnaire_num} 读取失败: {e}")
        return False, {}

def main():
    """主函数"""
    copy_questionnaires = [29, 71, 73]

    print("检查副本问卷的B6数据...")

    found_data = []
    new_b6_data = []

    for num in copy_questionnaires:
        has_data, dimension_ranks = check_copy_questionnaire_b6(num)
        if has_data:
            found_data.append(num)
            # 添加到新数据中
            for dimension, rank in dimension_ranks.items():
                new_b6_data.append({
                    'questionnaire_num': num,
                    'dimension': dimension,
                    'rank': rank
                })

    print(f"\n=== 检查结果 ===")
    print(f"有B6数据的副本问卷: {found_data}")

    if new_b6_data:
        print(f"找到 {len(new_b6_data)} 条新的B6数据")

        # 读取现有数据并合并
        existing_df = pd.read_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv')
        new_df = pd.DataFrame(new_b6_data)

        # 清理维度名称中的下划线
        new_df['dimension'] = new_df['dimension'].str.replace(r'^_+\s*', '', regex=True)

        # 合并数据
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.sort_values(['questionnaire_num', 'dimension']).reset_index(drop=True)

        # 保存合并后的数据
        combined_df.to_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv', index=False, encoding='utf-8-sig')

        print(f"合并后总数据: {len(combined_df)}条记录")

        # 统计问卷数量
        questionnaire_counts = combined_df['questionnaire_num'].value_counts()
        print(f"包含B6数据的问卷数量: {len(questionnaire_counts)}个")

        # 检查数据完整性
        incomplete_questionnaires = []
        for questionnaire_num in range(1, 101):
            count = questionnaire_counts.get(questionnaire_num, 0)
            if count != 5:
                incomplete_questionnaires.append(questionnaire_num)

        if incomplete_questionnaires:
            print(f"数据不完整的问卷: {incomplete_questionnaires}")
        else:
            print("🎉 所有问卷的B6数据都完整！")
    else:
        print("没有找到新的B6数据")

if __name__ == "__main__":
    main()
