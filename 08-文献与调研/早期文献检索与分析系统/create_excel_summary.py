#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file create_excel_summary.py
@description 创建Excel格式的论文详细分析汇总表
@author AI Assistant
@date 2024
"""

import json
import pandas as pd
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

def create_comprehensive_dataframe(analysis_results: List[Dict[str, Any]], 
                                 original_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """创建综合数据表"""
    
    # 创建标题映射
    title_mapping = {paper.get("title", ""): paper for paper in original_data}
    
    data_rows = []
    
    for result in analysis_results:
        original_title = result.get("original_paper", {}).get("title", "")
        original_paper = title_mapping.get(original_title, {})
        
        row = {
            # 基本信息
            "论文ID": result.get("paper_id", ""),
            "标题": original_paper.get("title", ""),
            "作者": original_paper.get("author", ""),
            "年份": original_paper.get("year", ""),
            "来源": original_paper.get("source", ""),
            "关键词": original_paper.get("keywords", ""),
            
            # 方法信息
            "方法类型": result.get("method_type", ""),
            "方法详情": result.get("method_detail", ""),
            
            # 一级主体标签
            "涉及药企": result.get("level1_pharma", False),
            "涉及政府": result.get("level1_government", False),
            "涉及科研机构": result.get("level1_research", False),
            "涉及保险方": result.get("level1_insurance", False),
            "涉及其他主体": result.get("level1_others", False),
            
            # 二级主体标签
            "药企类型": result.get("level2_pharma", ""),
            "政府部门": result.get("level2_government", ""),
            "科研机构类型": result.get("level2_research", ""),
            "保险方类型": result.get("level2_insurance", ""),
            "其他主体类型": result.get("level2_others", ""),
            
            # 创新特征
            "创新认知差异": result.get("innovation_diff", False),
            "多主体评价": result.get("multi_stakeholder", False),
            "权重分配": result.get("weight_allocation", False),
            "协调机制": result.get("coordination_mechanism", False),
            
            # 关系信息
            "主体关系": result.get("relationships", ""),
            "关系类型": result.get("relationship_types", ""),
            
            # 创新观点
            "药企创新观点": result.get("innovation_view_pharma", ""),
            "政府创新观点": result.get("innovation_view_government", ""),
            "科研创新观点": result.get("innovation_view_research", ""),
            "保险创新观点": result.get("innovation_view_insurance", ""),
            "其他创新观点": result.get("innovation_view_others", ""),
            
            # 研究结论
            "关键假设": result.get("key_assumption", ""),
            "主要结论": result.get("main_conclusion", ""),
            
            # 研究空白
            "主体空白": result.get("gap_subjects", ""),
            "方法空白": result.get("gap_methods", ""),
            "创新空白": result.get("gap_innovation", ""),
            
            # 摘要（用于进一步分析）
            "摘要": original_paper.get("summary", "")[:500] + "..." if len(original_paper.get("summary", "")) > 500 else original_paper.get("summary", "")
        }
        
        data_rows.append(row)
    
    return pd.DataFrame(data_rows)

def create_summary_sheets(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """创建各种汇总表"""
    
    sheets = {}
    
    # 1. 权重分配相关论文
    weight_df = df[df["权重分配"] == True].copy()
    sheets["权重分配研究"] = weight_df
    
    # 2. 多主体评价相关论文
    multi_stakeholder_df = df[df["多主体评价"] == True].copy()
    sheets["多主体评价研究"] = multi_stakeholder_df
    
    # 3. 创新认知差异相关论文
    innovation_diff_df = df[df["创新认知差异"] == True].copy()
    sheets["创新认知差异研究"] = innovation_diff_df
    
    # 4. 协调机制相关论文
    coordination_df = df[df["协调机制"] == True].copy()
    sheets["协调机制研究"] = coordination_df
    
    # 5. 保险方相关论文
    insurance_df = df[df["涉及保险方"] == True].copy()
    sheets["保险方研究"] = insurance_df
    
    # 6. 年份统计
    year_stats = df.groupby("年份").agg({
        "论文ID": "count",
        "权重分配": "sum",
        "多主体评价": "sum",
        "创新认知差异": "sum",
        "协调机制": "sum",
        "涉及保险方": "sum"
    }).rename(columns={"论文ID": "论文总数"})
    sheets["年份统计"] = year_stats
    
    # 7. 方法类型统计
    method_stats = df.groupby("方法类型").agg({
        "论文ID": "count",
        "权重分配": "sum",
        "多主体评价": "sum",
        "创新认知差异": "sum",
        "协调机制": "sum"
    }).rename(columns={"论文ID": "论文总数"})
    sheets["方法类型统计"] = method_stats
    
    # 8. 主体组合分析
    subject_combinations = []
    for _, row in df.iterrows():
        subjects = []
        if row["涉及药企"]: subjects.append("药企")
        if row["涉及政府"]: subjects.append("政府")
        if row["涉及科研机构"]: subjects.append("科研机构")
        if row["涉及保险方"]: subjects.append("保险方")
        if row["涉及其他主体"]: subjects.append("其他主体")
        
        subject_combinations.append({
            "论文ID": row["论文ID"],
            "标题": row["标题"],
            "主体组合": "+".join(subjects),
            "主体数量": len(subjects),
            "权重分配": row["权重分配"],
            "多主体评价": row["多主体评价"],
            "创新认知差异": row["创新认知差异"],
            "协调机制": row["协调机制"]
        })
    
    subject_df = pd.DataFrame(subject_combinations)
    sheets["主体组合分析"] = subject_df
    
    return sheets

def main():
    """主函数"""
    print("=" * 80)
    print("📊 创建Excel格式论文分析汇总表")
    print("=" * 80)
    
    # 加载数据
    print("🔄 加载数据...")
    analysis_results = load_analysis_results()
    original_data = load_original_data()
    
    if not analysis_results or not original_data:
        print("❌ 数据加载失败，程序退出")
        return
    
    print(f"✅ 数据加载完成 - 分析结果: {len(analysis_results)}篇, 原始数据: {len(original_data)}篇")
    
    # 创建综合数据表
    print("🔄 创建综合数据表...")
    df = create_comprehensive_dataframe(analysis_results, original_data)
    print(f"✅ 综合数据表创建完成，共 {len(df)} 行数据")
    
    # 创建各种汇总表
    print("🔄 创建汇总表...")
    sheets = create_summary_sheets(df)
    print(f"✅ 汇总表创建完成，共 {len(sheets)} 个工作表")
    
    # 保存到Excel文件
    print("🔄 保存Excel文件...")
    try:
        with pd.ExcelWriter("创新药论文详细分析汇总表.xlsx", engine='openpyxl') as writer:
            # 主数据表
            df.to_excel(writer, sheet_name="全部论文数据", index=False)
            
            # 各种汇总表
            for sheet_name, sheet_df in sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("✅ Excel文件保存成功: 创新药论文详细分析汇总表.xlsx")
        
    except Exception as e:
        print(f"❌ Excel文件保存失败: {e}")
        print("💡 提示: 请确保已安装openpyxl库: pip install openpyxl")
        
        # 保存为CSV格式作为备选
        try:
            df.to_csv("创新药论文详细分析汇总表.csv", encoding="utf-8-sig", index=False)
            print("✅ CSV文件保存成功: 创新药论文详细分析汇总表.csv")
        except Exception as csv_e:
            print(f"❌ CSV文件保存也失败: {csv_e}")
    
    print("\n" + "=" * 80)
    print("🎉 Excel汇总表创建完成!")
    print("=" * 80)
    
    # 显示统计信息
    print("\n📊 数据统计:")
    print(f"   • 总论文数: {len(df)}")
    print(f"   • 权重分配研究: {df['权重分配'].sum()}篇")
    print(f"   • 多主体评价研究: {df['多主体评价'].sum()}篇")
    print(f"   • 创新认知差异研究: {df['创新认知差异'].sum()}篇")
    print(f"   • 协调机制研究: {df['协调机制'].sum()}篇")
    print(f"   • 保险方研究: {df['涉及保险方'].sum()}篇")
    
    print(f"\n📁 生成文件:")
    print(f"   • 创新药论文详细分析汇总表.xlsx (主要文件)")
    print(f"   • 创新药论文详细分析汇总表.csv (备选文件)")

if __name__ == "__main__":
    main()