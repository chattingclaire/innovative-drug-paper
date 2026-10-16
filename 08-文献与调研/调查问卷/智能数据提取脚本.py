#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据提取脚本 - 通过对比选项差异来识别答案
"""

import os
import re
import pandas as pd
from docx import Document
import glob

class SmartDataExtractor:
    """智能数据提取器"""

    def __init__(self, input_dir):
        self.input_dir = input_dir
        self.part_a_data = []
        self.part_b_data = []
        self.part_c_data = []
        self.b6_sorting_data = []

    def extract_questionnaire_number(self, filename):
        """从文件名提取问卷编号"""
        patterns = [
            r'(\d+)调查问卷-提交版\.docx',
            r'(\d+)-调查问卷-提交版\.docx'
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

    def smart_extract_selected_option(self, line, highlighted_runs, colored_runs):
        """智能提取选中的选项 - 通过对比差异"""
        # 1. 首先检查明显的符号标记
        for symbol in ['●', '√', '✓', '◉']:
            match = re.search(f'{symbol}\\s*([^○●√✓◉]+?)(?=[○●√✓◉]|$)', line)
            if match:
                return match.group(1).strip()

        # 2. 检查高亮标记
        for highlighted_run in highlighted_runs:
            if highlighted_run['paragraph_text'] == line:
                highlighted_text = highlighted_run['text']
                option_text = re.sub(r'^○\s*', '', highlighted_text).strip()
                if option_text and not option_text.startswith('○'):
                    return option_text

        # 3. 检查颜色标记
        for colored_run in colored_runs:
            if colored_run['paragraph_text'] == line and colored_run['color'] in ['0000FF', 'EE0000']:
                colored_text = colored_run['text']
                option_text = re.sub(r'^○\s*', '', colored_text).strip()
                if option_text and not option_text.startswith('○'):
                    return option_text

        # 4. 智能对比：找出与其他选项不同的选项
        # 提取所有选项
        options = re.findall(r'[○●√✓◉]\\s*([^○●√✓◉]+?)(?=[○●√✓◉]|$)', line)
        if len(options) > 1:
            # 检查是否有选项没有○符号（被选中的选项）
            for option in options:
                option = option.strip()
                if option and not option.startswith('○'):
                    return option

            # 如果所有选项都有○符号，检查是否有其他差异
            # 比如字体大小、颜色等（这里简化处理）
            # 在实际应用中，可以通过更复杂的对比来识别差异

        # 5. 检查特殊标记：没有○符号的选项
        if '○' not in line and line.strip():
            if len(line.strip()) > 1 and not line.strip().startswith('A') and not line.strip().startswith('B') and not line.strip().startswith('C'):
                return line.strip()

        return None

    def smart_extract_choice_number(self, line, highlighted_runs, colored_runs):
        """智能提取选择的分数"""
        # 1. 检查明显的符号标记
        for symbol in ['●', '√', '✓', '◉']:
            match = re.search(f'{symbol}\\s*(\\d+)', line)
            if match:
                return int(match.group(1))

        # 2. 检查高亮标记
        for highlighted_run in highlighted_runs:
            if highlighted_run['paragraph_text'] == line:
                highlighted_text = highlighted_run['text']
                match = re.search(r'(\\d+)', highlighted_text)
                if match:
                    return int(match.group(1))

        # 3. 检查颜色标记
        for colored_run in colored_runs:
            if colored_run['paragraph_text'] == line and colored_run['color'] in ['0000FF', 'EE0000']:
                colored_text = colored_run['text']
                match = re.search(r'(\\d+)', colored_text)
                if match:
                    return int(match.group(1))

        # 4. 智能对比：找出与其他选项不同的分数
        # 提取所有分数选项
        scores = re.findall(r'[○●√✓◉]\\s*(\\d+)', line)
        if len(scores) > 1:
            # 检查是否有分数没有○符号（被选中的分数）
            for score in scores:
                if not re.search(f'○\\s*{score}', line):
                    return int(score)

        # 5. 检查特殊标记：没有○符号的分数
        if '○' not in line:
            match = re.search(r'(\\d+)', line)
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

        # 处理Part A
        self._process_part_a(lines, questionnaire_num, highlighted_runs, colored_runs)

        # 处理Part B
        self._process_part_b(lines, questionnaire_num, highlighted_runs, colored_runs)

        # 处理Part C
        self._process_part_c(lines, questionnaire_num, highlighted_runs, colored_runs)

    def _process_part_a(self, lines, questionnaire_num, highlighted_runs, colored_runs):
        """处理Part A"""
        for i, line in enumerate(lines):
            question_match = re.match(r'A(\\d+)\\.\\s*(.+)', line)
            if question_match:
                question_num = f"A{question_match.group(1)}"
                question_text = question_match.group(2)

                # 查找选项行
                selected_option = None
                j = i + 1
                while j < len(lines) and not re.match(r'[ABC]\\d+', lines[j]):
                    option_line = lines[j]
                    option = self.smart_extract_selected_option(option_line, highlighted_runs, colored_runs)
                    if option and not selected_option:
                        selected_option = option
                    j += 1

                if selected_option:
                    self.part_a_data.append({
                        'questionnaire_num': questionnaire_num,
                        'part': 'A',
                        'question_num': question_num,
                        'question_text': question_text,
                        'selected_option': selected_option
                    })

    def _process_part_b(self, lines, questionnaire_num, highlighted_runs, colored_runs):
        """处理Part B"""
        for i, line in enumerate(lines):
            # 只处理B1-B5，跳过B6排序题
            question_match = re.match(r'B([1-5])\\s*(.+)', line)
            if question_match:
                question_num = f"B{question_match.group(1)}"
                question_text = question_match.group(2)

                # 查找下一行的评分选项
                if i + 1 < len(lines):
                    options_line = lines[i + 1]
                    choice = self.smart_extract_choice_number(options_line, highlighted_runs, colored_runs)
                    if choice:
                        self.part_b_data.append({
                            'questionnaire_num': questionnaire_num,
                            'part': 'B',
                            'question_num': question_num,
                            'question_text': question_text,
                            'choice': choice
                        })

    def _process_part_c(self, lines, questionnaire_num, highlighted_runs, colored_runs):
        """处理Part C"""
        for i, line in enumerate(lines):
            question_match = re.match(r'C(\\d+)\\s*(.+)', line)
            if question_match:
                question_num = f"C{question_match.group(1)}"
                question_text = question_match.group(2)

                # 查找下一行的评分选项
                if i + 1 < len(lines):
                    options_line = lines[i + 1]
                    choice = self.smart_extract_choice_number(options_line, highlighted_runs, colored_runs)
                    if choice:
                        self.part_c_data.append({
                            'questionnaire_num': questionnaire_num,
                            'part': 'C',
                            'question_num': question_num,
                            'question_text': question_text,
                            'choice': choice
                        })

    def process_all_documents(self):
        """处理所有文档"""
        docx_files = glob.glob(os.path.join(self.input_dir, "*.docx"))
        docx_files.sort()

        print(f"找到 {len(docx_files)} 个Word文档")

        for file_path in docx_files:
            self.process_document(file_path)

    def save_to_csv(self):
        """保存数据到CSV文件"""
        # 保存Part A数据
        if self.part_a_data:
            part_a_df = pd.DataFrame(self.part_a_data)
            part_a_df.to_csv('智能提取_PARTA_问卷数据.csv', index=False, encoding='utf-8-sig')
            print(f"Part A数据已保存: {len(self.part_a_data)}条记录")

        # 保存Part B数据
        if self.part_b_data:
            part_b_df = pd.DataFrame(self.part_b_data)
            part_b_df.to_csv('智能提取_PARTB_问卷数据.csv', index=False, encoding='utf-8-sig')
            print(f"Part B数据已保存: {len(self.part_b_data)}条记录")

        # 保存Part C数据
        if self.part_c_data:
            part_c_df = pd.DataFrame(self.part_c_data)
            part_c_df.to_csv('智能提取_PARTC_问卷数据.csv', index=False, encoding='utf-8-sig')
            print(f"Part C数据已保存: {len(self.part_c_data)}条记录")

    def print_summary(self):
        """打印处理摘要"""
        print("\n" + "="*50)
        print("智能数据提取摘要")
        print("="*50)

        # 统计问卷数量
        part_a_questionnaires = set(item['questionnaire_num'] for item in self.part_a_data)
        part_b_questionnaires = set(item['questionnaire_num'] for item in self.part_b_data)
        part_c_questionnaires = set(item['questionnaire_num'] for item in self.part_c_data)

        print(f"Part A: {len(part_a_questionnaires)}个问卷, {len(self.part_a_data)}条记录")
        print(f"Part B: {len(part_b_questionnaires)}个问卷, {len(self.part_b_data)}条记录")
        print(f"Part C: {len(part_c_questionnaires)}个问卷, {len(self.part_c_data)}条记录")

def main():
    """主函数"""
    input_dir = "."

    extractor = SmartDataExtractor(input_dir)
    extractor.process_all_documents()
    extractor.print_summary()
    extractor.save_to_csv()

    print("\n智能数据提取完成！")

if __name__ == "__main__":
    main()
