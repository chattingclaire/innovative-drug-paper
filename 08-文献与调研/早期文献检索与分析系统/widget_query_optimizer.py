#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@file widget_query_optimizer.py
@description Widget查询优化器：使用系统提示优化dashboard查询，增加具体性和多样性
"""

import json
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

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

# 扩展的股票代码列表
STOCK_SYMBOLS = [
    "GOOGL", "AAPL", "META", "MSFT", "NVDA", "TSLA", "AMD", "NFLX", "DIS", "AMZN", "JPM", "BAC", "V", "MA",
    "WMT", "PG", "KO", "PEP", "ABT", "JNJ", "UNH", "HD", "MCD", "PFE", "TMO", "ABBV", "AVGO", "COST", "MRK",
    "ACN", "DHR", "NEE", "TXN", "LLY", "UNP", "HON", "RTX", "QCOM", "LOW", "UPS", "INTU", "SPGI", "ISRG",
    "GILD", "ADI", "TGT", "ELV", "PLD", "REGN", "DE", "BDX", "SCHW", "TJX", "CI", "ITW", "CME", "MMC",
    "BLK", "AXP", "GS", "MS", "C", "WFC", "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "ALL", "TRV"
]

# 扩展的加密货币列表
CRYPTO_SYMBOLS = [
    "Bitcoin", "Ethereum", "Solana", "Cardano", "Polkadot", "Chainlink", "Polygon", "Avalanche",
    "BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "MATIC", "AVAX", "BNB", "XRP", "DOGE", "SHIB",
    "Litecoin", "Bitcoin Cash", "Ethereum Classic", "Monero", "Dash", "Zcash", "Tezos", "Algorand"
]

def load_system_prompt():
    """加载系统提示"""
    try:
        with open("widget-query-system-prompt.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
        print(f"✅ 成功加载系统提示")
        return system_prompt
    except FileNotFoundError as e:
        print(f"❌ 系统提示文件未找到: {e}")
        return None

def load_data():
    """加载数据"""
    try:
        with open("dashboard_prompts_extracted.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ 成功加载 {len(data)} 个查询")
        return data
    except FileNotFoundError as e:
        print(f"❌ 数据文件未找到: {e}")
        return []

def llm_optimize_query(query, system_prompt):
    """使用LLM优化单个查询"""
    
    # 随机选择一些股票和加密货币作为示例
    random_stocks = random.sample(STOCK_SYMBOLS, min(5, len(STOCK_SYMBOLS)))
    random_cryptos = random.sample(CRYPTO_SYMBOLS, min(3, len(CRYPTO_SYMBOLS)))
    
    prompt = f"""请根据以下系统提示优化这个查询：

{system_prompt}

输入查询：{query}

请按照系统提示的要求，在保持原始意图和复杂度的基础上，添加具体的股票代码、加密货币、widget名称等具体示例。

可用的股票代码示例：{', '.join(random_stocks)}
可用的加密货币示例：{', '.join(random_cryptos)}

请随机选择并使用这些示例，不要局限于固定的几个。"""

    try:
        response = client.chat.completions.create(
            model="claude-sonnet-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # 增加随机性
        )
        
        result = response.choices[0].message.content
        
        # 清理结果，移除可能的markdown格式
        if result.startswith("```"):
            lines = result.split('\n')
            if len(lines) > 2:
                result = '\n'.join(lines[1:-1])
        
        return result.strip()
            
    except Exception as e:
        print(f"⚠️ LLM调用失败: {str(e)}")
        return None

def optimize_single_query(query_data, system_prompt, query_index, total_count):
    """优化单个查询"""
    original_query = query_data.get("prompt", "")
    
    with progress_lock:
        print(f"🔄 [{query_index+1}/{total_count}] 优化查询: {original_query[:50]}...")
    
    # 使用LLM进行优化
    optimized_query = llm_optimize_query(original_query, system_prompt)
    
    if not optimized_query:
        with progress_lock:
            print(f"   ❌ LLM优化失败")
        return query_data
    
    with progress_lock:
        print(f"   ✅ 优化完成")
        print(f"   📝 原查询: {original_query[:80]}...")
        print(f"   📝 优化后: {optimized_query[:80]}...")
    
    # 返回优化后的查询
    optimized_data = {
        "original_prompt": original_query,
        "optimized_prompt": optimized_query,
        "optimization_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return optimized_data

def process_queries_threaded(queries, system_prompt):
    """多线程处理查询"""
    optimized_queries = []
    results = {}
    
    def worker(args):
        query_data, index = args
        return index, optimize_single_query(query_data, system_prompt, index, len(queries))
    
    # 使用线程池，增加到50个线程
    with ThreadPoolExecutor(max_workers=50) as executor:
        # 提交所有任务
        futures = []
        for i, query_data in enumerate(queries):
            future = executor.submit(worker, (query_data, i))
            futures.append(future)
        
        # 收集结果
        for future in futures:
            try:
                index, optimized_data = future.result()
                with results_lock:
                    results[index] = optimized_data
            except Exception as e:
                print(f"⚠️ 线程处理错误: {e}")
    
    # 按索引顺序整理结果
    for i in range(len(queries)):
        if i in results:
            optimized_queries.append(results[i])
    
    return optimized_queries

def analyze_optimization_results(optimized_queries):
    """分析优化结果"""
    chinese_count = 0
    english_count = 0
    stock_mentions = 0
    crypto_mentions = 0
    widget_mentions = 0
    
    for query_data in optimized_queries:
        optimized_query = query_data.get("optimized_prompt", "")
        
        # 检测语言
        has_chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in optimized_query)
        if has_chinese_chars:
            chinese_count += 1
        else:
            english_count += 1
        
        # 检测股票代码
        if any(symbol in optimized_query for symbol in STOCK_SYMBOLS):
            stock_mentions += 1
        
        # 检测加密货币
        if any(crypto in optimized_query for crypto in CRYPTO_SYMBOLS):
            crypto_mentions += 1
        
        # 检测widget名称
        widget_names = ["TradingView", "Investing.com", "EastMoney", "Baidu Maps", "Bing Maps", "OpenStreetMap", "Windy", "Youku", "Tencent Video", "YouTube", "Vimeo", "Spotify", "Twitter", "Google Docs", "RSS Feed", "Tawk.to", "Crisp Chat", "tlk.io", "Buy Me a Coffee", "Ko-fi", "GitHub Gist", "Swagger UI", "Quizlet", "Desmos", "GoQR.me", "Tencent Docs"]
        if any(widget in optimized_query for widget in widget_names):
            widget_mentions += 1
    
    return {
        "total_queries": len(optimized_queries),
        "chinese_queries": chinese_count,
        "english_queries": english_count,
        "stock_mentions": stock_mentions,
        "crypto_mentions": crypto_mentions,
        "widget_mentions": widget_mentions
    }

def main():
    """主函数"""
    print("=" * 80)
    print("🚀 Widget Query Optimizer")
    print("=" * 80)
    
    # 加载系统提示
    system_prompt = load_system_prompt()
    if not system_prompt:
        return
    
    # 加载数据
    queries = load_data()
    if not queries:
        return
    
    print(f"\n📊 数据统计:")
    print(f"   • 总查询数: {len(queries)}")
    
    # 分析原始数据语言分布
    chinese_count = 0
    english_count = 0
    for query_data in queries:
        query = query_data.get("prompt", "")
        has_chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in query)
        if has_chinese_chars:
            chinese_count += 1
        else:
            english_count += 1
    
    print(f"   • 中文查询: {chinese_count}")
    print(f"   • 英文查询: {english_count}")
    
    print(f"\n🔧 开始多线程优化...")
    
    # 多线程处理
    optimized_queries = process_queries_threaded(queries, system_prompt)
    
    # 保存结果
    output_file = "optimized_widget_queries.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(optimized_queries, f, ensure_ascii=False, indent=2)
    
    # 分析优化结果
    analysis = analyze_optimization_results(optimized_queries)
    
    print(f"\n🎉 优化完成!")
    print("=" * 80)
    print(f"📁 输出文件: {output_file}")
    print(f"📊 总查询数: {analysis['total_queries']}")
    print(f"🇨🇳 中文查询: {analysis['chinese_queries']} 个")
    print(f"🇺🇸 英文查询: {analysis['english_queries']} 个")
    print(f"📈 包含股票代码: {analysis['stock_mentions']} 个")
    print(f"🪙 包含加密货币: {analysis['crypto_mentions']} 个")
    print(f"🔧 包含Widget名称: {analysis['widget_mentions']} 个")
    
    print("=" * 80)
    
    # 显示优化示例
    print(f"\n💡 优化示例:")
    chinese_examples = []
    english_examples = []
    
    for query_data in optimized_queries:
        optimized_query = query_data.get('optimized_prompt', '')
        has_chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in optimized_query)
        
        if has_chinese_chars and len(chinese_examples) < 2:
            chinese_examples.append(query_data)
        elif not has_chinese_chars and len(english_examples) < 3:
            english_examples.append(query_data)
        
        if len(chinese_examples) >= 2 and len(english_examples) >= 3:
            break
    
    for i, query_data in enumerate(chinese_examples + english_examples):
        original_query = query_data.get('original_prompt', '')
        optimized_query = query_data.get('optimized_prompt', '')
        has_chinese_chars = any('\u4e00' <= char <= '\u9fff' for char in optimized_query)
        lang_flag = "🇨🇳" if has_chinese_chars else "🇺🇸"
        
        print(f"\n{lang_flag} 示例 {i+1}:")
        print(f"   原查询: {original_query[:100]}...")
        print(f"   优化后: {optimized_query[:100]}...")

if __name__ == "__main__":
    main() 