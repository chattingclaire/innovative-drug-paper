#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充B6数据提取脚本 - 提取新发现的格式
"""

import os
import re
import pandas as pd
from docx import Document

def extract_missing_b6_data():
    """提取缺失的B6数据"""
    # 读取现有的B6数据
    existing_df = pd.read_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv')
    print(f"现有B6数据: {len(existing_df)}条记录")

    # 新发现的问卷
    new_questionnaires = [91, 92, 93, 94, 95, 96, 98, 99, 100]
    new_data = []

    for questionnaire_num in new_questionnaires:
        file_path = f'01_原始问卷文件/问卷{questionnaire_num:03d}.docx'

        try:
            doc = Document(file_path)
            lines = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    lines.append(paragraph.text.strip())

            print(f"\n处理问卷 {questionnaire_num}...")

            # 查找B6部分
            b6_started = False
            dimension_ranks = {}

            for line in lines:
                if 'B6' in line and '排序' in line:
                    b6_started = True
                    continue

                if b6_started:
                    if 'Part C' in line:
                        break

                    # 格式1: __1_ 安全维度 或 _1__ 安全维度
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

            # 添加到数据中
            if len(dimension_ranks) == 5:
                for dimension, rank in dimension_ranks.items():
                    new_data.append({
                        'questionnaire_num': questionnaire_num,
                        'dimension': dimension,
                        'rank': rank
                    })
                print(f"  ✅ 问卷{questionnaire_num} B6数据完整: {dimension_ranks}")
            else:
                print(f"  ❌ 问卷{questionnaire_num} B6数据不完整: {len(dimension_ranks)}/5个维度")

        except Exception as e:
            print(f"问卷{questionnaire_num} 处理失败: {e}")

    # 合并数据
    if new_data:
        new_df = pd.DataFrame(new_data)
        # 清理维度名称中的下划线
        new_df['dimension'] = new_df['dimension'].str.replace(r'^_+\s*', '', regex=True)

        # 合并现有数据和新数据
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.sort_values(['questionnaire_num', 'dimension']).reset_index(drop=True)

        # 保存合并后的数据
        combined_df.to_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv', index=False, encoding='utf-8-sig')

        print(f"\n=== 数据合并结果 ===")
        print(f"新增数据: {len(new_data)}条记录")
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

        # 统计排序分布
        print("\n排序分布:")
        rank_counts = combined_df['rank'].value_counts().sort_index()
        for rank, count in rank_counts.items():
            print(f"  第{rank}位: {count}次")

    else:
        print("没有找到新的B6数据")

if __name__ == "__main__":
    extract_missing_b6_data()
