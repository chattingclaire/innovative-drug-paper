#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file test_analyzer.py
@description 创新药论文分析系统测试脚本
@author AI Assistant
@date 2024
"""

import json
import os
from academic_paper_analyzer import load_system_prompt, load_papers_data, format_paper_input

def test_file_loading():
    """测试文件加载功能"""
    print("🧪 测试文件加载功能...")
    
    # 测试系统提示词加载
    prompt_file = "tag-academic-paper-prompt.md"
    if os.path.exists(prompt_file):
        system_prompt = load_system_prompt(prompt_file)
        if system_prompt:
            print(f"✅ 系统提示词加载成功，长度: {len(system_prompt)} 字符")
        else:
            print("❌ 系统提示词加载失败")
    else:
        print(f"❌ 系统提示词文件不存在: {prompt_file}")
    
    # 测试论文数据加载
    data_file = "chuangxinyao.json"
    if os.path.exists(data_file):
        papers = load_papers_data(data_file)
        if papers:
            print(f"✅ 论文数据加载成功，共 {len(papers)} 篇论文")
            
            # 显示前几篇论文的基本信息
            print("\n📄 前3篇论文信息:")
            for i, paper in enumerate(papers[:3]):
                print(f"   {i+1}. {paper.get('title', 'N/A')[:50]}... ({paper.get('year', 'N/A')})")
        else:
            print("❌ 论文数据加载失败")
    else:
        print(f"❌ 论文数据文件不存在: {data_file}")

def test_data_formatting():
    """测试数据格式化功能"""
    print("\n🧪 测试数据格式化功能...")
    
    # 加载测试数据
    data_file = "chuangxinyao.json"
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return
    
    papers = load_papers_data(data_file)
    if not papers:
        print("❌ 无法加载论文数据")
        return
    
    # 测试格式化
    test_paper = papers[0]
    formatted_paper = format_paper_input(test_paper)
    
    print("✅ 数据格式化测试:")
    print(f"   原始字段数: {len(test_paper)}")
    print(f"   格式化后字段数: {len(formatted_paper)}")
    print(f"   标题: {formatted_paper.get('title', 'N/A')[:50]}...")
    print(f"   作者: {formatted_paper.get('author', 'N/A')}")
    print(f"   年份: {formatted_paper.get('year', 'N/A')}")

def test_api_connection():
    """测试API连接"""
    print("\n🧪 测试API连接...")
    
    try:
        from openai import OpenAI
        
        # API配置
        api_key = "REDACTED_API_KEY"
        api_url = "https://openai.app.msh.team/v1"
        
        client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )
        
        # 简单测试
        response = client.chat.completions.create(
            model="claude-sonnet-4",
            messages=[
                {"role": "user", "content": "请回复'API连接测试成功'"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        if "成功" in result or "success" in result.lower():
            print("✅ API连接测试成功")
        else:
            print(f"⚠️ API响应异常: {result}")
            
    except Exception as e:
        print(f"❌ API连接测试失败: {e}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 创新药论文分析系统测试")
    print("=" * 60)
    
    # 运行各项测试
    test_file_loading()
    test_data_formatting()
    test_api_connection()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main() 