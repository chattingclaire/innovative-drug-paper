#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缺失数据脚本
"""

import pandas as pd

def check_missing_data():
    """检查缺失的数据"""
    print("="*60)
    print("检查缺失数据")
    print("="*60)

    # 检查Part A数据
    print("\nPart A数据检查:")
    print("-" * 40)
    df_a = pd.read_csv('去重后_PARTA_问卷数据.csv')

    # 检查每个问题的问卷覆盖情况
    for question in ['A1', 'A2', 'A3', 'A4']:
        question_data = df_a[df_a['question_num'] == question]
        questionnaire_nums = set(question_data['questionnaire_num'])
        missing_questionnaires = set(range(1, 101)) - questionnaire_nums

        print(f"{question}: {len(questionnaire_nums)}个问卷")
        if missing_questionnaires:
            print(f"  缺失问卷: {sorted(missing_questionnaires)}")

    # 检查Part B数据
    print("\nPart B数据检查:")
    print("-" * 40)
    df_b = pd.read_csv('去重后_PARTB_问卷数据.csv')

    # 检查每个问题的问卷覆盖情况
    for question in ['B1', 'B2', 'B3', 'B4', 'B5']:
        question_data = df_b[df_b['question_num'] == question]
        questionnaire_nums = set(question_data['questionnaire_num'])
        missing_questionnaires = set(range(1, 101)) - questionnaire_nums

        print(f"{question}: {len(questionnaire_nums)}个问卷")
        if missing_questionnaires:
            print(f"  缺失问卷: {sorted(missing_questionnaires)}")

    # 检查Part C数据
    print("\nPart C数据检查:")
    print("-" * 40)
    df_c = pd.read_csv('去重后_PARTC_问卷数据.csv')

    # 检查每个问题的问卷覆盖情况
    for question in ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9']:
        question_data = df_c[df_c['question_num'] == question]
        questionnaire_nums = set(question_data['questionnaire_num'])
        missing_questionnaires = set(range(1, 101)) - questionnaire_nums

        print(f"{question}: {len(questionnaire_nums)}个问卷")
        if missing_questionnaires:
            print(f"  缺失问卷: {sorted(missing_questionnaires)}")

if __name__ == "__main__":
    check_missing_data()
