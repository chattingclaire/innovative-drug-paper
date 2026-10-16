"""Attach source-verified object scope. Contains no predicted/reference labels."""
from pathlib import Path
import hashlib,json,copy,re
from pypdf import PdfReader
D=Path(__file__).resolve().parent
REGISTRY=json.loads((D/'对象适用范围登记.json').read_text())['scopes']
checked=set()
def attach_scope(record):
    out=copy.deepcopy(record)
    for scope in REGISTRY:
        binding=scope.get('source_hash_field','source_sha256')
        assert binding in {'source_sha256','unit_source_sha256'}
        if record.get(binding)!=scope['source_sha256']:continue
        if scope.get('required_branch_text') and re.sub(r'\s+','',(record.get('verified_rule_branch_context') or {}).get('text',''))!=scope['required_branch_text']:continue
        if scope['source_sha256'] not in checked:
            source=Path(scope['source'])
            assert hashlib.sha256(source.read_bytes()).hexdigest()==scope['source_sha256']
            if scope['normalization']=='none':
                assert source.read_text().splitlines()[scope['locator']['line']-1]==scope['text']
            else:
                pdf=PdfReader(source)
                extracted=''.join(pdf.pages[p-1].extract_text() for p in scope['locator']['physical_pages'])
                assert scope['text'] in re.sub(r'\s+','',extracted)
            assert hashlib.sha256(scope['text'].encode()).hexdigest()==scope['text_sha256']
            checked.add(scope['source_sha256'])
        out.setdefault('verified_object_scope',[]).append({
            'kind':scope['kind'],'source_sha256':scope['source_sha256'],
            'source_hash_field':binding, 'required_branch_text':scope.get('required_branch_text'),
            'unit_text_sha256':hashlib.sha256(record['unit_text'].encode()).hexdigest(),
            'text':scope['text'],'text_sha256':scope['text_sha256'],
            'locator':dict(scope['locator'],source=scope['source']),
            'verification':scope['verification'],'normalization':scope['normalization']})
    return out
