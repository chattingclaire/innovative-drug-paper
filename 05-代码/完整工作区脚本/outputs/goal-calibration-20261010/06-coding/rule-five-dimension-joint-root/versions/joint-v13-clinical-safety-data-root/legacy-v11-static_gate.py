"""Pure current-only V11 gate. No classifier import or source access."""
import re
import unicodedata
V11_REPAIR_ENTRY = '数据保护|受保护[^。；;]{0,6}数据'

def matching_current(raw):
    joined = "".join(unicodedata.normalize("NFKC", char) for char in raw)
    return re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", joined)

def normalized_gate(text):
    return bool(re.search(V11_REPAIR_ENTRY, text))

def gate(raw):
    return normalized_gate(matching_current(raw))
