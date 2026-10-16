"""Build only this independent candidate from frozen modules and preserved patches."""
from pathlib import Path
import difflib, hashlib, json

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / 'full4481-rule-production-adapter-sol'


def build():
    dimensions = (FROZEN / 'dimensions.py').read_text()
    dimensions = dimensions.replace('for dim in DIMENSIONS:\n        if not re.search(TOPICS[dim], text):',
        'for dim in DIMENSIONS:\n        if dim in ("S", "E", "Ec"):\n            continue\n        if unit.details.get("affected_dimensions") is not None and dim not in unit.details["affected_dimensions"]:\n            continue\n        if not re.search(TOPICS[dim], text):', 1)
    # The existing function bodies remain in the diff as disclosed origin;
    # later definitions deliberately replace only S/E and Ec consumers.
    append = (HERE / 'se_predicates.inc').read_text()
    dimensions = dimensions.replace('\ndef judge(view) -> dict:', '\n' + append + '\n\ndef judge(view) -> dict:', 1)
    dimensions = dimensions.replace('        _innovation(acc, unit, obj)\n        _fairness(acc, unit, obj)',
        '        consumers = unit.details.get("affected_dimensions")\n        if consumers is None or "I" in consumers:\n            _innovation(acc, unit, obj)\n        if consumers is None or "F" in consumers:\n            _fairness(acc, unit, obj)', 1)
    for dim, section in [('S','三'),('E','四'),('Ec','五')]:
        dimensions = dimensions.replace(f'"{dim}": "v1.3F human4澄清候选（未正式冻结） §一、§二、§{section}"',
            f'"{dim}": "冻结共同手册5ea7ab74 §一、§二、§{section}；非真人规则执行候选"')
    relations = (FROZEN / 'relations.py').read_text()
    relations = relations.replace('        self._complete_source_relations()\n',
        '        self._complete_source_relations()\n        self._se_bounded_content()\n        self._se_operational_references()\n', 1)
    relations += '\n' + (HERE / 'se_relations.inc').read_text()
    for name, text in [('dimensions.py',dimensions),('relations.py',relations)]:
        compile(text, str(HERE/name), 'exec')
        (HERE/name).write_text(text)
        patch = ''.join(difflib.unified_diff((FROZEN/name).read_text().splitlines(True),text.splitlines(True),fromfile='frozen/'+name,tofile='SE-candidate/'+name))
        (HERE/(name+'.patch')).write_text(patch)
    modules=[]
    for name in ('source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py'):
        p=HERE/name;raw=p.read_bytes()
        modules.append({'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
    (HERE/'algorithm-bindings.json').write_text(json.dumps({'version':'rule-v20-SE-Ec-execution-repair-candidate',
        'modules':modules, 'development_only':True,'formal_validation_complete':False,'human_gold_labels_used':False},ensure_ascii=False,indent=2)+'\n')
    print('Built independent S/E/Ec candidate; frozen files untouched.')


if __name__=='__main__':
    build()
