#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保存分析结果到CSV文件脚本
将分析结果保存到"排序后"数据文件的其他sheet中
"""

import pandas as pd
import numpy as np
from collections import Counter
import os

def analyze_and_save_parta_results():
    """分析Part A数据并保存到CSV"""
    print("正在分析Part A数据并保存到CSV...")

    # 读取Part A数据
    df_parta = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTA_问卷数据.csv')

    # 数据清理
    df_parta = df_parta[df_parta['questionnaire_num'] <= 100]

    # 按问题分组分析
    questions = ['A1', 'A2', 'A3', 'A4']
    question_texts = {
        'A1': '您的职业是：',
        'A2': '您所在的机构类型：',
        'A3': '您从事创新药相关工作的年限：',
        'A4': '您参与药品监管、医疗保障、卫生健康管理等部门创新药相关评审/评价的经验：'
    }

    # 创建Excel写入器
    excel_file = '/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTA_问卷数据_分析结果.xlsx'

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # 保存原始数据
        df_parta.to_excel(writer, sheet_name='原始数据', index=False)

        # 分析每个问题
        for q in questions:
            q_data = df_parta[df_parta['question_num'] == q].copy()

            # 清理数据 - 只移除包含"其他"选项的数据
            q_data = q_data[~q_data['selected_option'].str.contains('其他', na=False)]

            # 统计各选项分布
            option_counts = q_data['selected_option'].value_counts()
            total_responses = len(q_data)

            # 创建统计结果DataFrame
            stats_df = pd.DataFrame({
                '选项': option_counts.index,
                '频数': option_counts.values,
                '百分比': (option_counts.values / total_responses * 100).round(2)
            })

            # 添加汇总信息
            summary_df = pd.DataFrame({
                '统计项目': ['有效回答数', '问题描述'],
                '数值': [total_responses, question_texts[q]]
            })

            # 保存到不同的sheet
            sheet_name = f'{q}_统计分析'
            summary_df.to_excel(writer, sheet_name=f'{q}_汇总', index=False)
            stats_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Part A分析结果已保存到: {excel_file}")

def analyze_and_save_partb_results():
    """分析Part B数据并保存到CSV"""
    print("正在分析Part B数据并保存到CSV...")

    # 读取Part B数据
    df_partb = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB_问卷数据.csv')

    # 数据清理
    df_partb = df_partb[df_partb['questionnaire_num'] <= 100]
    df_partb = df_partb[df_partb['choice'].astype(str).str.isdigit()]
    df_partb['choice'] = df_partb['choice'].astype(int)

    # 按维度分组分析
    dimensions = ['B1', 'B2', 'B3', 'B4', 'B5']
    dimension_names = {
        'B1': '安全维度',
        'B2': '有效维度',
        'B3': '经济维度',
        'B4': '创新维度',
        'B5': '公平维度'
    }

    # 创建Excel写入器
    excel_file = '/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB_问卷数据_分析结果.xlsx'

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # 保存原始数据
        df_partb.to_excel(writer, sheet_name='原始数据', index=False)

        # 分析每个维度
        for d in dimensions:
            d_data = df_partb[df_partb['question_num'] == d]

            # 统计各分数分布
            score_counts = d_data['choice'].value_counts().sort_index()
            total_responses = len(d_data)

            # 计算统计指标
            mean_score = d_data['choice'].mean()
            median_score = d_data['choice'].median()
            std_score = d_data['choice'].std()

            # 创建分数分布DataFrame
            score_dist_df = pd.DataFrame({
                '分数': range(1, 7),
                '频数': [score_counts.get(i, 0) for i in range(1, 7)],
                '百分比': [(score_counts.get(i, 0) / total_responses * 100) for i in range(1, 7)]
            })

            # 创建统计汇总DataFrame
            summary_df = pd.DataFrame({
                '统计指标': ['维度名称', '有效回答数', '平均分', '中位数', '标准差'],
                '数值': [dimension_names[d], total_responses, round(mean_score, 2), median_score, round(std_score, 2)]
            })

            # 保存到不同的sheet
            sheet_name = f'{d}_统计分析'
            summary_df.to_excel(writer, sheet_name=f'{d}_汇总', index=False)
            score_dist_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Part B分析结果已保存到: {excel_file}")

def analyze_and_save_partb6_results():
    """分析Part B6数据并保存到CSV"""
    print("正在分析Part B6数据并保存到CSV...")

    # 读取Part B6数据
    df_partb6 = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB6_问卷数据.csv')

    # 数据清理
    df_partb6 = df_partb6[df_partb6['questionnaire_num'] <= 100]

    # 按维度统计排序情况
    dimensions = ['安全维度', '有效维度', '经济维度', '创新维度', '公平维度']

    # 创建Excel写入器
    excel_file = '/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB6_问卷数据_分析结果.xlsx'

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # 保存原始数据
        df_partb6.to_excel(writer, sheet_name='原始数据', index=False)

        # 分析每个维度
        for dim in dimensions:
            dim_data = df_partb6[df_partb6['dimension'] == dim]

            # 统计各排名分布
            rank_counts = dim_data['rank'].value_counts().sort_index()
            total_responses = len(dim_data)

            # 计算平均排名
            mean_rank = dim_data['rank'].mean()

            # 创建排名分布DataFrame
            rank_dist_df = pd.DataFrame({
                '排名': range(1, 6),
                '频数': [rank_counts.get(i, 0) for i in range(1, 6)],
                '百分比': [(rank_counts.get(i, 0) / total_responses * 100) for i in range(1, 6)]
            })

            # 创建统计汇总DataFrame
            summary_df = pd.DataFrame({
                '统计指标': ['维度名称', '有效回答数', '平均排名'],
                '数值': [dim, total_responses, round(mean_rank, 2)]
            })

            # 保存到不同的sheet
            sheet_name = f'{dim}_统计分析'
            summary_df.to_excel(writer, sheet_name=f'{dim}_汇总', index=False)
            rank_dist_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Part B6分析结果已保存到: {excel_file}")

def main():
    """主函数"""
    print("开始保存分析结果到CSV文件...")

    # 分析并保存Part A结果
    analyze_and_save_parta_results()

    # 分析并保存Part B结果
    analyze_and_save_partb_results()

    # 分析并保存Part B6结果
    analyze_and_save_partb6_results()

    print("所有分析结果已保存到CSV文件！")

if __name__ == "__main__":
    main()
