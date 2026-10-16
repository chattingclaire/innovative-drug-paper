#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复问卷71B6数据脚本
"""

import os
import re
import pandas as pd
from docx import Document

def fix_questionnaire_71_b6():
    """修复问卷71的B6数据"""
    file_path = '01_原始问卷文件/副本问卷071.docx'

    try:
        doc = Document(file_path)
        lines = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                lines.append(paragraph.text.strip())

        print("=== 修复问卷71 B6数据 ===")

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

                # 格式2: ___4 公平维度 (数字在中间，前后都有下划线)
                match2 = re.match(r'_+(\d+)\s*(.+)', line)
                if match2:
                    rank = int(match2.group(1))
                    dimension = match2.group(2).strip()
                    dimension_ranks[dimension] = rank
                    print(f"  格式2: {line} -> {dimension}: {rank}")
                    continue

        print(f"问卷71 B6数据: {dimension_ranks}")

        if len(dimension_ranks) == 5:
            # 添加到数据中
            new_data = []
            for dimension, rank in dimension_ranks.items():
                new_data.append({
                    'questionnaire_num': 71,
                    'dimension': dimension,
                    'rank': rank
                })

            # 读取现有数据并合并
            existing_df = pd.read_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv')
            new_df = pd.DataFrame(new_data)

            # 清理维度名称中的下划线
            new_df['dimension'] = new_df['dimension'].str.replace(r'^_+\s*', '', regex=True)

            # 合并数据
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.sort_values(['questionnaire_num', 'dimension']).reset_index(drop=True)

            # 保存合并后的数据
            combined_df.to_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv', index=False, encoding='utf-8-sig')

            print(f"✅ 问卷71 B6数据已修复并合并")
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
            print(f"❌ 问卷71 B6数据仍然不完整: {len(dimension_ranks)}/5个维度")

    except Exception as e:
        print(f"处理问卷71失败: {e}")

if __name__ == "__main__":
    fix_questionnaire_71_b6()
