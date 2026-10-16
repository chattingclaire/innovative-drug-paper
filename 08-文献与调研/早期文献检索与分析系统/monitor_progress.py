#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file monitor_progress.py
@description 监控分析进度的脚本
@author AI Assistant
@date 2024
"""

import os
import time
import json
from datetime import datetime

def check_analysis_progress():
    """检查分析进度"""
    print("🔍 检查分析进度...")
    
    # 检查输出文件
    output_file = "academic_paper_analysis_results.json"
    stats_file = "analysis_statistics.json"
    
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                results = json.load(f)
            
            print(f"✅ 分析结果文件存在")
            print(f"📄 已分析论文数: {len(results)}")
            
            # 显示最新分析的论文
            if results:
                latest_result = results[-1]
                print(f"📝 最新分析论文: {latest_result.get('paper_id', 'N/A')}")
                print(f"⏰ 分析时间: {latest_result.get('original_paper', {}).get('analysis_timestamp', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 读取结果文件失败: {e}")
    else:
        print(f"⏳ 分析结果文件尚未生成")
    
    # 检查统计文件
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
            
            print(f"✅ 统计文件存在")
            print(f"📊 总论文数: {stats.get('total_papers', 0)}")
            print(f"✅ 成功分析: {stats.get('successful_analysis', 0)}")
            
        except Exception as e:
            print(f"❌ 读取统计文件失败: {e}")
    else:
        print(f"⏳ 统计文件尚未生成")
    
    # 检查进程状态
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'academic_paper_analyzer.py' in result.stdout:
            print("🔄 分析进程正在运行")
        else:
            print("⏹️ 分析进程已结束")
    except Exception as e:
        print(f"❌ 检查进程状态失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("📊 分析进度监控")
    print("=" * 60)
    
    while True:
        check_analysis_progress()
        print(f"\n⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # 等待30秒后再次检查
        time.sleep(30)

if __name__ == "__main__":
    main() 