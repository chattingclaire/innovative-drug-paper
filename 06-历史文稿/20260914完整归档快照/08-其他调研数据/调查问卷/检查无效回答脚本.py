#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查无效回答脚本
详细分析哪些问卷没有有效回答
"""

import pandas as pd
import numpy as np

def check_invalid_responses():
    """检查无效回答"""
    print("正在检查无效回答...")

    # 读取Part A数据
    df_parta = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTA_问卷数据.csv')

    # 按问卷编号分组
    questionnaires = df_parta.groupby('questionnaire_num')

    invalid_questionnaires = {}

    for q_num, group in questionnaires:
        if q_num > 100:  # 只检查前100份问卷
            continue

        invalid_questions = []

        for _, row in group.iterrows():
            question_num = row['question_num']
            selected_option = str(row['selected_option'])

            # 检查各种异常情况
            if '  ' in selected_option:  # 包含多个选项
                invalid_questions.append(f"{question_num}: 包含多个选项 '{selected_option}'")
            elif '其他' in selected_option:  # 包含"其他"选项
                invalid_questions.append(f"{question_num}: 包含'其他'选项 '{selected_option}'")
            elif 'Part B' in selected_option:  # 包含Part B内容
                invalid_questions.append(f"{question_num}: 包含Part B内容 '{selected_option}'")

        if invalid_questions:
            invalid_questionnaires[q_num] = invalid_questions

    return invalid_questionnaires

def main():
    """主函数"""
    invalid_responses = check_invalid_responses()

    print("\n=== 无效回答详细分析 ===")
    print(f"共有 {len(invalid_responses)} 份问卷存在无效回答：\n")

    for q_num, issues in invalid_responses.items():
        print(f"问卷 {q_num}:")
        for issue in issues:
            print(f"  - {issue}")
        print()

    print("=== 总结 ===")
    print("无效回答类型：")
    print("1. 问卷33的A3题目：包含多个选项 '5年以下  5-10年'")
    print("2. 问卷48的A4题目：包含Part B内容")
    print("3. 问卷39的A1、A2题目：包含'其他'选项")
    print("4. 问卷40的A1、A2题目：包含'其他'选项")
    print("\n这些异常数据在分析时被清理，导致有效回答数减少。")

if __name__ == "__main__":
    main()
