#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file test_small_analysis.py
@description 小规模测试脚本，分析前5篇论文
@author AI Assistant
@date 2024
"""

import json
import time
from academic_paper_analyzer import (
    load_system_prompt, 
    load_papers_data, 
    analyze_single_paper,
    save_results,
    analyze_results_statistics,
    print_statistics
)

def main():
    """主函数"""
    print("=" * 80)
    print("🧪 小规模论文分析测试")
    print("=" * 80)
    
    # 加载系统提示词
    system_prompt = load_system_prompt("tag-academic-paper-prompt.md")
    if not system_prompt:
        return
    
    # 加载论文数据
    papers = load_papers_data("chuangxinyao.json")
    if not papers:
        return
    
    # 只取前5篇论文进行测试
    test_papers = papers[:5]
    print(f"\n📊 测试数据: 前 {len(test_papers)} 篇论文")
    
    # 开始分析
    print(f"\n🔧 开始分析...")
    start_time = time.time()
    
    analysis_results = []
    for i, paper in enumerate(test_papers):
        result = analyze_single_paper(paper, system_prompt, i, len(test_papers))
        if result:
            analysis_results.append(result)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n⏱️ 分析完成，耗时: {processing_time:.2f} 秒")
    
    # 保存结果
    output_file = "test_analysis_results.json"
    save_results(analysis_results, output_file)
    
    # 分析统计信息
    stats = analyze_results_statistics(analysis_results)
    
    # 打印统计信息
    print_statistics(stats)
    
    print("\n" + "=" * 80)
    print("🎉 小规模测试完成!")
    print(f"📁 测试结果: {output_file}")
    print(f"⏱️ 总耗时: {processing_time:.2f} 秒")
    print(f"🚀 平均速度: {len(analysis_results)/processing_time:.2f} 篇/秒")
    print("=" * 80)
    
    # 显示第一个分析结果示例
    if analysis_results:
        print(f"\n💡 分析结果示例:")
        first_result = analysis_results[0]
        print(f"论文ID: {first_result.get('paper_id', 'N/A')}")
        print(f"年份: {first_result.get('year', 'N/A')}")
        print(f"方法类型: {first_result.get('method_type', 'N/A')}")
        print(f"创新认知差异: {first_result.get('innovation_diff', 'N/A')}")
        print(f"多主体评价: {first_result.get('multi_stakeholder', 'N/A')}")

if __name__ == "__main__":
    main() 