#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查B6数据脚本
"""

import pandas as pd

def check_b6_data():
    """检查B6排序题数据"""
    print("="*60)
    print("检查B6排序题数据")
    print("="*60)

    # 读取B6数据
    df_b6 = pd.read_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv')

    print(f"B6数据总记录数: {len(df_b6)}")

    # 检查问卷数量
    questionnaire_counts = df_b6['questionnaire_num'].value_counts().sort_index()
    print(f"问卷数量: {len(questionnaire_counts)}个")

    # 检查每个问卷的维度数量
    print("\n每个问卷的维度数量:")
    for questionnaire_num in sorted(questionnaire_counts.index):
        count = questionnaire_counts[questionnaire_num]
        print(f"  问卷{questionnaire_num}: {count}个维度")
        if count != 5:
            print(f"    ⚠️ 问卷{questionnaire_num}维度数量异常!")

    # 检查是否有重复记录
    print(f"\n是否有重复记录: {df_b6.duplicated().any()}")
    if df_b6.duplicated().any():
        print(f"重复记录数: {df_b6.duplicated().sum()}")

    # 检查维度分布
    print("\n维度分布:")
    dimension_counts = df_b6['dimension'].value_counts()
    for dimension, count in dimension_counts.items():
        print(f"  {dimension}: {count}条")

    # 检查排序值分布
    print("\n排序值分布:")
    rank_counts = df_b6['rank'].value_counts().sort_index()
    for rank, count in rank_counts.items():
        print(f"  {rank}位: {count}次")

if __name__ == "__main__":
    check_b6_data()
