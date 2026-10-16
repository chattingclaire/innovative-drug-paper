#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据去重脚本 - 确保每个问题只有100条记录
"""

import pandas as pd

def deduplicate_data():
    """去重数据，确保每个问题只有100条记录"""
    print("="*60)
    print("数据去重处理")
    print("="*60)

    # 处理Part A数据
    print("\n处理Part A数据...")
    df_a = pd.read_csv('最终格式差异_PARTA_问卷数据.csv')

    # 按问卷编号和问题编号去重，保留第一个
    df_a_dedup = df_a.drop_duplicates(subset=['questionnaire_num', 'question_num'], keep='first')

    print(f"原始记录数: {len(df_a)}")
    print(f"去重后记录数: {len(df_a_dedup)}")

    # 检查每个问题的记录数
    question_counts = df_a_dedup['question_num'].value_counts().sort_index()
    print("去重后每个问题的记录数:")
    for question, count in question_counts.items():
        print(f"  {question}: {count}条")

    # 保存去重后的数据
    df_a_dedup.to_csv('去重后_PARTA_问卷数据.csv', index=False, encoding='utf-8-sig')
    print("Part A去重数据已保存")

    # 处理Part B数据
    print("\n处理Part B数据...")
    df_b = pd.read_csv('最终格式差异_PARTB_问卷数据.csv')

    # 按问卷编号和问题编号去重，保留第一个
    df_b_dedup = df_b.drop_duplicates(subset=['questionnaire_num', 'question_num'], keep='first')

    print(f"原始记录数: {len(df_b)}")
    print(f"去重后记录数: {len(df_b_dedup)}")

    # 检查每个问题的记录数
    question_counts_b = df_b_dedup['question_num'].value_counts().sort_index()
    print("去重后每个问题的记录数:")
    for question, count in question_counts_b.items():
        print(f"  {question}: {count}条")

    # 保存去重后的数据
    df_b_dedup.to_csv('去重后_PARTB_问卷数据.csv', index=False, encoding='utf-8-sig')
    print("Part B去重数据已保存")

    # 处理Part C数据
    print("\n处理Part C数据...")
    df_c = pd.read_csv('最终格式差异_PARTC_问卷数据.csv')

    # 按问卷编号和问题编号去重，保留第一个
    df_c_dedup = df_c.drop_duplicates(subset=['questionnaire_num', 'question_num'], keep='first')

    print(f"原始记录数: {len(df_c)}")
    print(f"去重后记录数: {len(df_c_dedup)}")

    # 检查每个问题的记录数
    question_counts_c = df_c_dedup['question_num'].value_counts().sort_index()
    print("去重后每个问题的记录数:")
    for question, count in question_counts_c.items():
        print(f"  {question}: {count}条")

    # 保存去重后的数据
    df_c_dedup.to_csv('去重后_PARTC_问卷数据.csv', index=False, encoding='utf-8-sig')
    print("Part C去重数据已保存")

    print("\n" + "="*60)
    print("数据去重完成！")
    print("="*60)
    print("生成的文件:")
    print("- 去重后_PARTA_问卷数据.csv")
    print("- 去重后_PARTB_问卷数据.csv")
    print("- 去重后_PARTC_问卷数据.csv")

if __name__ == "__main__":
    deduplicate_data()
