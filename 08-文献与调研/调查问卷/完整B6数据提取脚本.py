#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整B6数据提取脚本 - 支持多种B6排序题格式
"""

import os
import re
import pandas as pd
from docx import Document
import glob

class CompleteB6Extractor:
    """完整B6数据提取器"""

    def __init__(self, input_dir):
        self.input_dir = input_dir
        self.b6_data = []

    def extract_questionnaire_number(self, filename):
        """从文件名提取问卷编号"""
        patterns = [
            r'(\d+)调查问卷-提交版\.docx',
            r'(\d+)-调查问卷-提交版\.docx',
            r'问卷(\d+)\.docx'
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        return None

    def read_docx_file(self, file_path):
        """读取Word文档内容"""
        try:
            doc = Document(file_path)
            lines = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    lines.append(paragraph.text.strip())

            return lines
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return []

    def process_document(self, file_path):
        """处理单个文档"""
        filename = os.path.basename(file_path)
        questionnaire_num = self.extract_questionnaire_number(filename)

        if questionnaire_num is None:
            print(f"无法提取问卷编号: {filename}")
            return

        lines = self.read_docx_file(file_path)
        if not lines:
            return

        print(f"处理问卷 {questionnaire_num}...")

        # 处理B6排序题
        self._process_b6_sorting(lines, questionnaire_num)

    def _process_b6_sorting(self, lines, questionnaire_num):
        """处理B6排序题 - 支持多种格式"""
        # 查找B6排序题
        b6_started = False
        dimension_ranks = {}

        for i, line in enumerate(lines):
            # 查找B6排序题开始
            if 'B6' in line and '排序' in line:
                b6_started = True
                continue

            if b6_started:
                # 查找维度排序 - 支持多种格式
                # 格式1: _1_ 安全维度 或 __2_ 安全维度
                match1 = re.match(r'_+(\d+)_\s*(.+)', line)
                if match1:
                    rank = int(match1.group(1))
                    dimension = match1.group(2).strip()
                    dimension_ranks[dimension] = rank
                    continue

                # 格式2: 1___ 安全维度 (数字在前，下划线在后)
                match2 = re.match(r'(\d+)_+\s*(.+)', line)
                if match2:
                    rank = int(match2.group(1))
                    dimension = match2.group(2).strip()
                    dimension_ranks[dimension] = rank
                    continue

                # 格式3: ___1 安全维度 (下划线在前，数字在后)
                match3 = re.match(r'_+(\d+)\s*(.+)', line)
                if match3:
                    rank = int(match3.group(1))
                    dimension = match3.group(2).strip()
                    dimension_ranks[dimension] = rank
                    continue

                # 如果遇到Part C，说明B6部分结束
                if 'Part C' in line:
                    break

        # 如果找到了5个维度的排序，添加到数据中
        if len(dimension_ranks) == 5:
            for dimension, rank in dimension_ranks.items():
                self.b6_data.append({
                    'questionnaire_num': questionnaire_num,
                    'dimension': dimension,
                    'rank': rank
                })
            print(f"  问卷{questionnaire_num} B6数据完整: {dimension_ranks}")
        else:
            print(f"  问卷{questionnaire_num} B6数据不完整: {len(dimension_ranks)}/5个维度")
            if dimension_ranks:
                print(f"    已找到: {dimension_ranks}")

    def process_all_documents(self):
        """处理所有文档"""
        docx_files = glob.glob(os.path.join(self.input_dir, "01_原始问卷文件", "*.docx"))
        docx_files.sort()

        print(f"找到 {len(docx_files)} 个Word文档")

        for file_path in docx_files:
            self.process_document(file_path)

    def save_to_csv(self):
        """保存数据到CSV文件"""
        if self.b6_data:
            df_b6 = pd.DataFrame(self.b6_data)
            df_b6 = df_b6.sort_values(['questionnaire_num', 'dimension']).reset_index(drop=True)
            df_b6.to_csv('02_提取的数据文件/完整B6排序题数据.csv', index=False, encoding='utf-8-sig')
            print(f"B6数据已保存: {len(self.b6_data)}条记录")

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

            # 统计排序分布
            print("\n排序分布:")
            rank_counts = df_b6['rank'].value_counts().sort_index()
            for rank, count in rank_counts.items():
                print(f"  第{rank}位: {count}次")

    def print_summary(self):
        """打印处理摘要"""
        print("\n" + "="*50)
        print("B6数据提取摘要")
        print("="*50)
        print(f"总记录数: {len(self.b6_data)}条")

        if self.b6_data:
            df_b6 = pd.DataFrame(self.b6_data)
            questionnaire_counts = df_b6['questionnaire_num'].value_counts()
            print(f"问卷数量: {len(questionnaire_counts)}个")

            # 统计维度分布
            dimension_counts = df_b6['dimension'].value_counts()
            print("维度分布:")
            for dimension, count in dimension_counts.items():
                print(f"  {dimension}: {count}条")

def main():
    """主函数"""
    input_dir = "."

    extractor = CompleteB6Extractor(input_dir)
    extractor.process_all_documents()
    extractor.print_summary()
    extractor.save_to_csv()

    print("\nB6数据提取完成！")

if __name__ == "__main__":
    main()
