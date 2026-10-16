# -*- coding: utf-8 -*-
"""Fast-DetectGPT 采样差异度（analytic 版，论文式(5)），逐段打分。
分数越高 = 越接近该语言模型自身的高概率输出 = 越可能由 LLM 生成。"""
import sys, json, re, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
M='Qwen/Qwen2.5-0.5B'
dev='mps' if torch.backends.mps.is_available() else 'cpu'
tok=AutoTokenizer.from_pretrained(M)
mod=AutoModelForCausalLM.from_pretrained(M, dtype=torch.float32).to(dev).eval()

def discrepancy(text):
    """fast-detect-gpt: (logp_x - E[logp]) / sqrt(Var[logp])，同一模型充当采样与打分模型"""
    ids=tok(text, return_tensors='pt', truncation=True, max_length=1024).input_ids.to(dev)
    if ids.shape[1]<24: return None
    with torch.no_grad():
        logits=mod(ids).logits[0,:-1]          # [T-1, V]
    labels=ids[0,1:]
    lprobs=torch.log_softmax(logits.float(), dim=-1)
    probs=lprobs.exp()
    logp_x=lprobs.gather(-1, labels.unsqueeze(-1)).squeeze(-1).sum()
    mean=(probs*lprobs).sum(-1)                 # 每个位置的期望对数概率
    var=(probs*lprobs.square()).sum(-1)-mean.square()
    return ((logp_x-mean.sum())/var.sum().sqrt()).item()

segs=json.load(open(sys.argv[1],encoding='utf-8'))
out=[]
for s in segs:
    d=discrepancy(s['text'])
    if d is not None: out.append({**s,'score':round(d,3),'n':len(s['text'])})
    print('.',end='',flush=True)
print()
json.dump(out, open(sys.argv[2],'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('已评 %d 段 → %s'%(len(out),sys.argv[2]))
