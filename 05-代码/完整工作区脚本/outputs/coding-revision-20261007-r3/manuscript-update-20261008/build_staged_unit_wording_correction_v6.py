"""Single authorized P83 wording correction; preserve sealed v5 and all statistical inputs."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE/'完整论文局部替换稿-v5.json'
OUT=HERE/'完整论文局部替换稿-v6.json'
D=HERE/'integration-preflight'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
B=lambda p:{'path':str(p),'sha256':H(p)}
def require(v,msg):
    if not v:raise RuntimeError(msg)
def main():
    require(H(OLD)=='375a6255436bf080d71a19cab04e22c54709368485b033d59d39e87a553d1794','v5 changed')
    review=HERE/'full03-evidence-review-20261008/正式03六定义56构成逐项独立对照QA.json'
    require(H(review)=='59b948ed5d8af18181c2ec8256a58130115480c9817846eeb4dd033440d6e4a2','Review changed')
    frozen=[OLD,HERE/'完整论文局部替换稿-v5.md',HERE/'局部替换稿v5抽样描述修正绑定.json',HERE/'build_staged_sampling_correction_v5.py',*sorted(D.glob('*v5*.*')),*sorted((D/'snapshot-20261008-v5').iterdir())]
    before={p:H(p) for p in frozen if p.is_file()}
    old=json.loads(OLD.read_text());new=json.loads(OLD.read_text());target=next(x for x in new['replacements']if x['zero_based_body_p_index']==83)
    require(target['replacement_text'].count('同句内容组合')==1,'Target not unique')
    target['replacement_text']=target['replacement_text'].replace('同句内容组合','同一单元的内容组合')
    changed=[b['zero_based_body_p_index']for a,b in zip(old['replacements'],new['replacements'])if a!=b]
    require(changed==[83],'Unexpected change')
    require(len(new['replacements'])==52 and len(new['measurement_fields'])==39,'Unexpected scope')
    require(all(old[k]==new[k]for k in old if k!='replacements'),'Top-level changed')
    require(all(a['old_text']==b['old_text']and a['old_text_sha256']==b['old_text_sha256']for a,b in zip(old['replacements'],new['replacements'])),'Anchors changed')
    p47=next(x['replacement_text']for x in new['replacements']if x['zero_based_body_p_index']==47)
    require('按部门简单随机不放回各抽60条，共180条，卫健为框内全查。'in p47,'Sampling operation absent')
    pattern=re.compile(r'\[[0-9,，;；\s–—-]+\]|〔[A-Za-z][A-Za-z0-9_;；,，\s]*〕')
    require([pattern.findall(x['replacement_text'])for x in old['replacements']]==[pattern.findall(x['replacement_text'])for x in new['replacements']],'Citations changed')
    md=HERE/'完整论文局部替换稿-v6.md';delta=HERE/'局部替换稿v6分析单元用语修正绑定.json'
    require(not any(p.exists()for p in [OUT,md,delta]),'Refuse overwrite')
    with OUT.open('x')as f:f.write(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
    text=['# 完整论文局部替换稿 v6','','仅将P83的“同句内容组合”改为“同一单元的内容组合”，与句段及必要语境的分析单元定义一致。其余51段、39字段、所有引用和原文锚点不变；未生成DOCX或变更标签、样本、统计。','']
    for row in new['replacements']:text += [f"P{row['zero_based_body_p_index']}",'',row['replacement_text'],'']
    with md.open('x')as f:f.write('\n'.join(text)+'\n')
    require(all(H(p)==h for p,h in before.items()),'v5 frozen file changed')
    obj={'status':'PASS_SINGLE_P83_ANALYSIS_UNIT_WORDING_CORRECTION_NOT_FINAL_MANUSCRIPT','previous_staged':B(OLD),'new_staged':B(OUT),'preview':B(md),'producer':B(Path(__file__).resolve()),'prior_real03_sensitivity_review':B(review),'changed_paragraphs':changed,'old_phrase':'同句内容组合','new_phrase':'同一单元的内容组合','other51_and_P47_unchanged':True,'all39_fields_and_citation_tokens_and_baseline_anchors_unchanged':True,'no_new_definition_or_method_change':True,'no_DOCX_or_label_or_statistic_mutation':True,'preserved_v5_files':[{'path':str(p),'sha256':h}for p,h in before.items()]}
    with delta.open('x')as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'staged':B(OUT),'delta':B(delta),'protected_v5_files':len(before)},ensure_ascii=False))
if __name__=='__main__':main()
