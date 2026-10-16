#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据完整性脚本
"""

import pandas as pd

def check_data_integrity():
    """检查数据完整性"""
    print("="*60)
    print("数据完整性检查")
    print("="*60)

    # 检查Part A数据
    print("\nPart A数据检查:")
    print("-" * 40)
    df_a = pd.read_csv('最终格式差异_PARTA_问卷数据.csv')

    # 统计每个问题的记录数
    question_counts = df_a['question_num'].value_counts().sort_index()
    print("每个问题的记录数:")
    for question, count in question_counts.items():
        print(f"  {question}: {count}条")

    # 检查问卷数量
    questionnaire_counts = df_a['questionnaire_num'].value_counts().sort_index()
    print(f"\n问卷数量: {len(questionnaire_counts)}个")
    print(f"总记录数: {len(df_a)}条")

    # 检查是否有重复记录
    print(f"\n是否有重复记录: {df_a.duplicated().any()}")
    if df_a.duplicated().any():
        print(f"重复记录数: {df_a.duplicated().sum()}")

    # 检查Part B数据
    print("\nPart B数据检查:")
    print("-" * 40)
    df_b = pd.read_csv('最终格式差异_PARTB_问卷数据.csv')

    # 统计每个问题的记录数
    question_counts_b = df_b['question_num'].value_counts().sort_index()
    print("每个问题的记录数:")
    for question, count in question_counts_b.items():
        print(f"  {question}: {count}条")

    # 检查问卷数量
    questionnaire_counts_b = df_b['questionnaire_num'].value_counts().sort_index()
    print(f"\n问卷数量: {len(questionnaire_counts_b)}个")
    print(f"总记录数: {len(df_b)}条")

    # 检查是否有重复记录
    print(f"\n是否有重复记录: {df_b.duplicated().any()}")
    if df_b.duplicated().any():
        print(f"重复记录数: {df_b.duplicated().sum()}")

    # 检查Part C数据
    print("\nPart C数据检查:")
    print("-" * 40)
    df_c = pd.read_csv('最终格式差异_PARTC_问卷数据.csv')

    # 统计每个问题的记录数
    question_counts_c = df_c['question_num'].value_counts().sort_index()
    print("每个问题的记录数:")
    for question, count in question_counts_c.items():
        print(f"  {question}: {count}条")

    # 检查问卷数量
    questionnaire_counts_c = df_c['questionnaire_num'].value_counts().sort_index()
    print(f"\n问卷数量: {len(questionnaire_counts_c)}个")
    print(f"总记录数: {len(df_c)}条")

    # 检查是否有重复记录
    print(f"\n是否有重复记录: {df_c.duplicated().any()}")
    if df_c.duplicated().any():
        print(f"重复记录数: {df_c.duplicated().sum()}")

if __name__ == "__main__":
    check_data_integrity()
