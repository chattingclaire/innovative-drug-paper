import json,sys
from pathlib import Path
base=Path('outputs/ai-audit800-20261010/source-A/coder-A/materials')
for i in range(int(sys.argv[1]),int(sys.argv[2])+1):
 d=json.loads((base/f'A-{i:06}.json').read_text());r=d['source_record']; print('\n###',i,r['id']);print(r['text'])
 for c in r.get('contexts',[]):
  if c.get('text')==r['text'] or c.get('kind','').startswith('same_snapshot') or c.get('kind') in ['source_fragment','document_context','ordered_members']:continue
  print(c.get('context_id'),c.get('kind'),c.get('text',c.get('row_cells',c.get('headers','nontext metadata'))))
 print('Resources:',[(k,len(d.get(k,[]))) for k in ['explicit_or_primary_source_resources','preserved_historical_neutral_source_supplements','source_full_text_resources','source_provenance_addenda','source_reference_index'] if d.get(k)])
