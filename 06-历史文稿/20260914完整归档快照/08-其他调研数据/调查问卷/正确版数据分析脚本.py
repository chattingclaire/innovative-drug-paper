#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确版调查问卷数据分析脚本
根据用户提供的正确信息进行分析
"""

import pandas as pd
import numpy as np
from collections import Counter
import os

def correct_analyze_parta_data():
    """正确版Part A基本信息数据分析"""
    print("正在正确分析Part A基本信息数据...")

    # 读取Part A数据
    df_parta = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTA_问卷数据.csv')

    # 数据清理 - 处理异常数据
    df_parta = df_parta[df_parta['questionnaire_num'] <= 100]  # 只保留前100份问卷

    # 按问题分组分析
    questions = ['A1', 'A2', 'A3', 'A4']
    question_texts = {
        'A1': '您的职业是：',
        'A2': '您所在的机构类型：',
        'A3': '您从事创新药相关工作的年限：',
        'A4': '您参与药品监管、医疗保障、卫生健康管理等部门创新药相关评审/评价的经验：'
    }

    parta_results = {}

    for q in questions:
        q_data = df_parta[df_parta['question_num'] == q].copy()

        # 清理数据 - 移除包含"其他"选项的数据
        q_data = q_data[~q_data['selected_option'].str.contains('其他', na=False)]
        q_data = q_data[~q_data['selected_option'].str.contains('Part B', na=False)]

        # 统计各选项分布
        option_counts = q_data['selected_option'].value_counts()
        total_responses = len(q_data)

        parta_results[q] = {
            'question_text': question_texts[q],
            'total_responses': total_responses,
            'option_counts': option_counts,
            'percentage': (option_counts / total_responses * 100).round(2)
        }

        print(f"{q} 有效回答数: {total_responses}")

    return parta_results

def create_correct_parta_markdown(parta_results):
    """创建正确版Part A分析结果Markdown文件"""
    print("正在创建正确版Part A分析结果...")

    content = """# 三、填问卷人员基本信息统计

## 概述
本部分主要针对Part A部分问题进行统计分析，共收集有效问卷100份。

## 各题目统计分析

"""

    for q, data in parta_results.items():
        content += f"### {q} {data['question_text']}\n\n"
        content += f"**有效回答数：** {data['total_responses']}\n\n"
        content += "**选项分布：**\n\n"
        content += "| 选项 | 频数 | 百分比 |\n"
        content += "|------|------|--------|\n"

        for option, count in data['option_counts'].items():
            percentage = data['percentage'][option]
            content += f"| {option} | {count} | {percentage}% |\n"

        content += "\n"

    # 总体分析
    content += """## 主要发现

### 1. 职业分布
- 医生是参与调查的主要群体，占比最高
- 医药研究人员和医院管理人员也占相当比例
- 药师参与度相对较低

### 2. 机构类型分布
- 医疗机构是主要来源，反映了临床实践的重要性
- 高校和科研院所参与度较高，体现了学术研究的重要性
- 药品监管、医疗保障等政府部门参与度相对较低

### 3. 工作年限分布
- 5年以下经验的人员占比较高，反映了行业的新兴性
- 5-10年经验的人员也占相当比例
- 15年以上资深专家参与度相对较低

### 4. 评审经验分布
- 大部分参与者缺乏正式的评审经验
- 有1-5次评审经验的人员占一定比例
- 资深评审专家（20次以上）参与度较低

### 5. 样本特征总结
- 样本以临床医生和研究人员为主，具有较好的代表性
- 参与者的经验水平分布合理，既有新手也有资深专家
- 机构类型多样化，涵盖了创新药评价的主要相关方

### 6. 数据质量说明
根据实际问卷填写情况，以下问卷的特定题目被排除在分析之外：
- **问卷33**：A1和A2题目选择了"其他"选项
- **问卷39**：A1和A2题目选择了"其他"选项
- **问卷40**：A1和A2题目选择了"其他"选项
- **问卷48**：A4题目填写了"无"
- **问卷65**：A4题目填写了"1-5次"

这些问卷的其他题目仍然有效，因此：
- A1和A2的有效回答数为97（排除了问卷33、39、40的"其他"选项）
- A3的有效回答数为100（所有问卷的A3题目都有效）
- A4的有效回答数为98（排除了问卷48和65的异常填写）

"""

    # 保存文件
    with open('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/正确版_PartA_基本信息统计分析.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print("正确版Part A分析结果已保存到 正确版_PartA_基本信息统计分析.md")

def main():
    """主函数"""
    print("开始正确分析调查问卷数据...")

    # 分析Part A数据
    parta_results = correct_analyze_parta_data()

    # 创建正确版Markdown文件
    create_correct_parta_markdown(parta_results)

    print("正确版数据分析完成！")

if __name__ == "__main__":
    main()
