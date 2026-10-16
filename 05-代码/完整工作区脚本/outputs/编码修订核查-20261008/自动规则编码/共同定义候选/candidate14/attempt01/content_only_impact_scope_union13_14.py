"""Conservative deterministic semantic/evidence impact envelope vs frozen13.

Union of both releases' input guards. This deliberately includes regressions
that no longer trigger14. It never reads old predictions/labels or metrics;
no source authentication or coding occurs. Full classifications are required
later to know realised label changes. Release metadata changes on every row.
"""
import argparse,hashlib,importlib.util,json,re,sys
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent.parent/'candidate13/attempt01'
sys.path.insert(0,str(H/'runtime'))
import common_innovation_relations14 as I14
import common_medicine_access14 as F14
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=json.loads((P/'candidate13_freeze.json').read_text())
for name in ('common_innovation_relations13.py','common_medicine_access13.py'):
    assert sha(P/'runtime'/name)==freeze['runtime_files'][name]
def load(name):
    spec=importlib.util.spec_from_file_location(name,P/'runtime'/f'{name}.py');m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m
I13=load('common_innovation_relations13');F13=load('common_medicine_access13')

def scope(record):
    text=record.get('unit_text','');oldI=[];oldF=[]
    if I13.current_scientific_guidance(text):oldI.append('parent13_current_scientific_guidance')
    if re.search(r'鼓励(?:新药)?研发人员与药品技术审评机构密切沟通|如有未能阐明的个性化问题[，,]\s*可采用沟通交流的方式解决',text):oldI.append('parent13_technical_communication')
    # Remaining13 I guards are unchanged/supersets in the14 entry envelope.
    for gate in I14.trigger_reasons(record):
        if gate in {'first_communication_bounded_program','qualified_protection_comparison','adopted_decimal_requirement'}:oldI.append('parent13_'+gate)
    if F13._SHORTAGE.search(F13._TITLE.sub(lambda m:' '*len(m.group()),text)) and not F13._CARRIER.search(text):oldF.append('parent13_shortage_priority')
    if F13._PRIORITY.search(text) and re.search(r'以下|下列|同时满足|应满足|相关条件',text):oldF.append('parent13_required_shortage_priority_list')
    if F13.current_direct_access(text):oldF.append('parent13_current_direct_access_including_retired_speed')
    reasons={'new14_I':I14.trigger_reasons(record),'new14_F':F14.trigger_reasons(record),'parent13_I':oldI,'parent13_F':oldF}
    return dict(potential_semantic_or_evidence_impact=any(reasons.values()),reasons=reasons,
        current_text_sha256=hashlib.sha256(text.encode()).hexdigest(),classification_performed=False,
        old_predictions_labels_metrics_identity_used=False,source_authentication_performed=False,
        scope_kind='union-of-source-only-input-guards, conservative potential envelope; no claim every row changes',
        parent13_runtime_sources_sha256={n:freeze['runtime_files'][n] for n in ('common_innovation_relations13.py','common_medicine_access13.py')})

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=[];count=0
    for ln in Path(a.input).open():
        x=json.loads(ln);s=scope(x.get('input',x));count+=1
        if s['potential_semantic_or_evidence_impact']:s['id']=x.get('id') or x.get('unit_id');out.append(s)
    Path(a.output).write_text(json.dumps(dict(input_path=str(Path(a.input).resolve()),input_sha256=sha(a.input),source_rows_read=count,
        coding_count=0,rows=out,metadata_version_impact='Every coded output uses new release metadata; union envelope covers possible semantic/evidence differences only.',manual_sha256=I14.MANUAL_SHA256),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
