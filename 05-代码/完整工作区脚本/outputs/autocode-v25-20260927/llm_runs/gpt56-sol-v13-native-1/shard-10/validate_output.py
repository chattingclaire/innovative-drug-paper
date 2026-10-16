"""No reference labels or inference: JSON shape and literal-evidence audit only."""
import json, sys
from pathlib import Path
DIMS=['S','E','Ec','I','F']
def iter_text(value):
    if isinstance(value,str):
        yield value
    elif isinstance(value,list):
        for v in value:yield from iter_text(v)
    elif isinstance(value,dict):
        for k,v in value.items():
            if k in {'text','headers','row_cells','caption','definition','title','note'}:
                yield from iter_text(v)
            elif isinstance(v,(dict,list)):
                yield from iter_text(v)

def validate(output, inputs):
    errors=[]
    if output.get('protocol_version')!='CAL-5D-20260926-v1.3':errors.append('protocol_version')
    rows=output.get('rows',[])
    if [r.get('id') for r in rows]!=[r['id'] for r in inputs]:return errors+['ID_count_order_or_duplicate']
    for row,inp in zip(rows,inputs):
        bid=row['id'];labels=row['labels']
        if set(labels)!=set(DIMS):errors.append(f'{bid}:dimensions')
        for d,v in labels.items():
            if not (type(v) is int and v in (0,1) or v=='待定'):errors.append(f'{bid}:{d}:label_type')
            if not row['dimension_reasons'].get(d,'').strip():errors.append(f'{bid}:{d}:reason')
            if v==1 and not any(e['dimension']==d and e['source']=='unit' for e in row['evidence']):
                errors.append(f'{bid}:{d}:missing_unit_evidence')
        if '待定' in labels.values() and set(labels.values())!={'待定'}:errors.append(f'{bid}:partial_pending_not_current_contract')
        for e in row['evidence']:
            hay=[inp['text']] if e['source']=='unit' else list(iter_text(inp.get('contexts',{})))
            if not any(e['quote'] in t for t in hay):errors.append(f'{bid}:{e["dimension"]}:nonliteral_evidence')
        for d,key in [('F','fairness_subtypes'),('I','innovation_subtypes')]:
            if (labels[d]==1) != bool(row[key]):errors.append(f'{bid}:{key}:label_conflict')
        if labels['S']=='待定' and row['safety_quality_basis']!='undetermined':errors.append(f'{bid}:S_pending_basis')
        if labels['S']==0 and row['safety_quality_basis']!='no_quality_basis':errors.append(f'{bid}:S_zero_basis')
        if labels['S']==1 and row['safety_quality_basis']=='undetermined':errors.append(f'{bid}:S_positive_basis')
    return errors

def shape(value, spec, location='root'):
    problems=[]
    if 'enum' in spec and not any(type(value) is type(v) and value==v for v in spec['enum']):
        problems.append(location+':enum')
    kind=spec.get('type')
    if kind=='object':
        if not isinstance(value,dict):return problems+[location+':object']
        keys=set(spec['properties'])
        if set(value)!=keys:problems.append(location+':fields')
        for k in keys & set(value):problems+=shape(value[k],spec['properties'][k],location+'.'+k)
    elif kind=='array':
        if not isinstance(value,list):return problems+[location+':array']
        if spec.get('uniqueItems') and len({json.dumps(v,sort_keys=True) for v in value})!=len(value):problems.append(location+':duplicate')
        for i,v in enumerate(value):problems+=shape(v,spec['items'],location+f'[{i}]')
    elif kind=='string':
        if not isinstance(value,str):problems.append(location+':string')
        elif len(value)<spec.get('minLength',0):problems.append(location+':short')
    return problems

if __name__=='__main__':
    packet=Path(sys.argv[1]);output=Path(sys.argv[2]);here=Path(__file__).resolve().parent
    assert packet.resolve().parent==here and output.resolve().parent==here
    inp=json.loads(packet.read_text())['rows'];result=json.loads(output.read_text())
    errors=shape(result,json.loads((here/'output_schema.json').read_text()))
    if not errors:errors+=validate(result,inp)
    print(json.dumps({'n':len(inp),'errors':errors,'valid':not errors},ensure_ascii=False))
    sys.exit(1 if errors else 0)
