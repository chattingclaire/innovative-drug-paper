#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查缺失B6问卷脚本
"""

import pandas as pd

def check_missing_b6_questionnaires():
    """检查缺失的B6问卷"""
    print("="*60)
    print("检查缺失的B6问卷")
    print("="*60)

    # 读取B6数据
    df_b6 = pd.read_csv('02_提取的数据文件/排序后_PARTB6_问卷数据.csv')

    # 获取B6数据中的问卷编号
    b6_questionnaires = set(df_b6['questionnaire_num'])

    # 应该有的问卷编号（1-100）
    all_questionnaires = set(range(1, 101))

    # 找出缺失的问卷
    missing_questionnaires = all_questionnaires - b6_questionnaires

    print(f"B6数据中的问卷数量: {len(b6_questionnaires)}")
    print(f"应该有的问卷数量: {len(all_questionnaires)}")
    print(f"缺失的问卷数量: {len(missing_questionnaires)}")

    if missing_questionnaires:
        print(f"\n缺失的问卷编号: {sorted(missing_questionnaires)}")

        # 检查这些问卷在Part B中是否有数据
        df_b = pd.read_csv('02_提取的数据文件/排序后_PARTB_问卷数据.csv')
        b_questionnaires = set(df_b['questionnaire_num'])

        print(f"\nPart B数据中的问卷数量: {len(b_questionnaires)}")

        # 检查缺失的问卷在Part B中是否有数据
        missing_in_b = missing_questionnaires - b_questionnaires
        if missing_in_b:
            print(f"在Part B中也缺失的问卷: {sorted(missing_in_b)}")

        # 检查缺失的问卷在Part B中有数据但B6缺失的
        missing_only_b6 = missing_questionnaires & b_questionnaires
        if missing_only_b6:
            print(f"Part B有数据但B6缺失的问卷: {sorted(missing_only_b6)}")
    else:
        print("所有问卷都有B6数据")

if __name__ == "__main__":
    check_missing_b6_questionnaires()
