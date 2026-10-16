"""Current-unit structural role; no dimension detector or inherited label.

Only a whole unit consisting of a structural pointer is classified as pure.
Mixed units retain their substantive clauses. Source authentication and missing
material gates remain the caller's responsibility.
"""
import hashlib
import re

VERSION = 'measurement-current-unit-role-02'
_PURE = re.compile(
    r'\s*(?:[(（]?[一二三四五六七八九十0-9]+[)）.、]\s*)?'
    r'(?:(?:这些|上述|以下|下列|相关|其|主要|具体|基本|有关|本)[^，,。；;：:\n]{0,18}'
    r'(?:特征|特点|内容|方面|条件|情形|要求|事项|范围|资料|材料|问题|项目)|'
    r'(?:特征|特点|内容|方面|条件|情形|要求|事项|范围|资料|材料|问题|项目))'
    r'(?:包括(?:但不限于)?|包含|如下|为|有|主要包括|主要有)'
    r'(?:以下|下列|如下)?(?:几个|各个|[一二三四五六七八九十0-9]+个)?'
    r'(?:方面|内容|条件|情形|要求|事项|资料|材料|问题|项目)?\s*[:：]\s*'
)
_POINTER = re.compile(r'以下|下列|如下|上述|前述|同时满足')
_SUBSTANTIVE = re.compile(
    r'(?:应当|应|须|需|必须|需要)(?:当)?(?:包括|包含|提供|提交|补充|评价|评估|考虑|满足|符合|证明|阐明|说明)'
    r'|(?:满足|符合)(?:以下|下列|上述|前述)(?:条件|要求)'
    r'|(?:评价|评估|比较|调出|纳入)[^。；;]{0,25}(?:以下|下列|条件|情形)'
    r'|(?:可以|可|允许|不再|不予)?(?:申请适用|申请|适用|给予|享受|获得|取消|停止)'
    r'[^。；;]{0,25}(?:优先审评审批|加快审评|审评通道|支持|保障|沟通交流|数据保护)'
)


def classify(text):
    pure = bool(_PURE.fullmatch(text))
    # The final pointed list is governed by its own actual sentence. An
    # evaluation requirement in another sentence cannot license its expansion.
    # Commas/semicolons may join a condition and its arrangement, so they are
    # not mechanical sentence boundaries here.
    pointers=list(_POINTER.finditer(text))
    pointer=pointers[-1] if pointers else None
    sentence_start=(max(text.rfind(c,0,pointer.start()) for c in '。！？!?\n')+1
                    if pointer else 0)
    sentence=text[sentence_start:]
    local_predicate=_SUBSTANTIVE.search(sentence) if pointer else None
    predicate_anchor=(dict(start=sentence_start+local_predicate.start(),
        end=sentence_start+local_predicate.end(),
        text=text[sentence_start+local_predicate.start():sentence_start+local_predicate.end()])
        if local_predicate else None)
    # A complete pure tail is still structural even in a mixed unit. This
    # does not zero the earlier independent substantive propositions.
    pure_tail=bool(_PURE.fullmatch(sentence)) and sentence_start>0
    role = ('structural_reference_only' if pure else
            'substantive_list_lead' if predicate_anchor and not pure_tail else
            'enumerated_member' if re.match(r'^\s*[(（]?[一二三四五六七八九十0-9]+[)）.、]', text) else
            'ordinary_or_mixed_substantive_unit')
    return dict(version=VERSION, role=role, current_unit_sha256=hashlib.sha256(text.encode()).hexdigest(),
        whole_unit_structural_match=pure, labels_from_members_used=False,
        pointer_sentence_start=sentence_start if pointer else None,
        structural_tail_in_mixed_unit=pure_tail,
        current_substantive_predicate=predicate_anchor if not pure and not pure_tail else None)


def permits_content_expansion(text):
    return classify(text)['role'] == 'substantive_list_lead'
