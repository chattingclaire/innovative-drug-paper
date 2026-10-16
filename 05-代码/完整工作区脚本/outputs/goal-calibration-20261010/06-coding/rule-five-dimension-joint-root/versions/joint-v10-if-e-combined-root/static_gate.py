"""Frozen pure V10 nomination gate; normalization matches unchanged evidence.py."""
import re
import unicodedata
V10_REPAIR_ENTRY = '其他[^。；;]{0,30}优先审评审批[^。；;]{0,12}情形|(?:工具|表征|评估)[^。；;]{0,100}(?:沟通|接受)|(?:建立|完善|实施)[^。；;]{0,80}支持创新[^。；;]{0,30}机制|(?:审核|符合)[^。；;]{0,35}药品试验数据保护条件[^。；;]{0,50}(?:执行|实施)|(?:开展|实施)[^。；;]{0,18}试点|(?:项目申请前|临床试验申请前)[^。；;]{0,120}沟通交流|临床试验机构[^。；;]{0,65}(?:培训|技术能力)'

def matching_current(raw):
    joined=''.join(unicodedata.normalize('NFKC',char) for char in raw)
    return re.sub(r'(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])','',joined)

def normalized_gate(text):
    return bool(re.search(V10_REPAIR_ENTRY,text))

def if_gate(raw):
    return normalized_gate(matching_current(raw))

E_OUTCOME_ENTRY = '完\\s*全\\s*应\\s*答\\s*率|部\\s*分\\s*应\\s*答\\s*率|客\\s*观\\s*应\\s*答\\s*率|完\\s*全\\s*缓\\s*解\\s*率|部\\s*分\\s*缓\\s*解\\s*率|客\\s*观\\s*缓\\s*解\\s*率'

def _e_outcome_gate(text):
    """Necessary superset gate: only raw current text, no source/label/context feature."""
    return bool(re.search(E_OUTCOME_ENTRY, text))


def gate(raw):
    return if_gate(raw) or _e_outcome_gate(raw)
