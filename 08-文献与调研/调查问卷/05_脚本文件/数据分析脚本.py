#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析脚本 - 对提取的问卷数据进行统计分析
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def analyze_part_a():
    """分析Part A基本信息"""
    print("="*60)
    print("三、填问卷人员基本信息统计")
    print("="*60)

    # 读取数据
    df = pd.read_csv('最终格式差异_PARTA_问卷数据.csv')

    # 统计每个问题的选项分布
    questions = ['A1', 'A2', 'A3', 'A4']
    question_names = {
        'A1': '您的职业是：',
        'A2': '您所在的机构类型：',
        'A3': '您从事创新药相关工作的年限：',
        'A4': '您参与药品监管、医疗保障、卫生健康管理等部门创新药相关评审/评价的经验：'
    }

    results = []

    for question in questions:
        question_data = df[df['question_num'] == question]
        question_name = question_names[question]

        # 统计选项分布
        option_counts = question_data['selected_option'].value_counts()
        total_responses = len(question_data)

        print(f"\n{question} {question_name}")
        print("-" * 50)

        for option, count in option_counts.items():
            percentage = (count / total_responses) * 100
            print(f"{option}: {count}人 ({percentage:.1f}%)")
            results.append({
                'question_num': question,
                'question_text': question_name,
                'option': option,
                'count': count,
                'percentage': percentage,
                'total_responses': total_responses
            })

    # 保存结果
    results_df = pd.DataFrame(results)
    results_df.to_csv('PartA_基本信息统计分析.csv', index=False, encoding='utf-8-sig')

    # 生成图表
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('填问卷人员基本信息统计', fontsize=16, fontweight='bold')

    for i, question in enumerate(questions):
        row = i // 2
        col = i % 2

        question_data = df[df['question_num'] == question]
        option_counts = question_data['selected_option'].value_counts()

        axes[row, col].pie(option_counts.values, labels=option_counts.index, autopct='%1.1f%%', startangle=90)
        axes[row, col].set_title(f'{question} {question_names[question]}', fontsize=10)

    plt.tight_layout()
    plt.savefig('PartA_基本信息统计图表.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\nPart A数据统计完成，共{len(df)}条记录")
    return results_df

def analyze_part_b():
    """分析Part B维度重要性"""
    print("\n" + "="*60)
    print("四、对创新药评价各维度的重要程度打分")
    print("="*60)

    # 读取数据
    df = pd.read_csv('最终格式差异_PARTB_问卷数据.csv')

    # 维度名称映射
    dimension_names = {
        'B1': '安全维度',
        'B2': '有效维度',
        'B3': '经济维度',
        'B4': '创新维度',
        'B5': '公平维度'
    }

    results = []

    for question in ['B1', 'B2', 'B3', 'B4', 'B5']:
        question_data = df[df['question_num'] == question]
        dimension_name = dimension_names[question]

        # 计算平均分
        average_score = question_data['choice'].mean()

        # 统计各分数分布
        score_counts = question_data['choice'].value_counts().sort_index()
        total_responses = len(question_data)

        print(f"\n{question} {dimension_name}")
        print("-" * 50)
        print(f"平均分: {average_score:.2f}")
        print("分数分布:")

        for score in range(1, 7):  # 1-6分
            count = score_counts.get(score, 0)
            percentage = (count / total_responses) * 100
            print(f"  {score}分: {count}人 ({percentage:.1f}%)")

            results.append({
                'question_num': question,
                'dimension_name': dimension_name,
                'score': score,
                'count': count,
                'percentage': percentage,
                'total_responses': total_responses,
                'average_score': average_score
            })

    # 保存结果
    results_df = pd.DataFrame(results)
    results_df.to_csv('PartB_维度重要性统计分析.csv', index=False, encoding='utf-8-sig')

    # 生成图表
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('创新药评价各维度重要程度打分统计', fontsize=16, fontweight='bold')

    # 维度平均分对比
    avg_scores = []
    dimension_labels = []

    for question in ['B1', 'B2', 'B3', 'B4', 'B5']:
        question_data = df[df['question_num'] == question]
        avg_score = question_data['choice'].mean()
        avg_scores.append(avg_score)
        dimension_labels.append(dimension_names[question])

    axes[0, 0].bar(dimension_labels, avg_scores, color='skyblue')
    axes[0, 0].set_title('各维度平均分对比', fontweight='bold')
    axes[0, 0].set_ylabel('平均分')
    axes[0, 0].set_ylim(0, 6)
    axes[0, 0].tick_params(axis='x', rotation=45)

    # 为每个维度添加数值标签
    for i, v in enumerate(avg_scores):
        axes[0, 0].text(i, v + 0.1, f'{v:.2f}', ha='center', va='bottom')

    # 各维度分数分布
    for i, question in enumerate(['B1', 'B2', 'B3', 'B4', 'B5']):
        row = (i + 1) // 3
        col = (i + 1) % 3

        question_data = df[df['question_num'] == question]
        score_counts = question_data['choice'].value_counts().sort_index()

        # 确保所有分数都有数据
        all_scores = list(range(1, 7))
        counts = [score_counts.get(score, 0) for score in all_scores]

        axes[row, col].bar(all_scores, counts, color='lightcoral')
        axes[row, col].set_title(f'{dimension_names[question]}分数分布', fontweight='bold')
        axes[row, col].set_xlabel('分数')
        axes[row, col].set_ylabel('人数')
        axes[row, col].set_xticks(all_scores)
        axes[row, col].set_ylim(0, max(counts) + 5)

        # 添加数值标签
        for j, v in enumerate(counts):
            if v > 0:
                axes[row, col].text(all_scores[j], v + 0.5, str(v), ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('PartB_维度重要性统计图表.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\nPart B数据统计完成，共{len(df)}条记录")
    return results_df

def main():
    """主函数"""
    print("开始数据分析...")

    # 分析Part A
    part_a_results = analyze_part_a()

    # 分析Part B
    part_b_results = analyze_part_b()

    print("\n" + "="*60)
    print("数据分析完成！")
    print("="*60)
    print("生成的文件:")
    print("- PartA_基本信息统计分析.csv")
    print("- PartB_维度重要性统计分析.csv")
    print("- PartA_基本信息统计图表.png")
    print("- PartB_维度重要性统计图表.png")

if __name__ == "__main__":
    main()
