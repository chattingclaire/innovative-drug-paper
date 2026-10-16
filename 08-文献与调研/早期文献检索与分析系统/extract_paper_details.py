#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file extract_paper_details.py
@description 提取论文详细信息和评价体系内容
@author AI Assistant
@date 2024
"""

import json
from typing import Dict, List, Any

def load_analysis_results() -> List[Dict[str, Any]]:
    """加载分析结果"""
    try:
        with open("academic_paper_analysis_results.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载分析结果失败: {e}")
        return []

def load_original_data() -> List[Dict[str, Any]]:
    """加载原始论文数据"""
    try:
        with open("chuangxinyao.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载原始数据失败: {e}")
        return []

def create_title_mapping(original_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """创建标题到原始数据的映射"""
    mapping = {}
    for paper in original_data:
        title = paper.get("title", "")
        mapping[title] = paper
    return mapping

def extract_papers_by_feature(analysis_results: List[Dict[str, Any]], 
                            original_mapping: Dict[str, Dict[str, Any]], 
                            feature: str, 
                            value: bool = True) -> List[Dict[str, Any]]:
    """根据特征提取论文"""
    papers = []
    for result in analysis_results:
        if result.get(feature) == value:
            original_title = result.get("original_paper", {}).get("title", "")
            if original_title in original_mapping:
                paper_info = {
                    "analysis_result": result,
                    "original_data": original_mapping[original_title]
                }
                papers.append(paper_info)
    return papers

def extract_papers_with_weight_allocation(analysis_results: List[Dict[str, Any]], 
                                        original_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取涉及权重分配的论文"""
    return extract_papers_by_feature(analysis_results, original_mapping, "weight_allocation", True)

def extract_papers_with_multi_stakeholder(analysis_results: List[Dict[str, Any]], 
                                        original_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取涉及多主体评价的论文"""
    return extract_papers_by_feature(analysis_results, original_mapping, "multi_stakeholder", True)

def extract_papers_with_innovation_diff(analysis_results: List[Dict[str, Any]], 
                                      original_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取涉及创新认知差异的论文"""
    return extract_papers_by_feature(analysis_results, original_mapping, "innovation_diff", True)

def extract_papers_with_coordination_mechanism(analysis_results: List[Dict[str, Any]], 
                                             original_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取涉及协调机制的论文"""
    return extract_papers_by_feature(analysis_results, original_mapping, "coordination_mechanism", True)

def extract_insurance_related_papers(analysis_results: List[Dict[str, Any]], 
                                   original_mapping: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取涉及保险方的论文"""
    return extract_papers_by_feature(analysis_results, original_mapping, "level1_insurance", True)

def format_paper_info(paper_info: Dict[str, Any]) -> Dict[str, Any]:
    """格式化论文信息"""
    analysis = paper_info["analysis_result"]
    original = paper_info["original_data"]
    
    return {
        "标题": original.get("title", ""),
        "作者": original.get("author", ""),
        "年份": original.get("year", ""),
        "来源": original.get("source", ""),
        "关键词": original.get("keywords", ""),
        "摘要": original.get("summary", ""),
        "分析结果": {
            "论文ID": analysis.get("paper_id", ""),
            "方法类型": analysis.get("method_type", ""),
            "方法详情": analysis.get("method_detail", ""),
            "一级主体标签": {
                "药企": analysis.get("level1_pharma", False),
                "政府": analysis.get("level1_government", False),
                "科研机构": analysis.get("level1_research", False),
                "保险方": analysis.get("level1_insurance", False),
                "其他": analysis.get("level1_others", False)
            },
            "二级主体标签": {
                "药企": analysis.get("level2_pharma", ""),
                "政府": analysis.get("level2_government", ""),
                "科研机构": analysis.get("level2_research", ""),
                "保险方": analysis.get("level2_insurance", ""),
                "其他": analysis.get("level2_others", "")
            },
            "创新特征": {
                "创新认知差异": analysis.get("innovation_diff", False),
                "多主体评价": analysis.get("multi_stakeholder", False),
                "权重分配": analysis.get("weight_allocation", False),
                "协调机制": analysis.get("coordination_mechanism", False)
            },
            "主体关系": analysis.get("relationships", ""),
            "关系类型": analysis.get("relationship_types", ""),
            "创新观点": {
                "药企观点": analysis.get("innovation_view_pharma", ""),
                "政府观点": analysis.get("innovation_view_government", ""),
                "科研观点": analysis.get("innovation_view_research", ""),
                "保险观点": analysis.get("innovation_view_insurance", ""),
                "其他观点": analysis.get("innovation_view_others", "")
            },
            "关键假设": analysis.get("key_assumption", ""),
            "主要结论": analysis.get("main_conclusion", ""),
            "研究空白": {
                "主体空白": analysis.get("gap_subjects", ""),
                "方法空白": analysis.get("gap_methods", ""),
                "创新空白": analysis.get("gap_innovation", "")
            }
        }
    }

def save_detailed_papers(papers: List[Dict[str, Any]], filename: str, category_name: str):
    """保存详细论文信息"""
    formatted_papers = [format_paper_info(paper) for paper in papers]
    
    output = {
        "类别": category_name,
        "论文数量": len(formatted_papers),
        "提取时间": "2025-08-24",
        "论文详情": formatted_papers
    }
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ {category_name}论文详情已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存{category_name}论文详情失败: {e}")

def generate_summary_report(all_extractions: Dict[str, List[Dict[str, Any]]]):
    """生成汇总报告"""
    report = []
    report.append("# 创新药论文详细提取报告\n")
    report.append(f"## 提取概览\n")
    
    total_papers = 0
    for category, papers in all_extractions.items():
        count = len(papers)
        total_papers += count
        report.append(f"- **{category}**: {count}篇论文")
    
    report.append(f"\n**总计**: {total_papers}篇论文（可能有重复）\n")
    
    # 为每个类别生成详细信息
    for category, papers in all_extractions.items():
        report.append(f"## {category}论文列表\n")
        
        for i, paper in enumerate(papers, 1):
            original = paper["original_data"]
            analysis = paper["analysis_result"]
            
            report.append(f"### {i}. {original.get('title', 'N/A')}")
            report.append(f"- **作者**: {original.get('author', 'N/A')}")
            report.append(f"- **年份**: {original.get('year', 'N/A')}")
            report.append(f"- **来源**: {original.get('source', 'N/A')}")
            report.append(f"- **方法**: {analysis.get('method_detail', 'N/A')}")
            report.append(f"- **关键假设**: {analysis.get('key_assumption', 'N/A')}")
            report.append(f"- **主要结论**: {analysis.get('main_conclusion', 'N/A')}")
            report.append("")
    
    # 保存报告
    try:
        with open("论文详细提取汇总报告.md", "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        print("✅ 汇总报告已保存到: 论文详细提取汇总报告.md")
    except Exception as e:
        print(f"❌ 保存汇总报告失败: {e}")

def main():
    """主函数"""
    print("=" * 80)
    print("📄 创新药论文详细信息提取")
    print("=" * 80)
    
    # 加载数据
    print("🔄 加载数据...")
    analysis_results = load_analysis_results()
    original_data = load_original_data()
    
    if not analysis_results or not original_data:
        print("❌ 数据加载失败，程序退出")
        return
    
    print(f"✅ 加载完成 - 分析结果: {len(analysis_results)}篇, 原始数据: {len(original_data)}篇")
    
    # 创建映射
    print("🔄 创建标题映射...")
    original_mapping = create_title_mapping(original_data)
    print(f"✅ 映射创建完成")
    
    # 提取不同类别的论文
    print("\n🔄 开始提取论文...")
    
    all_extractions = {}
    
    # 1. 权重分配相关论文
    print("📊 提取权重分配相关论文...")
    weight_papers = extract_papers_with_weight_allocation(analysis_results, original_mapping)
    all_extractions["权重分配研究"] = weight_papers
    save_detailed_papers(weight_papers, "权重分配论文详情.json", "权重分配研究")
    
    # 2. 多主体评价相关论文
    print("👥 提取多主体评价相关论文...")
    multi_stakeholder_papers = extract_papers_with_multi_stakeholder(analysis_results, original_mapping)
    all_extractions["多主体评价研究"] = multi_stakeholder_papers
    save_detailed_papers(multi_stakeholder_papers, "多主体评价论文详情.json", "多主体评价研究")
    
    # 3. 创新认知差异相关论文
    print("💡 提取创新认知差异相关论文...")
    innovation_diff_papers = extract_papers_with_innovation_diff(analysis_results, original_mapping)
    all_extractions["创新认知差异研究"] = innovation_diff_papers
    save_detailed_papers(innovation_diff_papers, "创新认知差异论文详情.json", "创新认知差异研究")
    
    # 4. 协调机制相关论文
    print("🤝 提取协调机制相关论文...")
    coordination_papers = extract_papers_with_coordination_mechanism(analysis_results, original_mapping)
    all_extractions["协调机制研究"] = coordination_papers
    save_detailed_papers(coordination_papers, "协调机制论文详情.json", "协调机制研究")
    
    # 5. 保险方相关论文
    print("🏥 提取保险方相关论文...")
    insurance_papers = extract_insurance_related_papers(analysis_results, original_mapping)
    all_extractions["保险方研究"] = insurance_papers
    save_detailed_papers(insurance_papers, "保险方论文详情.json", "保险方研究")
    
    # 生成汇总报告
    print("\n📋 生成汇总报告...")
    generate_summary_report(all_extractions)
    
    print("\n" + "=" * 80)
    print("🎉 论文详细信息提取完成!")
    print("=" * 80)
    
    # 显示提取统计
    print("\n📊 提取统计:")
    for category, papers in all_extractions.items():
        print(f"   • {category}: {len(papers)}篇")
    
    print(f"\n📁 生成文件:")
    print(f"   • 权重分配论文详情.json")
    print(f"   • 多主体评价论文详情.json")
    print(f"   • 创新认知差异论文详情.json")
    print(f"   • 协调机制论文详情.json")
    print(f"   • 保险方论文详情.json")
    print(f"   • 论文详细提取汇总报告.md")

if __name__ == "__main__":
    main()