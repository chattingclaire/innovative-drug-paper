#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file academic_paper_analyzer.py
@description 创新药论文分析系统：使用大模型分析学术论文，提取结构化信息
@author AI Assistant
@date 2024
"""

import json
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from typing import Dict, List, Any, Optional

# API配置
api_key = "REDACTED_API_KEY"
api_url = "https://openai.app.msh.team/v1"

# 初始化OpenAI客户端
client = OpenAI(
    api_key=api_key,
    base_url=api_url
)

# 线程安全的锁
results_lock = threading.Lock()
progress_lock = threading.Lock()

def load_system_prompt(prompt_file: str) -> Optional[str]:
    """
    加载系统提示词
    
    @param prompt_file: 提示词文件路径
    @return: 系统提示词内容
    """
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            system_prompt = f.read()
        print(f"✅ 成功加载系统提示词: {prompt_file}")
        return system_prompt
    except FileNotFoundError as e:
        print(f"❌ 系统提示词文件未找到: {e}")
        return None
    except Exception as e:
        print(f"❌ 读取系统提示词失败: {e}")
        return None

def load_papers_data(data_file: str) -> List[Dict[str, Any]]:
    """
    加载论文数据
    
    @param data_file: 数据文件路径
    @return: 论文数据列表
    """
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        print(f"✅ 成功加载 {len(papers)} 篇论文数据")
        return papers
    except FileNotFoundError as e:
        print(f"❌ 数据文件未找到: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return []
    except Exception as e:
        print(f"❌ 读取数据文件失败: {e}")
        return []

def format_paper_input(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化论文输入数据
    
    @param paper: 原始论文数据
    @return: 格式化后的论文数据
    """
    return {
        "title": paper.get("title", ""),
        "author": paper.get("author", ""),
        "summary": paper.get("summary", ""),
        "keywords": paper.get("keywords", ""),
        "year": paper.get("year", 0)
    }

def analyze_single_paper(paper: Dict[str, Any], system_prompt: str, paper_index: int, total_count: int) -> Optional[Dict[str, Any]]:
    """
    分析单篇论文
    
    @param paper: 论文数据
    @param system_prompt: 系统提示词
    @param paper_index: 论文索引
    @param total_count: 总论文数
    @return: 分析结果
    """
    # 格式化输入数据
    formatted_paper = format_paper_input(paper)
    
    with progress_lock:
        print(f"🔄 [{paper_index+1}/{total_count}] 分析论文: {formatted_paper['title'][:50]}...")
    
    # 构建用户消息
    user_message = f"""请分析以下论文：

标题：{formatted_paper['title']}
作者：{formatted_paper['author']}
摘要：{formatted_paper['summary']}
关键词：{formatted_paper['keywords']}
年份：{formatted_paper['year']}

请按照系统提示的要求进行分析，直接输出JSON格式的结果。"""
    
    try:
        response = client.chat.completions.create(
            model="claude-sonnet-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.1  # 降低随机性，确保结果一致性
        )
        
        result_content = response.choices[0].message.content.strip()
        
        # 尝试解析JSON结果
        try:
            # 如果结果包含markdown代码块，提取其中的JSON
            if "```json" in result_content:
                start_idx = result_content.find("```json") + 7
                end_idx = result_content.find("```", start_idx)
                if end_idx != -1:
                    result_content = result_content[start_idx:end_idx].strip()
            elif "```" in result_content:
                start_idx = result_content.find("```") + 3
                end_idx = result_content.find("```", start_idx)
                if end_idx != -1:
                    result_content = result_content[start_idx:end_idx].strip()
            
            analysis_result = json.loads(result_content)
            
            # 添加原始论文信息
            analysis_result["original_paper"] = {
                "title": formatted_paper['title'],
                "author": formatted_paper['author'],
                "year": formatted_paper['year'],
                "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with progress_lock:
                print(f"   ✅ 分析完成")
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            with progress_lock:
                print(f"   ❌ JSON解析失败: {e}")
                print(f"   📝 原始响应: {result_content[:200]}...")
            return None
            
    except Exception as e:
        with progress_lock:
            print(f"   ❌ LLM调用失败: {str(e)}")
        return None

def process_papers_threaded(papers: List[Dict[str, Any]], system_prompt: str, max_workers: int = 20) -> List[Dict[str, Any]]:
    """
    多线程处理论文分析
    
    @param papers: 论文列表
    @param system_prompt: 系统提示词
    @param max_workers: 最大线程数
    @return: 分析结果列表
    """
    analysis_results = []
    results = {}
    
    def worker(args):
        paper, index = args
        return index, analyze_single_paper(paper, system_prompt, index, len(papers))
    
    print(f"🔧 启动 {max_workers} 个线程进行并行分析...")
    
    # 使用线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = []
        for i, paper in enumerate(papers):
            future = executor.submit(worker, (paper, i))
            futures.append(future)
        
        # 收集结果
        completed_count = 0
        for future in futures:
            try:
                index, analysis_result = future.result()
                with results_lock:
                    results[index] = analysis_result
                    completed_count += 1
                    
                    # 显示进度
                    if completed_count % 10 == 0 or completed_count == len(papers):
                        print(f"📊 进度: {completed_count}/{len(papers)} ({completed_count/len(papers)*100:.1f}%)")
                        
            except Exception as e:
                print(f"⚠️ 线程处理错误: {e}")
    
    # 按索引顺序整理结果
    for i in range(len(papers)):
        if i in results and results[i] is not None:
            analysis_results.append(results[i])
    
    return analysis_results

def analyze_results_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析结果统计
    
    @param results: 分析结果列表
    @return: 统计信息
    """
    stats = {
        "total_papers": len(results),
        "successful_analysis": len(results),
        "level1_stats": {},
        "method_types": {},
        "innovation_features": {},
        "relationship_types": {},
        "year_distribution": {}
    }
    
    # 初始化统计
    level1_categories = ["pharma", "government", "research", "insurance", "others"]
    for category in level1_categories:
        stats["level1_stats"][category] = 0
    
    innovation_features = ["innovation_diff", "multi_stakeholder", "weight_allocation", "coordination_mechanism"]
    for feature in innovation_features:
        stats["innovation_features"][feature] = 0
    
    for result in results:
        # 统计一级标签
        for category in level1_categories:
            if result.get(f"level1_{category}", False):
                stats["level1_stats"][category] += 1
        
        # 统计方法类型
        method_type = result.get("method_type", "")
        if method_type:
            stats["method_types"][method_type] = stats["method_types"].get(method_type, 0) + 1
        
        # 统计创新特征
        for feature in innovation_features:
            if result.get(feature, False):
                stats["innovation_features"][feature] += 1
        
        # 统计关系类型
        relationship_types = result.get("relationship_types", "")
        if relationship_types:
            for rel_type in relationship_types.split(","):
                rel_type = rel_type.strip()
                if rel_type:
                    stats["relationship_types"][rel_type] = stats["relationship_types"].get(rel_type, 0) + 1
        
        # 统计年份分布
        year = result.get("year", 0)
        if year:
            stats["year_distribution"][year] = stats["year_distribution"].get(year, 0) + 1
    
    return stats

def save_results(results: List[Dict[str, Any]], output_file: str):
    """
    保存分析结果
    
    @param results: 分析结果列表
    @param output_file: 输出文件路径
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到: {output_file}")
    except Exception as e:
        print(f"❌ 保存结果失败: {e}")

def save_statistics(stats: Dict[str, Any], stats_file: str):
    """
    保存统计信息
    
    @param stats: 统计信息
    @param stats_file: 统计文件路径
    """
    try:
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"✅ 统计信息已保存到: {stats_file}")
    except Exception as e:
        print(f"❌ 保存统计信息失败: {e}")

def print_statistics(stats: Dict[str, Any]):
    """
    打印统计信息
    
    @param stats: 统计信息
    """
    print("\n" + "=" * 80)
    print("📊 分析结果统计")
    print("=" * 80)
    
    print(f"📄 总论文数: {stats['total_papers']}")
    print(f"✅ 成功分析: {stats['successful_analysis']}")
    
    print(f"\n🏷️ 一级标签分布:")
    for category, count in stats['level1_stats'].items():
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {category}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n🔬 方法类型分布:")
    for method_type, count in sorted(stats['method_types'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {method_type}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n💡 创新特征分布:")
    for feature, count in stats['innovation_features'].items():
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {feature}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n🔗 关系类型分布:")
    for rel_type, count in sorted(stats['relationship_types'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {rel_type}: {count} 次 ({percentage:.1f}%)")
    
    print(f"\n📅 年份分布 (前10年):")
    sorted_years = sorted(stats['year_distribution'].items(), key=lambda x: x[0], reverse=True)[:10]
    for year, count in sorted_years:
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {year}: {count} 篇 ({percentage:.1f}%)")

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 创新药论文分析系统")
    print("=" * 80)
    
    # 文件路径配置
    prompt_file = "tag-academic-paper-prompt.md"
    data_file = "chuangxinyao.json"
    output_file = "academic_paper_analysis_results.json"
    stats_file = "analysis_statistics.json"
    
    # 检查文件是否存在
    if not os.path.exists(prompt_file):
        print(f"❌ 系统提示词文件不存在: {prompt_file}")
        return
    
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    # 加载系统提示词
    system_prompt = load_system_prompt(prompt_file)
    if not system_prompt:
        return
    
    # 加载论文数据
    papers = load_papers_data(data_file)
    if not papers:
        return
    
    print(f"\n📊 数据统计:")
    print(f"   • 总论文数: {len(papers)}")
    
    # 年份分布统计
    year_counts = {}
    for paper in papers:
        year = paper.get("year", 0)
        if year:
            year_counts[year] = year_counts.get(year, 0) + 1
    
    print(f"   • 年份范围: {min(year_counts.keys()) if year_counts else 'N/A'} - {max(year_counts.keys()) if year_counts else 'N/A'}")
    print(f"   • 涉及年份数: {len(year_counts)}")
    
    # 确认开始分析
    print(f"\n🔧 开始多线程分析...")
    start_time = time.time()
    
    # 多线程处理论文分析
    analysis_results = process_papers_threaded(papers, system_prompt, max_workers=20)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n⏱️ 分析完成，耗时: {processing_time:.2f} 秒")
    
    # 保存结果
    save_results(analysis_results, output_file)
    
    # 分析统计信息
    stats = analyze_results_statistics(analysis_results)
    save_statistics(stats, stats_file)
    
    # 打印统计信息
    print_statistics(stats)
    
    print("\n" + "=" * 80)
    print("🎉 分析完成!")
    print(f"📁 分析结果: {output_file}")
    print(f"📊 统计信息: {stats_file}")
    print(f"⏱️ 总耗时: {processing_time:.2f} 秒")
    print(f"🚀 平均速度: {len(analysis_results)/processing_time:.2f} 篇/秒")
    print("=" * 80)

if __name__ == "__main__":
    main() 