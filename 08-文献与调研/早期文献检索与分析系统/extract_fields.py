#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从chuangxinyao.json中提取指定字段
保留title、author、year、keywords、summary字段
"""

import json
import os

def extract_fields(input_file, output_file, min_pages=6):
    """提取指定字段并保存到新文件，过滤掉页码少于指定值的论文"""
    try:
        # 读取原始文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"原始文件包含 {len(data)} 条记录")
        
        # 提取指定字段并过滤页码
        extracted_data = []
        filtered_count = 0
        
        for item in data:
            # 获取页码信息
            page_count = item.get("page_count", 0)
            
            # 如果页码少于指定值，跳过
            if page_count < min_pages:
                filtered_count += 1
                continue
            
            extracted_item = {
                "title": item.get("title", ""),
                "author": item.get("author", ""),
                "year": item.get("year", ""),
                "keywords": item.get("keywords", ""),
                "summary": item.get("summary", ""),
                "page_count": page_count  # 保留页码信息用于验证
            }
            extracted_data.append(extracted_item)
        
        # 保存到新文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        print(f"提取完成！")
        print(f"输出文件: {output_file}")
        print(f"原始记录数: {len(data)}")
        print(f"过滤掉页码<{min_pages}的记录: {filtered_count}条")
        print(f"最终提取记录数: {len(extracted_data)}")
        
        # 显示前几条记录作为示例
        print("\n前3条记录示例:")
        for i, item in enumerate(extracted_data[:3]):
            print(f"\n记录 {i+1}:")
            print(f"  标题: {item['title'][:50]}...")
            print(f"  作者: {item['author']}")
            print(f"  年份: {item['year']}")
            print(f"  关键词: {item['keywords'][:50]}...")
            print(f"  摘要: {item['summary'][:100]}...")
            
    except Exception as e:
        print(f"处理文件时出错: {e}")

def main():
    input_file = "/Users/moonshot/Desktop/创新药.md/chuangxinyao.json"
    output_file = "/Users/moonshot/Desktop/创新药.md/chuangxinyao_simplified.json"
    
    if not os.path.exists(input_file):
        print(f"输入文件不存在: {input_file}")
        return
    
    extract_fields(input_file, output_file)

if __name__ == "__main__":
    main() 