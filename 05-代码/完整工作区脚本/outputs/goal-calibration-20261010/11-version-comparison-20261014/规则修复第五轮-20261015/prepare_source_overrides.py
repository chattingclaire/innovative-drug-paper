"""Project already declared original UTF-8 source; never classify or read labels."""
from pathlib import Path
import copy,hashlib,json,re,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'code'))
import source_packet,evidence

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def save(name,x):(HERE/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
OLD=ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl'
TARGETS={'RECODE25-04589','RECODE25-04614'}
units={r['id']:r['semantic_unit'] for r in map(json.loads,OLD.open()) if r['id'] in TARGETS}
assert set(units)==TARGETS
s0=next(iter(units.values()))
specs=[d for d in s0['source_bundle']['source_documents'] if d['source_sha256']==s0['source_ref']['sha256']]
assert len(specs)==1
spec=specs[0];path=Path(spec['snapshot']);raw=path.read_bytes();digest=sha(raw)
assert digest==spec['source_sha256'] and len(raw)==spec['bytes']
text=raw.decode('utf-8');assert text.encode()==raw
lines=text.splitlines(keepends=True);offsets=[0]
for line in lines:offsets.append(offsets[-1]+len(line))
assert ''.join(lines)==text

def locator(first,last):
 a,b=offsets[first-1],offsets[last]
 return {'kind':'verbatim_UTF8_snapshot_text','coordinate_basis':'original strict UTF8 snapshot; Unicode codepoints and UTF8 bytes; no normalization',
 'snapshot_absolute_path':str(path),'snapshot_sha256':digest,
 'physical_line_interval_inclusive_1based':[first,last],'physical_line_range_1based_inclusive':[first,last],
 'unicode_code_point_interval_half_open':[a,b],
 'utf8_byte_interval_half_open':[len(text[:a].encode()),len(text[:b].encode())],
 'physical_pages':None,'PDF_page_or_pixel_locator_available':False}
full_id='SOURCE-TEXT-'+digest+'-COMPLETE-UTF8'
full={'kind':'verbatim_UTF8_snapshot_text','source_resource_id':full_id,'source_sha256':digest,
 'source_version_id':'SOURCEVERSION-'+digest,'text':text,'text_unicode_code_points':len(text),'text_utf8_bytes':len(raw),
 'text_utf8_sha256':digest,'locator':locator(1,len(lines))}
doc_id='SOURCE-ORDERED-UTF8-'+digest
members=[]
for i,line in enumerate(lines,1):
 loc=locator(i,i)
 members.append({'source_resource_id':f'{doc_id}-L{i:04d}','source_document_resource_id':'SOURCE-'+digest,
 'source_sha256':digest,'source_version_id':'SOURCEVERSION-'+digest,'text':line,'text_sha256':sha(line.encode()),
 'representation':'literal original UTF8 physical line including line ending','source_locator':loc,
 'source_ref':{'sha256':digest,'source_resource_id':'SOURCE-'+digest,'locator':copy.deepcopy(loc)}})
heading=re.compile(r'^第[一二三四五六七八九十百零〇两]+[条章节](?:\s.*)?$')
article=re.compile(r'^第[一二三四五六七八九十百零〇两]+条$')
groups=[]
for i,line in enumerate(lines):
 label=line.strip()
 if not article.fullmatch(label):continue
 j=i+1
 while j<len(lines) and not heading.fullmatch(lines[j].strip()):j+=1
 assert j>i+1
 selected=members[i+1:j]
 for pos,m in enumerate(selected,1):m.update(article=label,clause_index_one_based=pos)
 groups.append({'article':label,'source_sha256':digest,'ordered_source_resource_ids':[m['source_resource_id'] for m in selected],
 'article_heading_source_resource_id':members[i]['source_resource_id'],
 'next_boundary_source_resource_id':members[j]['source_resource_id'] if j<len(members) else None,
 'article_with_heading_locator':locator(i+1,j),'body_locator':locator(i+2,j),
 'closure_basis':'all original physical lines after exact article heading and before next original article/chapter/section heading or source EOF'})
assert len({g['article'] for g in groups})==len(groups)
for name in ['第五十九条','第六十条','第六十一条','第六十八条','第六十九条','第七十条','第九十六条']:
 assert len([g for g in groups if g['article']==name])==1
ordered={'source_resource_id':doc_id,'source_sha256':digest,'snapshot_sha256':digest,
 'source_version_id':'SOURCEVERSION-'+digest,'source_snapshot':str(path),
 'representation':'complete original UTF8 body projected as ordered physical lines and literal article headings',
 'complete_text_resource_id':full_id,'full_text_utf8_sha256':digest,'full_text_unicode_code_points':len(text),
 'source_texts':members,'ordered_article_groups':groups,
 'component_identity_status':'original snapshot and old contexts contain no explicit component ID; no component ID inferred'}
# Check literal source coordinates before invoking the existing adapter.
for leaf,loc in [(full,full['locator'])]+[(m,m['source_locator']) for m in members]:
 a,b=loc['unicode_code_point_interval_half_open'];ba,bb=loc['utf8_byte_interval_half_open'];first,last=loc['physical_line_interval_inclusive_1based']
 assert text[a:b]==leaf['text'] and raw[ba:bb]==leaf['text'].encode()
 assert ''.join(lines[first-1:last])==leaf['text']
 assert sha(raw[ba:bb])==leaf.get('text_utf8_sha256',leaf.get('text_sha256'))
outputs={};bindings=[]
for sid,old in sorted(units.items()):
 assert old['source_ref']['sha256']==digest
 assert any(d['snapshot']==str(path) and d['source_sha256']==digest for d in old['source_bundle']['source_documents'])
 bundle=copy.deepcopy(old['source_bundle']);original_bundle=copy.deepcopy(bundle)
 # The saved semantic bundle has no record ID; the adapter intentionally omits IDs.
 baseline=source_packet.semantic_unit(bundle)
 assert baseline==old, 'Existing adapter must first exactly reproduce saved semantic unit'
 bundle['source_full_text_resources'].append(copy.deepcopy(full))
 bundle['explicit_or_primary_source_resources'].append(copy.deepcopy(ordered))
 new=source_packet.semantic_unit(bundle)
 assert new['text']==old['text'] and new['source_ref']==old['source_ref']
 assert new['contexts'][:len(old['contexts'])]==old['contexts']
 for key in old:
  if key not in ['source_bundle','contexts','derived_context_origins']:assert new[key]==old[key]
 assert {k:new['derived_context_origins'][k] for k in old['derived_context_origins']}==old['derived_context_origins']
 for key in original_bundle:
  if key not in ['source_full_text_resources','explicit_or_primary_source_resources']:assert bundle[key]==original_bundle[key]
 # Inventory validation needs an administrative id only in this separate validation copy.
 inv_bundle=copy.deepcopy(bundle);inv_bundle['source_record']['id']=sid
 inventory=source_packet.source_inventory(inv_bundle)
 assert len({x['resource_id'] for x in inventory})==len(inventory)
 assert len({c['context_id'] for c in new['contexts']})==len(new['contexts'])
 # Validate every derived reference against its exact raw bundle pointer and text.
 added=new['contexts'][len(old['contexts']):]
 for c in added:
  origin=new['derived_context_origins'][c['context_id']];v=new['source_bundle']
  for part in origin['source_bundle_pointer'].strip('/').split('/'):v=v[int(part)] if isinstance(v,list) else v[part]
  assert c['text']==v['text'] and c['source_ref']['sha256']==digest
  a=evidence.context_anchor(new,c['context_id'],0,len(c['text']),'source_projection_structure_check_only')
  assert a['text']==c['text']
 outputs[sid]=new
 bindings.append({'id':sid,'old_semantic_sha256':sha(canonical(old)),'new_semantic_sha256':sha(canonical(new)),
 'source_record_unchanged':new['source_bundle']['source_record']==old['source_bundle']['source_record'],
 'current_text_and_source_ref_unchanged':True,'old_contexts_exact_prefix':True,'old_derived_origins_unchanged':True,
 'added_context_N':len(added),'source_inventory_N':len(inventory),'classification_run':False})
save('semantic-overrides.json',outputs)
save('source-projection-bindings.json',{'source_snapshot':str(path),'source_sha256':digest,'source_bytes':len(raw),
 'unicode_code_points':len(text),'physical_lines':len(lines),'article_groups':len(groups),
 'old_effective_inputs_sha256':sha(OLD.read_bytes()),'adapter_sha256':sha((HERE/'code/source_packet.py').read_bytes()),
 'semantic_overrides_sha256':sha((HERE/'semantic-overrides.json').read_bytes()),'records':bindings,
 'checks':['declared original byte SHA/size','strict UTF8 roundtrip','all line slices and Unicode/byte offsets','all literal hashes','adapter baseline exact reproduction','old current/contexts/origins unchanged','unique inventory/context IDs','all new evidence anchor/pointer literal texts'],
 'no_classification_or_human_labels_read':True,'component_ID_invented':False})
save('source-projection-article-index.json',groups)
print(json.dumps({'records':len(outputs),'lines':len(lines),'articles':len(groups),'source_sha256':digest,'added_context_N':bindings[0]['added_context_N']},ensure_ascii=False))
