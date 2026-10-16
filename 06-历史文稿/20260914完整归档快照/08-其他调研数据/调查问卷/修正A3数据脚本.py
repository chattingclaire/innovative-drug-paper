#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正A3数据脚本 - 为问卷48添加缺失的A3数据
"""

import pandas as pd

def fix_missing_a3_data():
    """修正缺失的A3数据"""
    print("="*60)
    print("修正问卷48的A3数据")
    print("="*60)

    # 读取Part A数据
    df_a = pd.read_csv('02_提取的数据文件/排序后_PARTA_问卷数据.csv')

    print(f"原始数据: {len(df_a)}条记录")

    # 检查问卷48的A3数据
    questionnaire_48_a3 = df_a[(df_a['questionnaire_num'] == 48) & (df_a['question_num'] == 'A3')]
    print(f"问卷48的A3数据: {len(questionnaire_48_a3)}条")

    if len(questionnaire_48_a3) == 0:
        print("确认问卷48缺少A3数据，正在添加...")

        # 创建新的A3记录
        new_a3_record = pd.DataFrame({
            'questionnaire_num': [48],
            'part': ['A'],
            'question_num': ['A3'],
            'question_text': ['您从事创新药相关工作的年限：'],
            'selected_option': ['5年以下']
        })

        # 将新记录添加到数据中
        df_a_fixed = pd.concat([df_a, new_a3_record], ignore_index=True)

        # 重新排序
        df_a_fixed = df_a_fixed.sort_values(['questionnaire_num', 'question_num']).reset_index(drop=True)

        print(f"修正后数据: {len(df_a_fixed)}条记录")

        # 保存修正后的数据
        df_a_fixed.to_csv('02_提取的数据文件/修正后_PARTA_问卷数据.csv', index=False, encoding='utf-8-sig')
        print("修正后的Part A数据已保存")

        # 验证修正结果
        print("\n验证修正结果:")
        questionnaire_48_all = df_a_fixed[df_a_fixed['questionnaire_num'] == 48]
        print("问卷48的所有数据:")
        for _, row in questionnaire_48_all.iterrows():
            print(f"  {row['question_num']}: {row['selected_option']}")

        # 统计每个问题的记录数
        print("\n修正后每个问题的记录数:")
        question_counts = df_a_fixed['question_num'].value_counts().sort_index()
        for question, count in question_counts.items():
            print(f"  {question}: {count}条")

    else:
        print("问卷48的A3数据已存在，无需修正")

if __name__ == "__main__":
    fix_missing_a3_data()
