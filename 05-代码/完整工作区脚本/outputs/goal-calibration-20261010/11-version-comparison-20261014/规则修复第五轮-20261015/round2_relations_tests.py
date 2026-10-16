"""Finite saved-input replays and explicit synthetic relation boundary tests.
No reference labels are read and no saved corpus input/output is rewritten.
"""
import copy, hashlib, json, pathlib, sys
sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE/'code'))
import relations, dimensions, evidence

new_ids = ['00113','00120','00123','00127','00129','00134']
old_ids = ['00125','00132','00133','00138','00141','04162','04197','00038','00118']
wanted = {'RECODE25-'+s for s in new_ids+old_ids}
source = ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
units = {r['id']: r['semantic_unit'] for r in map(json.loads, source.open()) if r['id'] in wanted}

def run(unit):
    view = relations.RelationView(unit)
    decisions = dimensions.judge(view)
    evidence.validate_decisions(view.unit, decisions)
    return view, {dim:x['value'] for dim,x in decisions.items()}

def types(view):
    return [r['details'].get('relation_subtype') for r in view.traces()]

positives = []
for rid, unit in units.items():
    view, labels = run(unit)
    positives.append({'id':rid, 'labels':labels, 'relations':view.traces(),
                      'unresolved_material_requests':view.material_requests})
expected = {
    '00113':'bounded_current_eligibility_assessment',
    '00120':'bounded_primary_postadmission_technical_support',
    '00123':'bounded_current_eligibility_assessment',
    '00127':'bounded_primary_postadmission_technical_support',
    '00134':'bounded_primary_postadmission_technical_support',
}
for item in positives:
    suffix=item['id'].split('-')[-1]
    if suffix in expected:
        assert expected[suffix] in [r['details'].get('relation_subtype') for r in item['relations']], suffix
assert not next(r for r in positives if r['id'].endswith('00123'))['unresolved_material_requests']
assert not next(r for r in positives if r['id'].endswith('00129'))['relations']
assert next(r for r in positives if r['id'].endswith('00129'))['labels'] == dict(S=0,E=0,Ec=0,I=0,F=0)

# Equal-length synthetic paraphrases keep supplied source coordinates valid.
# All text occurrences in the in-memory bundle are changed consistently, given
# a distinct synthetic source SHA, and never represented as policy evidence.
def variant(unit, old, new):
    assert len(old)==len(new), (old,new)
    assert old in unit['text'], old
    original_sha=unit['source_ref']['sha256']
    synthetic_sha=hashlib.sha256(('SYNTHETIC_TEST_ONLY:'+old+'>'+new+original_sha).encode()).hexdigest()
    def transform(value):
        if isinstance(value,str):
            return value.replace(old,new).replace(original_sha,synthetic_sha)
        if isinstance(value,list): return [transform(x) for x in value]
        if isinstance(value,dict):
            obj={k:transform(v) for k,v in value.items()}
            if isinstance(obj.get('text'),str):
                for key in ('text_sha256','text_utf8_sha256'):
                    if key in obj:obj[key]=hashlib.sha256(obj['text'].encode()).hexdigest()
            return obj
        return value
    out=transform(copy.deepcopy(unit))
    for c in out.get('contexts',[]):
        origin=out.get('derived_context_origins',{}).get(c['context_id'],{})
        if origin.get('origin_inventory_view')=='text':
            origin['origin_inventory_view_sha256']=hashlib.sha256(c.get('text','').encode()).hexdigest()
    return out

paraphrases=[]
for suffix,old,new in [
    ('00113','进行论证','开展论证'),
    ('00120','内无异议','内无反对'),
    ('00123','应当及时终止','必须及时终止'),
    ('00127','优先安排','优先提供'),
    ('00129','初步审查','初步审核'),
    ('00134','按要求提交','按规定提交'),
]:
    v,labels=run(variant(units['RECODE25-'+suffix],old,new))
    if suffix in expected:
        assert expected[suffix] in types(v),(suffix,types(v))
    else:
        assert 'bounded_current_priority_resource' not in types(v)
    paraphrases.append({'based_on':suffix,'synthetic_only':True,'replacement':[old,new],
                       'required_relation_preserved':expected.get(suffix, 'priority_inheritance_retracted'),'labels':labels})

negatives=[]
for suffix,old,new in [
    ('00113','是否符合','仅仅记载'),
    ('00120','即纳入','已纳入'),
    ('00123','不符合纳入条件','未提交申报材料'),
    ('00127','优先安排','一般安排'),
    ('00129','组织核查','记录核查'),
    ('00134','经沟通交流确认','未经沟通及确认'),
]:
    v,labels=run(variant(units['RECODE25-'+suffix],old,new))
    assert expected.get(suffix,'bounded_current_priority_resource') not in types(v),(suffix,types(v))
    negatives.append({'based_on':suffix,'synthetic_only':True,'replacement':[old,new],
                      'target_relation_absent':expected.get(suffix,'bounded_current_priority_resource'),'labels_not_accuracy_claim':labels})

# Neither a distant programme title nor current action without its governing
# scope can produce these relations. Keep actual current wording unchanged.
for suffix in new_ids:
    u=copy.deepcopy(units['RECODE25-'+suffix])
    u['contexts']=[c for c in u['contexts'] if c['kind']!='source_textleaf']
    v,_=run(u)
    assert expected.get(suffix,'bounded_current_priority_resource') not in types(v),suffix
    negatives.append({'based_on':suffix,'synthetic_only':True,'missing_closed_primary_source':True,
                      'target_relation_absent':expected.get(suffix,'bounded_current_priority_resource')})

# Source/component near-neighbors must not be substituted for the actual
# antecedent: confirmatory submission needs its own same-source paragraph.
u=copy.deepcopy(units['RECODE25-00134'])
u['contexts']=[c for c in u['contexts'] if c['kind']!='paragraph']
v,_=run(u)
assert expected['00134'] not in types(v)
negatives.append({'name':'confirmed_submission_missing_same_paragraph','synthetic_only':True,'passed':True})

assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
out={'scope':'15 saved-source deterministic replays, 6 synthetic equal-length paraphrases, 13 boundary controls; not independent validation',
     'saved_replays':positives,'synthetic_paraphrases':paraphrases,'synthetic_boundary_controls':negatives,
     'original_input_unchanged':True,'original_input_sha256':source_hash,
     'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'code').glob('*.py')}}
(HERE/'round2-relations-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'saved_replays':[(r['id'],r['labels']) for r in positives],
                  'paraphrases_passed':len(paraphrases),'boundary_controls_passed':len(negatives)},ensure_ascii=False))
