#!/usr/bin/env python3
"""
Batch LLM coding for all 3387 sentences.
Uses Claude API to code each sentence into evaluation dimensions.
Processes in batches of 50 sentences, saves progress after each batch.
"""
import json, os, time
import anthropic

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'all_sentences.json')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'llm_all_results.json')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, 'llm_progress.json')
BATCH_SIZE = 50

SYSTEM_PROMPT = """你是一个政策文本编码专家。你的任务是判断每个句子涉及哪些创新药评价维度。

五个维度的定义：
1. 安全性：涉及药品安全、不良反应、毒性、风险管理、药物警戒、质量控制等
2. 有效性：涉及药品疗效、临床价值、临床获益、临床试验结果、循证证据等（注意：仅提及临床试验的行政程序/管理规定不算有效性，必须涉及对药物疗效的实质性评价）
3. 经济性：涉及费用、价格、成本、支付、报销、医保基金、谈判、预算等
4. 创新性：涉及创新药、新药研发、优先审评、突破性治疗、附条件批准、临床急需等
5. 公平性：涉及公平可及、基层用药、基本药物、罕见病、儿童用药、供应保障、合理用药等

规则：
- 一个句子可以涉及0个或多个维度
- 只有当句子实质性地涉及某个维度时才编码，提及不等于涉及
- 返回JSON数组格式"""

def code_batch(client, sentences):
    """Code a batch of sentences using Claude API."""
    prompt = "请对以下句子进行维度编码，每个句子返回涉及的维度列表。\n\n"
    for s in sentences:
        prompt += f"[ID {s['id']}] {s['sent']}\n\n"
    prompt += "\n请返回JSON格式，例如：\n[{\"id\": 0, \"dims\": [\"安全性\", \"有效性\"]}, {\"id\": 1, \"dims\": []}]\n\n只返回JSON，不要其他内容。"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    
    text = response.content[0].text.strip()
    # Extract JSON from response
    if text.startswith('```'):
        text = text.split('\n', 1)[1]
        if text.endswith('```'):
            text = text[:-3]
    
    return json.loads(text)

def main():
    with open(INPUT_FILE) as f:
        all_sentences = json.load(f)
    
    # Load progress
    results = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
            results = {r['id']: r['dims'] for r in progress}
        print(f"已有进度: {len(results)}/{len(all_sentences)} 句")
    
    # Find remaining sentences
    remaining = [s for s in all_sentences if s['id'] not in results]
    print(f"剩余: {len(remaining)} 句, 约 {len(remaining)//BATCH_SIZE + 1} 批")
    
    if not remaining:
        print("全部完成!")
        return
    
    client = anthropic.Anthropic()
    
    batch_num = 0
    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i+BATCH_SIZE]
        batch_num += 1
        total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"Batch {batch_num}/{total_batches} (ID {batch[0]['id']}—{batch[-1]['id']})...", end=' ', flush=True)
        
        try:
            coded = code_batch(client, batch)
            for r in coded:
                results[r['id']] = r['dims']
            print(f"OK ({len(coded)} sentences)")
        except Exception as e:
            print(f"ERROR: {e}")
            # Try one more time
            time.sleep(2)
            try:
                coded = code_batch(client, batch)
                for r in coded:
                    results[r['id']] = r['dims']
                print(f"OK (retry)")
            except Exception as e2:
                print(f"FAILED: {e2}, saving progress and stopping")
                break
        
        # Save progress after each batch
        progress_list = [{'id': k, 'dims': v} for k, v in sorted(results.items())]
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_list, f, ensure_ascii=False)
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
    
    # Save final results
    final = [{'id': k, 'dims': v} for k, v in sorted(results.items())]
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成: {len(results)}/{len(all_sentences)} 句")
    print(f"保存: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
