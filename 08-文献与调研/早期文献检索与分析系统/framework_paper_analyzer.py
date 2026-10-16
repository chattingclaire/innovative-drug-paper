#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file framework_paper_analyzer.py
@description 基于创新药研究框架的论文筛选系统：识别与框架相关的论文作为研究依据
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

# 配置参数
MAX_WORKERS = 5  # 减少并发线程数，避免API限流
API_DELAY = 1.0  # 增加API调用间隔，避免请求超时
MAX_RETRIES = 3  # 最大重试次数
TIMEOUT = 30     # 请求超时时间（秒）

def load_framework_prompt() -> str:
    """
    加载基于研究框架的分析提示词
    
    @return: 系统提示词内容
    """
    framework_prompt = """
# 创新药研究框架论文筛选系统

## 研究背景
你正在协助一项关于"创新药创新性评价的认知差异：基于制度复杂性的多利益相关者研究"的学术研究。

## 研究核心问题
1. **RQ1（认知结构）**：不同利益相关者如何理解和建构创新药的"创新性"概念？各维度权重存在怎样的系统性差异？
2. **RQ2（形成机制）**：这种认知差异的制度性根源是什么？组织特征和个体特征如何影响认知框架？
3. **RQ3（协调路径）**：如何构建基于认知差异理解的协调机制？哪些因素能够促进认知趋同？

## 研究框架核心要素

### 理论基础
- **制度复杂性理论**：Greenwood等（2011）的多重制度逻辑响应策略
- **认知框架理论**：Kahneman（2011）的双系统理论，Walsh（1995）的管理者认知框架
- **创新性概念的多维建构**：技术创新性、临床价值、社会经济三个维度

### 关键概念
- **制度逻辑**：科学逻辑、市场逻辑、公共逻辑
- **利益相关者**：药监系统、医保系统、医疗机构、制药企业、科研院所
- **认知差异**：不同主体对创新性的理解和评价标准差异
- **协调机制**：促进认知趋同的制度设计

### 研究假设
- **H1**：不同制度逻辑主导下的利益相关者对创新性采用系统性差异的认知框架
- **H2**：组织特征和个体特征共同塑造创新性评价标准
- **H3**：特定条件下存在认知趋同的可能性

## 分析任务
判断给定论文是否与上述研究框架相关，并提取关键信息。

## 输出格式
直接输出JSON，无其他文字：

```json
{
  "paper_id": "年份_标题前8字",
  "relevance_score": 8.5,
  "is_framework_relevant": true,
  "relevance_reason": "涉及药监与医保评价标准差异",
  
  "framework_elements": {
    "institutional_complexity": true,
    "cognitive_differences": true,
    "stakeholder_analysis": true,
    "coordination_mechanism": false,
    "innovation_evaluation": true
  },
  
  "research_questions": {
    "rq1_cognitive_structure": true,
    "rq2_formation_mechanism": false,
    "rq3_coordination_path": false
  },
  
  "stakeholders_involved": {
    "regulatory": true,
    "insurance": true,
    "healthcare": false,
    "pharmaceutical": true,
    "research": false
  },
  
  "theoretical_foundation": {
    "institutional_theory": true,
    "cognitive_framework": false,
    "innovation_theory": true,
    "stakeholder_theory": false
  },
  
  "key_findings": "药监重视技术创新，医保关注临床价值",
  "methodology": "文献分析,政策比较",
  "data_sources": "政策文件,专家访谈",
  
  "contribution_to_framework": "验证了不同主体认知差异的存在",
  "limitations": "缺少实证数据",
  "future_research": "需要量化分析认知差异程度"
}
```

## 评分标准
- **relevance_score**: 1-10分，10分为完全相关
- **is_framework_relevant**: 7分以上为相关
- 重点关注：认知差异、制度复杂性、多利益相关者、创新性评价
"""
    return framework_prompt

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
        "year": paper.get("year", 0),
        "source": paper.get("source", ""),
        "organ": paper.get("organ", "")
    }

def analyze_single_paper(paper: Dict[str, Any], system_prompt: str, paper_index: int, total_count: int) -> Optional[Dict[str, Any]]:
    """
    分析单篇论文与框架的相关性（带重试机制）
    
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
    user_message = f"""请分析以下论文与研究框架的相关性：

标题：{formatted_paper['title']}
作者：{formatted_paper['author']}
来源：{formatted_paper['source']}
机构：{formatted_paper['organ']}
摘要：{formatted_paper['summary']}
关键词：{formatted_paper['keywords']}
年份：{formatted_paper['year']}

请按照系统提示的要求进行分析，直接输出JSON格式的结果。"""
    
    # 重试机制
    for retry in range(MAX_RETRIES):
        try:
            # API限流
            time.sleep(API_DELAY)
            
            response = client.chat.completions.create(
                model="claude-3-5-sonnet-20240620",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,  # 降低随机性，确保结果一致性
                timeout=TIMEOUT   # 设置超时时间
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
                    "source": formatted_paper['source'],
                    "organ": formatted_paper['organ'],
                    "year": formatted_paper['year'],
                    "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with progress_lock:
                    relevance_score = analysis_result.get("relevance_score", 0)
                    is_relevant = analysis_result.get("is_framework_relevant", False)
                    print(f"   ✅ 分析完成 - 相关性: {relevance_score}/10, 是否相关: {is_relevant}")
                
                return analysis_result
                
            except json.JSONDecodeError as e:
                with progress_lock:
                    print(f"   ⚠️ JSON解析失败 (重试 {retry+1}/{MAX_RETRIES}): {e}")
                    if retry == MAX_RETRIES - 1:
                        print(f"   📝 原始响应: {result_content[:200]}...")
                continue
                
        except Exception as e:
            with progress_lock:
                print(f"   ⚠️ LLM调用失败 (重试 {retry+1}/{MAX_RETRIES}): {str(e)}")
                if retry == MAX_RETRIES - 1:
                    print(f"   ❌ 最终失败: {str(e)}")
            continue
    
    return None

def process_papers_threaded(papers: List[Dict[str, Any]], system_prompt: str, max_workers: int = MAX_WORKERS) -> List[Dict[str, Any]]:
    """
    多线程处理论文分析（优化版本）
    
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
    
    # 分批处理（小批次减少内存占用和API压力）
    batch_size = 3
    batches = [(i, paper) for i, paper in enumerate(papers)]
    batch_groups = [batches[i:i+batch_size] for i in range(0, len(batches), batch_size)]
    
    print(f"📦 将 {len(papers)} 篇论文分为 {len(batch_groups)} 个批次处理")
    
    # 使用线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交批次任务
        futures = []
        for batch in batch_groups:
            future = executor.submit(process_batch, batch, system_prompt, len(papers))
            futures.append(future)
        
        # 收集结果
        completed_count = 0
        for future in futures:
            try:
                batch_results = future.result()
                with results_lock:
                    for index, analysis_result in batch_results:
                        results[index] = analysis_result
                        completed_count += 1
                    
                    # 显示进度
                    if completed_count % 10 == 0 or completed_count == len(papers):
                        print(f"📊 进度: {completed_count}/{len(papers)} ({completed_count/len(papers)*100:.1f}%)")
                        
            except Exception as e:
                print(f"⚠️ 批次处理错误: {e}")
    
    # 按索引顺序整理结果
    for i in range(len(papers)):
        if i in results and results[i] is not None:
            analysis_results.append(results[i])
    
    return analysis_results

def process_batch(batch: List[tuple], system_prompt: str, total_count: int) -> List[tuple]:
    """
    处理单个批次的论文
    
    @param batch: 批次数据 [(index, paper), ...]
    @param system_prompt: 系统提示词
    @param total_count: 总论文数
    @return: 批次结果 [(index, result), ...]
    """
    batch_results = []
    
    for index, paper in batch:
        result = analyze_single_paper(paper, system_prompt, index, total_count)
        if result is not None:
            batch_results.append((index, result))
    
    return batch_results

def filter_relevant_papers(results: List[Dict[str, Any]], min_score: float = 7.0) -> List[Dict[str, Any]]:
    """
    筛选相关论文
    
    @param results: 分析结果列表
    @param min_score: 最低相关性分数
    @return: 相关论文列表
    """
    relevant_papers = []
    
    for result in results:
        relevance_score = result.get("relevance_score", 0)
        is_framework_relevant = result.get("is_framework_relevant", False)
        
        if relevance_score >= min_score or is_framework_relevant:
            relevant_papers.append(result)
    
    return relevant_papers

def analyze_results_statistics(results: List[Dict[str, Any]], relevant_papers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析结果统计
    
    @param results: 分析结果列表
    @param relevant_papers: 相关论文列表
    @return: 统计信息
    """
    stats = {
        "total_papers": len(results),
        "relevant_papers": len(relevant_papers),
        "relevance_rate": len(relevant_papers) / len(results) * 100 if results else 0,
        "average_relevance_score": 0,
        "score_distribution": {},
        "framework_elements": {},
        "research_questions": {},
        "stakeholders": {},
        "theoretical_foundation": {},
        "year_distribution": {},
        "source_distribution": {}
    }
    
    # 计算平均相关性分数
    total_score = 0
    score_counts = {}
    
    for result in results:
        score = result.get("relevance_score", 0)
        total_score += score
        
        # 分数分布
        score_range = f"{(int(score)//2)*2}-{(int(score)//2)*2+1}"
        score_counts[score_range] = score_counts.get(score_range, 0) + 1
        
        # 框架要素统计
        framework_elements = result.get("framework_elements", {})
        for element, value in framework_elements.items():
            if value:
                stats["framework_elements"][element] = stats["framework_elements"].get(element, 0) + 1
        
        # 研究问题统计
        research_questions = result.get("research_questions", {})
        for question, value in research_questions.items():
            if value:
                stats["research_questions"][question] = stats["research_questions"].get(question, 0) + 1
        
        # 利益相关者统计
        stakeholders = result.get("stakeholders_involved", {})
        for stakeholder, value in stakeholders.items():
            if value:
                stats["stakeholders"][stakeholder] = stats["stakeholders"].get(stakeholder, 0) + 1
        
        # 理论基础统计
        theoretical = result.get("theoretical_foundation", {})
        for theory, value in theoretical.items():
            if value:
                stats["theoretical_foundation"][theory] = stats["theoretical_foundation"].get(theory, 0) + 1
        
        # 年份分布
        year = result.get("original_paper", {}).get("year", 0)
        if year:
            stats["year_distribution"][year] = stats["year_distribution"].get(year, 0) + 1
        
        # 来源分布
        source = result.get("original_paper", {}).get("source", "")
        if source:
            stats["source_distribution"][source] = stats["source_distribution"].get(source, 0) + 1
    
    stats["average_relevance_score"] = total_score / len(results) if results else 0
    stats["score_distribution"] = score_counts
    
    return stats

def save_results(results: List[Dict[str, Any]], relevant_papers: List[Dict[str, Any]], output_file: str, relevant_file: str):
    """
    保存分析结果
    
    @param results: 分析结果列表
    @param relevant_papers: 相关论文列表
    @param output_file: 输出文件路径
    @param relevant_file: 相关论文文件路径
    """
    try:
        # 保存所有结果
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 所有分析结果已保存到: {output_file}")
        
        # 保存相关论文
        with open(relevant_file, "w", encoding="utf-8") as f:
            json.dump(relevant_papers, f, ensure_ascii=False, indent=2)
        print(f"✅ 相关论文已保存到: {relevant_file}")
        
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
    print("📊 框架相关性分析结果统计")
    print("=" * 80)
    
    print(f"📄 总论文数: {stats['total_papers']}")
    print(f"🎯 相关论文数: {stats['relevant_papers']}")
    print(f"📈 相关性比例: {stats['relevance_rate']:.1f}%")
    print(f"📊 平均相关性分数: {stats['average_relevance_score']:.2f}/10")
    
    print(f"\n📊 相关性分数分布:")
    for score_range, count in sorted(stats['score_distribution'].items()):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {score_range}分: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n🏗️ 框架要素覆盖情况:")
    for element, count in sorted(stats['framework_elements'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {element}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n❓ 研究问题覆盖情况:")
    for question, count in sorted(stats['research_questions'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {question}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n👥 利益相关者覆盖情况:")
    for stakeholder, count in sorted(stats['stakeholders'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {stakeholder}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n📚 理论基础覆盖情况:")
    for theory, count in sorted(stats['theoretical_foundation'].items(), key=lambda x: x[1], reverse=True):
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {theory}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n📅 年份分布 (前10年):")
    sorted_years = sorted(stats['year_distribution'].items(), key=lambda x: x[0], reverse=True)[:10]
    for year, count in sorted_years:
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {year}: {count} 篇 ({percentage:.1f}%)")
    
    print(f"\n📖 主要来源期刊 (前10个):")
    sorted_sources = sorted(stats['source_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]
    for source, count in sorted_sources:
        percentage = count / stats['total_papers'] * 100 if stats['total_papers'] > 0 else 0
        print(f"   • {source}: {count} 篇 ({percentage:.1f}%)")

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 创新药研究框架论文筛选系统")
    print("=" * 80)
    
    # 文件路径配置
    data_file = "chuangxinyao.json"
    output_file = "framework_analysis_results.json"
    relevant_file = "framework_relevant_papers.json"
    stats_file = "framework_analysis_statistics.json"
    
    # 检查文件是否存在
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    # 加载系统提示词
    system_prompt = load_framework_prompt()
    
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
    analysis_results = process_papers_threaded(papers, system_prompt, max_workers=MAX_WORKERS)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"\n⏱️ 分析完成，耗时: {processing_time:.2f} 秒")
    
    # 筛选相关论文
    print(f"\n🔍 筛选相关论文...")
    relevant_papers = filter_relevant_papers(analysis_results, min_score=7.0)
    print(f"✅ 筛选出 {len(relevant_papers)} 篇相关论文")
    
    # 保存结果
    save_results(analysis_results, relevant_papers, output_file, relevant_file)
    
    # 分析统计信息
    stats = analyze_results_statistics(analysis_results, relevant_papers)
    save_statistics(stats, stats_file)
    
    # 打印统计信息
    print_statistics(stats)
    
    print("\n" + "=" * 80)
    print("🎉 框架相关性分析完成!")
    print(f"📁 所有分析结果: {output_file}")
    print(f"🎯 相关论文: {relevant_file}")
    print(f"📊 统计信息: {stats_file}")
    print(f"⏱️ 总耗时: {processing_time:.2f} 秒")
    print(f"🚀 平均速度: {len(analysis_results)/processing_time:.2f} 篇/秒")
    print("=" * 80)

if __name__ == "__main__":
    main() 