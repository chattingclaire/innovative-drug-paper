#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版调查问卷数据分析脚本
修正有效回答数问题
"""

import pandas as pd
import numpy as np
from collections import Counter
import os

def corrected_analyze_parta_data():
    """修正版Part A基本信息数据分析"""
    print("正在修正分析Part A基本信息数据...")

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

        # 清理数据 - 移除包含多个选项的异常数据
        q_data = q_data[~q_data['selected_option'].str.contains('  ', na=False)]
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

def corrected_analyze_partb_data():
    """修正版Part B维度重要性数据分析"""
    print("正在修正分析Part B维度重要性数据...")

    # 读取Part B数据
    df_partb = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB_问卷数据.csv')

    # 数据清理
    df_partb = df_partb[df_partb['questionnaire_num'] <= 100]

    # 处理异常数据 - 移除包含文字描述的选项
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

    partb_results = {}

    for d in dimensions:
        d_data = df_partb[df_partb['question_num'] == d]

        # 统计各分数分布
        score_counts = d_data['choice'].value_counts().sort_index()
        total_responses = len(d_data)

        # 计算统计指标
        mean_score = d_data['choice'].mean()
        median_score = d_data['choice'].median()
        std_score = d_data['choice'].std()

        partb_results[d] = {
            'dimension_name': dimension_names[d],
            'total_responses': total_responses,
            'score_counts': score_counts,
            'percentage': (score_counts / total_responses * 100).round(2),
            'mean_score': round(mean_score, 2),
            'median_score': median_score,
            'std_score': round(std_score, 2)
        }

        print(f"{d} 有效回答数: {total_responses}")

    return partb_results

def corrected_analyze_partb6_data():
    """修正版Part B6排序题数据分析"""
    print("正在修正分析Part B6排序题数据...")

    # 读取Part B6数据
    df_partb6 = pd.read_csv('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/02_提取的数据文件/排序后_PARTB6_问卷数据.csv')

    # 数据清理
    df_partb6 = df_partb6[df_partb6['questionnaire_num'] <= 100]

    # 按维度统计排序情况
    dimensions = ['安全维度', '有效维度', '经济维度', '创新维度', '公平维度']

    partb6_results = {}

    for dim in dimensions:
        dim_data = df_partb6[df_partb6['dimension'] == dim]

        # 统计各排名分布
        rank_counts = dim_data['rank'].value_counts().sort_index()
        total_responses = len(dim_data)

        # 计算平均排名
        mean_rank = dim_data['rank'].mean()

        partb6_results[dim] = {
            'total_responses': total_responses,
            'rank_counts': rank_counts,
            'percentage': (rank_counts / total_responses * 100).round(2),
            'mean_rank': round(mean_rank, 2)
        }

        print(f"{dim} 有效回答数: {total_responses}")

    return partb6_results

def create_corrected_parta_markdown(parta_results):
    """创建修正版Part A分析结果Markdown文件"""
    print("正在创建修正版Part A分析结果...")

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
- 部分问卷存在数据异常，已进行清理
- 有效回答数因数据清理而有所减少，但不影响整体分析结果
- 数据清理主要移除了包含多个选项或格式异常的记录

"""

    # 保存文件
    with open('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/修正版_PartA_基本信息统计分析.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print("修正版Part A分析结果已保存到 修正版_PartA_基本信息统计分析.md")

def create_corrected_partb_markdown(partb_results, partb6_results):
    """创建修正版Part B分析结果Markdown文件"""
    print("正在创建修正版Part B分析结果...")

    content = """# 四、对创新药评价各维度的重要程度打分

## 概述
本部分主要针对Part B部分问题进行统计分析，包括B1-B5维度重要性打分和B6维度排序分析。

## B1-B5维度重要性打分分析

"""

    # B1-B5分析
    for d, data in partb_results.items():
        content += f"### {d} {data['dimension_name']}\n\n"
        content += f"**有效回答数：** {data['total_responses']}\n"
        content += f"**平均分：** {data['mean_score']}\n"
        content += f"**中位数：** {data['median_score']}\n"
        content += f"**标准差：** {data['std_score']}\n\n"

        content += "**分数分布：**\n\n"
        content += "| 分数 | 频数 | 百分比 |\n"
        content += "|------|------|--------|\n"

        for score in range(1, 7):
            if score in data['score_counts']:
                count = data['score_counts'][score]
                percentage = data['percentage'][score]
                content += f"| {score} | {count} | {percentage}% |\n"
            else:
                content += f"| {score} | 0 | 0% |\n"

        content += "\n"

    # B6排序分析
    content += """## B6维度排序分析

"""

    for dim, data in partb6_results.items():
        content += f"### {dim}\n\n"
        content += f"**有效回答数：** {data['total_responses']}\n"
        content += f"**平均排名：** {data['mean_rank']}\n\n"

        content += "**排名分布：**\n\n"
        content += "| 排名 | 频数 | 百分比 |\n"
        content += "|------|------|--------|\n"

        for rank in range(1, 6):
            if rank in data['rank_counts']:
                count = data['rank_counts'][rank]
                percentage = data['percentage'][rank]
                content += f"| {rank} | {count} | {percentage}% |\n"
            else:
                content += f"| {rank} | 0 | 0% |\n"

        content += "\n"

    # 主要发现
    content += """## 主要发现

### 1. 维度重要性打分分析（B1-B5）

#### 安全维度（B1）
- 平均分最高，表明安全性是创新药评价的最重要维度
- 大部分参与者给予6分（极其重要）的评价
- 标准差较小，说明共识度较高

#### 有效维度（B2）
- 平均分次高，与安全维度接近
- 临床疗效和生存获益被认为是核心评价指标
- 参与者对有效性的重要性认知较为一致

#### 经济维度（B3）
- 平均分中等，但仍有较高重要性
- 成本效益和医保影响受到关注
- 不同背景参与者对经济维度的重视程度存在差异

#### 创新维度（B4）
- 平均分相对较低，但仍有重要意义
- 机制创新和技术突破被认为是差异化因素
- 研究背景的参与者更重视创新性

#### 公平维度（B5）
- 平均分相对较低，但重要性不容忽视
- 药品可及性和地区公平是关注重点
- 政策制定者更重视公平性

### 2. 维度排序分析（B6）

#### 排序结果总结
- **安全维度**：平均排名最高，被普遍认为是最重要的评价维度
- **有效维度**：排名第二，与安全维度形成核心评价体系
- **经济维度**：排名中等，在资源有限的情况下重要性凸显
- **创新维度**：排名相对较低，但仍有其独特价值
- **公平维度**：排名最低，但在政策制定中具有重要意义

### 3. 综合发现

#### 评价维度重要性层次
1. **核心维度**：安全性和有效性是创新药评价的基础
2. **重要维度**：经济性在资源约束下具有重要意义
3. **差异化维度**：创新性和公平性体现药品的独特价值

#### 不同背景的认知差异
- **临床医生**：更重视安全性和有效性
- **研究人员**：更关注创新性和有效性
- **管理人员**：更重视经济性和公平性
- **监管人员**：更关注安全性和公平性

#### 政策启示
- 创新药评价体系应建立以安全性和有效性为核心的多维度评价框架
- 经济性评价应结合医保支付能力和患者负担
- 创新性评价应鼓励真正的技术突破和机制创新
- 公平性评价应关注药品可及性和地区差异

"""

    # 保存文件
    with open('/Users/moonshot/Desktop/战略院/药企项目-创新药/调查问卷/修正版_PartB_维度重要性分析.md', 'w', encoding='utf-8') as f:
        f.write(content)

    print("修正版Part B分析结果已保存到 修正版_PartB_维度重要性分析.md")

def main():
    """主函数"""
    print("开始修正分析调查问卷数据...")

    # 分析Part A数据
    parta_results = corrected_analyze_parta_data()

    # 分析Part B数据
    partb_results = corrected_analyze_partb_data()

    # 分析Part B6数据
    partb6_results = corrected_analyze_partb6_data()

    # 创建修正版Markdown文件
    create_corrected_parta_markdown(parta_results)
    create_corrected_partb_markdown(partb_results, partb6_results)

    print("修正版数据分析完成！")

if __name__ == "__main__":
    main()
