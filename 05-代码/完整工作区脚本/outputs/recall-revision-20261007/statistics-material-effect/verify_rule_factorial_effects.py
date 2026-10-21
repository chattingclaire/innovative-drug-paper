"""Independent 2x2 decomposition of material and classifier synonym changes."""
from pathlib import Path
import hashlib
import json

ROOT=Path('/PROJECT_ROOT')
OUT=Path(__file__).resolve().parent
RUN=OUT.parent/'rules-v31'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    data=[json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    rows={r['id']:r for r in data}
    assert len(data)==len(rows)==4924
    return rows


def main():
    stems={'C1_M1':'all_predictions_completed_material',
           'C1_M2':'all_predictions_material_v2_classifier_v1_control',
           'C2_M1':'all_predictions_material_v1_classifier_v2_control',
           'C2_M2':'all_predictions_completed_material_v2'}
    expected={'C1_M1':'e9c0ec1085008f2b81a0afd4ec83bdc2c088bc48a9367865da5af42a3406a961',
              'C1_M2':'755e85f92c852656bce8f0e04e8b76ae1b80c0e8f634b0323bcf79f1884c482f',
              'C2_M1':'698807588a70ea623351cc036c209f34a64d1124a41f208f4f6fc6d3bf5e8b93',
              'C2_M2':'aef7348228d9741814eca9293360a3a6996687aa0a74f62db3aa5d8d2494883c'}
    pred={};manifests={};sources={str(Path(__file__)):sha(Path(__file__))}
    inputs={}
    for key,stem in stems.items():
        path=RUN/f'{stem}.jsonl';mp=RUN/f'{stem}.run.json'
        assert sha(path)==expected[key]
        manifest=json.loads(mp.read_text())
        assert manifest['n']==4924 and manifest['pending_n']==0 and manifest['reference_labels_loaded'] is False
        assert manifest['prediction_sha256']==sha(path)
        input_path=Path(manifest['input_path'])
        assert sha(input_path)==manifest['input_sha256']
        inp=read(input_path)
        rows=read(path)
        assert set(inp)==set(rows)
        for rid,row in rows.items():
            p=row['prediction']
            assert p['version']==manifest['version']
            assert p['unit_text_sha256']==hashlib.sha256(inp[rid]['input']['unit_text'].encode()).hexdigest()
            assert all(type(v) is int and v in (0,1) for v in p['labels'].values())
        for name,digest in manifest['runtime_code_sha256'].items():
            assert sha(Path(name))==digest
            sources[name]=digest
        pred[key]=rows;manifests[key]=manifest;inputs[key]=inp
        for p in (path,mp,input_path):sources[str(p)]=sha(p)
    for key in stems:
        assert set(inputs[key])==set(inputs['C1_M1'])
        for rid,row in inputs[key].items():
            assert row['original_id']==inputs['C1_M1'][rid]['original_id']
            assert row['input']['unit_text']==inputs['C1_M1'][rid]['input']['unit_text']
    # Certificate validation may differ to authenticate the new material.
    # Every actual classification source must match within each C factor.
    for a,b in (('C1_M1','C1_M2'),('C2_M1','C2_M2')):
        codes=lambda x:{Path(k).name:v for k,v in manifests[x]['runtime_code_sha256'].items() if Path(k).name!='context_validation.py'}
        assert codes(a)==codes(b)
    contrasts=[]
    for a,b,effect in (('C1_M1','C1_M2','material_only_with_original_classifier'),
                       ('C2_M1','C2_M2','material_only_with_synonym_classifier'),
                       ('C1_M1','C2_M1','classifier_only_on_material_v1'),
                       ('C1_M2','C2_M2','classifier_only_on_material_v2')):
        changes=[]
        for rid in pred[a]:
            for d in ('S','E','Ec','I','F'):
                x,y=pred[a][rid]['prediction']['labels'][d],pred[b][rid]['prediction']['labels'][d]
                if x!=y:
                    changes.append({'id':rid,'dimension':d,'old':x,'new':y,'unit_text':inputs[a][rid]['input']['unit_text']})
        contrasts.append({'old_condition':a,'new_condition':b,'effect':effect,'changed_id_dimensions_n':len(changes),'changes':changes})
    assert [r['changed_id_dimensions_n'] for r in contrasts]==[2,3,0,1]
    assert {r['id'] for r in contrasts[0]['changes']}=={'RECODE25-01580','RECODE25-01672'}
    assert contrasts[3]['changes'][0]['id']=='RECODE25-02077' and contrasts[3]['changes'][0]['dimension']=='F'
    assert sources=={p:sha(Path(p)) for p in sources}
    report={'status':'passed','scope':'Read-only development decomposition; not final validation or a new statistical specification.',
        'factor_definitions':{'C1':'Original v31 recall boundary classifier',
                              'C2':'Same classifier with agreement/negotiation object synonym recognition',
                              'M1':'Frozen uniform source-context completion v1',
                              'M2':'v1 plus verified renewal object scopes in 434 units'},
        'actual_runs_per_condition':{key:{'prediction':str(RUN/f'{stem}.jsonl'),'sha256':expected[key],
                                        'version':manifests[key]['version'],'input_sha256':manifests[key]['input_sha256']} for key,stem in stems.items()},
        'ids_and_unit_texts_identical':4924,'classification_code_identity_within_each_factor':True,
        'contrasts':contrasts,'reference_labels_or_metrics_loaded':False,
        'interpretation':'The extra object context enables a classifier object-scope correction for one already-covered management-category sentence. That interaction is separate from two economic-dimension changes caused by the material alone.',
        'source_sha256':sources}
    path=OUT/'规则材料与同义识别2x2独立核验.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'passed','contrasts':contrasts,'output':str(path)},ensure_ascii=False))


if __name__=='__main__':main()
