#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新提取B6数据脚本 - 确保所有100个问卷的B6排序题数据都完整
"""

import os
import re
import pandas as pd
from docx import Document
import glob

class B6DataExtractor:
    """B6数据提取器"""

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
            highlighted_runs = []
            colored_runs = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    lines.append(paragraph.text.strip())

                    for run in paragraph.runs:
                        if run.text.strip():
                            # 检查高亮标记
                            if hasattr(run, '_element') and run._element.xml:
                                if 'w:highlight' in run._element.xml or 'w:shd' in run._element.xml:
                                    highlighted_runs.append({
                                        'text': run.text.strip(),
                                        'paragraph_text': paragraph.text.strip()
                                    })

                            # 检查颜色标记
                            if hasattr(run, 'font') and run.font.color and run.font.color.rgb:
                                color_value = str(run.font.color.rgb)
                                colored_runs.append({
                                    'text': run.text.strip(),
                                    'paragraph_text': paragraph.text.strip(),
                                    'color': color_value
                                })

            return lines, highlighted_runs, colored_runs
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return [], [], []

    def find_selected_score(self, line, highlighted_runs, colored_runs):
        """通过格式差异找出选中的分数"""
        # 1. 首先检查明显的符号标记
        for symbol in ['●', '√', '✓', '◉']:
            match = re.search(f'{symbol}\s*(\d+)', line)
            if match:
                return int(match.group(1))

        # 2. 检查高亮标记
        for highlighted_run in highlighted_runs:
            if highlighted_run['paragraph_text'] == line:
                highlighted_text = highlighted_run['text']
                match = re.search(r'(\d+)', highlighted_text)
                if match:
                    return int(match.group(1))

        # 3. 检查颜色标记
        for colored_run in colored_runs:
            if colored_run['paragraph_text'] == line and colored_run['color'] in ['0000FF', 'EE0000']:
                colored_text = colored_run['text']
                match = re.search(r'(\d+)', colored_text)
                if match:
                    return int(match.group(1))

        # 4. 格式差异分析：找出没有○符号的分数
        if '○' in line:
            # 如果行中有○符号，找出没有○符号的分数
            parts = re.split(r'○', line)
            for i, part in enumerate(parts):
                if i > 0 and part.strip():  # 跳过第一个空部分
                    # 检查这个部分是否被选中（没有○符号）
                    match = re.search(r'(\d+)', part)
                    if match:
                        return int(match.group(1))
        else:
            # 如果整行都没有○符号，可能是选中的分数
            match = re.search(r'(\d+)', line)
            if match:
                return int(match.group(1))

        return None

    def process_document(self, file_path):
        """处理单个文档"""
        filename = os.path.basename(file_path)
        questionnaire_num = self.extract_questionnaire_number(filename)

        if questionnaire_num is None:
            print(f"无法提取问卷编号: {filename}")
            return

        lines, highlighted_runs, colored_runs = self.read_docx_file(file_path)
        if not lines:
            return

        print(f"处理问卷 {questionnaire_num}...")

        # 处理B6排序题
        self._process_b6_sorting(lines, questionnaire_num, highlighted_runs, colored_runs)

    def _process_b6_sorting(self, lines, questionnaire_num, highlighted_runs, colored_runs):
        """处理B6排序题"""
        # 查找B6排序题
        b6_started = False
        dimensions = ['安全维度', '有效维度', '经济维度', '创新维度', '公平维度']
        dimension_ranks = {}

        for i, line in enumerate(lines):
            # 查找B6排序题开始
            if 'B6' in line and '排序' in line:
                b6_started = True
                continue

            if b6_started:
                # 查找维度排序
                for dimension in dimensions:
                    if dimension in line:
                        # 查找下一行的排序选项
                        if i + 1 < len(lines):
                            options_line = lines[i + 1]
                            rank = self.find_selected_score(options_line, highlighted_runs, colored_runs)
                            if rank:
                                dimension_ranks[dimension] = rank
                                break

        # 如果找到了5个维度的排序，添加到数据中
        if len(dimension_ranks) == 5:
            for dimension, rank in dimension_ranks.items():
                self.b6_data.append({
                    'questionnaire_num': questionnaire_num,
                    'dimension': dimension,
                    'rank': rank
                })
            print(f"  问卷{questionnaire_num} B6数据: {dimension_ranks}")
        else:
            print(f"  问卷{questionnaire_num} B6数据不完整: {len(dimension_ranks)}/5个维度")

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

    extractor = B6DataExtractor(input_dir)
    extractor.process_all_documents()
    extractor.print_summary()
    extractor.save_to_csv()

    print("\nB6数据重新提取完成！")

if __name__ == "__main__":
    main()
