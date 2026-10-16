#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文详情文件合并去重脚本
合并保险方、创新认知差异、多主体评价、权重分配、协调机制五个论文详情文件
"""

import json
import os
from typing import Dict, List, Set

def load_json_file(file_path: str) -> Dict:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        return {}

def merge_paper_details(file_paths: List[str]) -> Dict:
    """
    合并多个论文详情文件并去重
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        合并后的论文详情字典
    """
    all_papers = []
    seen_titles = set()  # 用于去重的标题集合
    total_papers = 0
    
    for file_path in file_paths:
        print(f"正在处理文件: {file_path}")
        data = load_json_file(file_path)
        
        if not data or '论文详情' not in data:
            print(f"文件 {file_path} 格式不正确或为空")
            continue
            
        papers = data['论文详情']
        total_papers += len(papers)
        
        for paper in papers:
            title = paper.get('标题', '').strip()
            if not title:
                continue
                
            # 去重：如果标题已存在，跳过
            if title in seen_titles:
                print(f"发现重复论文: {title}")
                continue
                
            seen_titles.add(title)
            all_papers.append(paper)
    
    # 按年份排序（降序）
    def get_year(paper):
        year = paper.get('年份', 0)
        if isinstance(year, str):
            try:
                return int(year)
            except (ValueError, TypeError):
                return 0
        return year
    
    all_papers.sort(key=get_year, reverse=True)
    
    # 构建合并后的数据结构
    merged_data = {
        "类别": "创新药论文综合研究",
        "论文数量": len(all_papers),
        "提取时间": "2025-01-27",
        "原始文件": [os.path.basename(fp) for fp in file_paths],
        "去重统计": {
            "总论文数": total_papers,
            "去重后数量": len(all_papers),
            "重复论文数": total_papers - len(all_papers)
        },
        "论文详情": all_papers
    }
    
    return merged_data

def save_merged_data(data: Dict, output_path: str):
    """保存合并后的数据到文件"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"合并文件已保存到: {output_path}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def main():
    """主函数"""
    # 文件路径列表
    file_paths = [
        "/Users/moonshot/Desktop/创新药.md/保险方论文详情.json",
        "/Users/moonshot/Desktop/创新药.md/创新认知差异论文详情.json", 
        "/Users/moonshot/Desktop/创新药.md/多主体评价论文详情.json",
        "/Users/moonshot/Desktop/创新药.md/权重分配论文详情.json",
        "/Users/moonshot/Desktop/创新药.md/协调机制论文详情.json"
    ]
    
    # 检查文件是否存在
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return
    
    print("开始合并论文详情文件...")
    
    # 合并文件
    merged_data = merge_paper_details(file_paths)
    
    # 保存合并后的文件
    output_path = "/Users/moonshot/Desktop/创新药.md/创新药论文详情合并.json"
    save_merged_data(merged_data, output_path)
    
    # 打印统计信息
    print("\n合并完成！")
    print(f"原始论文总数: {merged_data['去重统计']['总论文数']}")
    print(f"去重后论文数: {merged_data['去重统计']['去重后数量']}")
    print(f"重复论文数: {merged_data['去重统计']['重复论文数']}")
    print(f"去重率: {merged_data['去重统计']['重复论文数']/merged_data['去重统计']['总论文数']*100:.1f}%")

if __name__ == "__main__":
    main() 