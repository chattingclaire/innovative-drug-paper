#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理B6数据脚本 - 清理维度名称中的下划线
"""

import pandas as pd

def clean_b6_data():
    """清理B6数据中的维度名称"""
    print("="*60)
    print("清理B6数据")
    print("="*60)

    # 读取B6数据
    df_b6 = pd.read_csv('02_提取的数据文件/完整B6排序题数据.csv')

    print(f"原始数据: {len(df_b6)}条记录")

    # 清理维度名称中的下划线
    df_b6['dimension'] = df_b6['dimension'].str.replace('^_+\s*', '', regex=True)

    # 重新排序
    df_b6 = df_b6.sort_values(['questionnaire_num', 'dimension']).reset_index(drop=True)

    print(f"清理后数据: {len(df_b6)}条记录")

    # 保存清理后的数据
    df_b6.to_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv', index=False, encoding='utf-8-sig')
    print("清理后的B6数据已保存")

    # 统计问卷数量
    questionnaire_counts = df_b6['questionnaire_num'].value_counts()
    print(f"包含B6数据的问卷数量: {len(questionnaire_counts)}个")

    # 检查是否有问卷数据不完整
    incomplete_questionnaires = []
    for questionnaire_num in range(1, 101):
        count = questionnaire_counts.get(questionnaire_num, 0)
        if count != 5:
            incomplete_questionnaires.append(questionnaire_num)

    if incomplete_questionnaires:
        print(f"数据不完整的问卷: {incomplete_questionnaires}")
    else:
        print("所有问卷的B6数据都完整！")

    # 统计维度分布
    print("\n维度分布:")
    dimension_counts = df_b6['dimension'].value_counts()
    for dimension, count in dimension_counts.items():
        print(f"  {dimension}: {count}条")

    # 统计排序分布
    print("\n排序分布:")
    rank_counts = df_b6['rank'].value_counts().sort_index()
    for rank, count in rank_counts.items():
        print(f"  第{rank}位: {count}次")

if __name__ == "__main__":
    clean_b6_data()
