"""Complete source-verified list predicates and table headers, without labels."""
from pathlib import Path
from hashlib import sha256
import json, re, unicodedata, subprocess
import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'final-three-department-20261007'
ARCHIVE = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914')

def sha(path): return sha256(Path(path).read_bytes()).hexdigest()
def canonical(text): return ''.join(c for c in unicodedata.normalize('NFKC', text) if c.isalnum())
def load_rows(path): return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def rank(text):
    text = unicodedata.normalize('NFKC', text.strip())
    if re.match(r'^(?:第[一二三四五六七八九十百]+条|规则[一二三四五六七八九十]+|附则)',text): return 0
    for pattern, level in [(r'^[一二三四五六七八九十]+、',1), (r'^\([一二三四五六七八九十]+\)',2),
                           (r'^\d+[.、]',3), (r'^\(\d+\)',4),
                           (r'^\d+\s*(?:协议|近|由于|临床|药品|20\d{2}|纳入|经国家|药监|符合|按|本协议|市场)',5)]:
        if re.match(pattern, text): return level
    return None

cache = {}
def source_text(path):
    path = Path(path)
    if path not in cache:
        if path.suffix.lower() == '.pdf':
            doc = pdfium.PdfDocument(path)
            pages=[]
            for n in range(len(doc)):
                lines=doc[n].get_textpage().get_text_range().splitlines()
                # Running page numbers interrupt sentences crossing a page.
                # Remove only an exact page number at the extraction's edge.
                for edge in (0,-1):
                    if lines and lines[edge].strip()==str(n+1): lines.pop(edge)
                pages.append('\n'.join(lines))
            text = '\n'.join(pages)
        elif path.suffix.lower() == '.doc':
            text = subprocess.run(['textutil','-convert','txt','-stdout',str(path)],check=True,capture_output=True,text=True).stdout
        else: text = path.read_text()
        cache[path] = text
    return cache[path]

rules = load_rows(BASE/'rules-v30/rule_inputs_v30_shared.jsonl')
llm = load_rows(BASE/'llm-v29/effective_blind_inputs_v29.jsonl')
assert len(rules) == len(llm) == 4924
assert [x['id'] for x in rules] == [x['id'] for x in llm]
original_rules = json.loads(json.dumps(rules))
original_llm = json.loads(json.dumps(llm))
proposals = json.loads((HERE/'parent_list_context_proposals.json').read_text())
candidates = {x['candidate_file']:json.loads(Path(x['candidate_file']).read_text()) for x in proposals}
blocks = []
for proposal in proposals:
    ps = candidates[proposal['candidate_file']]['paragraphs']
    start = next(n for n,p in enumerate(ps) if p['id']==proposal['parent']['id'])
    level = rank(ps[start+1]['text']) if start+1<len(ps) else None
    children = []
    if level:
        parent_source = proposal['parent'].get('source_file') or proposal['source']
        for child in ps[start+1:]:
            child_source = child.get('source_file') or proposal['source']
            r = rank(child['text'])
            if child_source != parent_source or (r is not None and r < level): break
            if child.get('type')=='heading_candidate': break
            children.append(child)
    blocks.append({**proposal,'children':children})

# Additional peer branches found by the source-only structural audit use
# explicit reviewed child intervals; these include local renewal exceptions.
structure_review=json.loads((HERE/'source_context_structure_review.json').read_text())
for recommendation in structure_review['additional_branch_recommendations']:
    file=recommendation['candidate_file']; candidate=candidates[file]
    by_id={p['id']:p for p in candidate['paragraphs']}
    parent=by_id[recommendation['parent']['id']]
    assert parent['text']==recommendation['parent']['text']
    children=[by_id[i] for i in recommendation['child_ids']]
    blocks.append({'candidate_file':file,'source':recommendation['actual_source_path'],
                   'parent':parent,'children':children,'context_role':'reviewed_additional_branch'})

# A continuation such as "符合本条件" refers to the immediately preceding
# numbered item as well as the outer introduction, not to all peer items.
for block in list(blocks):
    previous_item=None
    for child in block['children']:
        if rank(child['text']) is not None:
            previous_item=child
        elif re.match(r'^符合本条件',child['text']) and previous_item is not None:
            blocks.append({**block,'parent':previous_item,'children':[child]})

# Add the explicit nested removal/payment-range headings within annual lists.
for file, candidate in candidates.items():
    ps = candidate['paragraphs']
    for n,parent in enumerate(ps[:-1]):
        if not (re.search(r'(?:调出目录|调整支付标准).{0,8}药品的?范围[。.:：]?$',parent['text'])
                or re.search(r'按以下规则确定支付标准后纳入常规目录管理[:：]$',parent['text'])): continue
        level = rank(ps[n+1]['text']); children=[]
        if level is None: continue
        for child in ps[n+1:]:
            r=rank(child['text'])
            if child.get('type')=='heading_candidate' or (r is not None and r<level): break
            children.append(child)
        blocks.append({'candidate_file':file,'source':candidate['source'],'parent':parent,'children':children})

# The normal-directory conversion branch retains its stated existing-drug
# object through its rules/procedure, until the next named rule or attachment.
# Do not extend other renewal conditions across "四、其他" local exceptions.
for proposal in proposals:
    parent=proposal['parent']
    if not re.search(r'满足以下条件之一.*可以纳入常规目录管理',parent['text']): continue
    ps=candidates[proposal['candidate_file']]['paragraphs']
    start=next(n for n,p in enumerate(ps) if p['id']==parent['id'])
    source=parent.get('source_file') or proposal['source']; branch=[]
    for child in ps[start+1:]:
        if (child.get('source_file') or proposal['source'])!=source: break
        if re.match(r'^(?:规则[一二三四五六七八九十]+|附则)',child['text']): break
        branch.append(child)
    blocks.append({**proposal,'children':branch,'context_role':'normal_directory_branch_object'})
    numbered={}
    for child in ps[start+1:]:
        match=re.match(r'^(\d+)[.、]',child['text'])
        if child.get('type')=='heading_candidate': break
        if match: numbered[match.group(1)]=child
    for child in branch:
        match=re.search(r'条件\s*(\d+)',child['text'])
        if match and match.group(1) in numbered:
            blocks.append({**proposal,'parent':numbered[match.group(1)],'children':[child],
                           'context_role':'explicit_numbered_antecedent'})
            for nested in list(blocks):
                if (nested['candidate_file']==proposal['candidate_file']
                        and nested['parent']['id']==child['id']):
                    blocks.append({**proposal,'parent':numbered[match.group(1)],
                                   'children':nested['children'],'context_role':'numbered_antecedent_chain'})

for block in list(blocks):
    for child in block['children']:
        if not re.search(r'取\s*1\s*和\s*2\s*两者',child['text']): continue
        for sibling in block['children']:
            if re.match(r'^[12](?:按|本协议)',sibling['text']):
                blocks.append({**block,'parent':sibling,'children':[child],
                               'context_role':'explicit_formula_antecedent'})

lookup = {}
source_checks = []
for block in blocks:
    parent=block['parent']; source=Path(parent.get('source_file') or block['source'])
    assert canonical(parent['text']) in canonical(source_text(source)), (source,parent['id'])
    source_checks.append({'source':str(source),'source_sha256':sha(source),'candidate':block['candidate_file'],
                          'parent_id':parent['id'],'parent_text':parent['text'],
                          'children':[c['id'] for c in block['children']],
                          'verification':'NFKC alphanumeric sequence in source extraction; structure interval separately reviewed'})
    for child in block['children']:
        lookup.setdefault((block['candidate_file'],child['id']),[]).append((parent,source))

changed=[]
for row, model in zip(rules,llm):
    record=row['input']; contexts=model['contexts']; additions=[]
    for p in record.get('paragraph_context',[]):
        for parent,source in lookup.get((record['candidate_file'],p['paragraph_id']),[]):
            existing=record.get('verified_parent_context',[])+additions
            if any(canonical(x.get('text',''))==canonical(parent['text']) for x in existing): continue
            if canonical(parent['text']) in canonical(record['unit_text']): continue
            additions.append({'paragraph_id':parent['id'],'text':parent['text'],'pages':parent.get('pages',[]),
                'text_sha256':sha256(parent['text'].encode()).hexdigest(),
                'source_path':str(source),'source_sha256':sha(source),
                'candidate_path':record['candidate_file'],'candidate_sha256':sha(record['candidate_file']),
                'original_unit_sha256':sha256(record['unit_text'].encode()).hexdigest(),
                'unit_id':record['unit_id'],'repair_version':'v31-source-list-predicate',
                'source_lines':parent.get('line_ids',[]),
                'verification':{'verified':True,'method':'normalized_source_text_and_reviewed_list_interval'},
                'usage':'Only restore the applicable list predicate/object. Do not inherit unrelated labels or treat application eligibility as actual insurance coverage.'})
    if additions:
        record.setdefault('verified_parent_context',[]).extend(additions)
        contexts.setdefault('verified_parent_context',[]).extend(json.loads(json.dumps(additions)))
        contexts.setdefault('verified_context_certificates',{})['verified_parent_context']=json.loads(json.dumps(contexts['verified_parent_context']))
        changed.append({'id':row['id'],'kind':'list_predicate','added_parent_ids':[x['paragraph_id'] for x in additions]})

# The same header is supplied to all 40 rows of the original monitoring table.
table_doc=ARCHIVE/'12-投稿定稿工作区/原文补全/附件：各省行动效果监测指标体系.doc'
header='各省行动效果监测指标体系\n序号\n评估维度\n评估指标\n指标导向'
assert header in source_text(table_doc)
for row,model in zip(rules,llm):
    record=row['input']
    if record.get('unit_source') != str(table_doc): continue
    cert={'text':header,'header_cells':['序号','评估维度','评估指标','指标导向'],
          'source_path':str(table_doc),'source_sha256':sha(table_doc),
          'usage':'Map the four original cells to their columns; the table is healthcare action monitoring, not a drug-specific value score.'}
    model['contexts']['verified_table_header']=cert
    record['verified_table_header']=json.loads(json.dumps(cert))
    changed.append({'id':row['id'],'kind':'table_header'})

for oldr,newr,oldl,newl in zip(original_rules,rules,original_llm,llm):
    assert oldr['input']['unit_text']==newr['input']['unit_text']==oldl['text']==newl['text']
    assert oldr['id']==newr['id']==oldl['id']==newl['id']
    for c in newr['input'].get('verified_parent_context',[]):
        if c.get('repair_version')=='v31-source-list-predicate':
            assert c['source_sha256']==(newr['input'].get('unit_source_sha256') or newr['input'].get('source_sha256'))
    newr['input']['llm_v29_shared_context']=json.loads(json.dumps(newl['contexts']))
    assert newr['input']['llm_v29_shared_context']==newl['contexts']
rp=HERE/'rule_inputs_v31_shared.jsonl'; lp=HERE/'effective_blind_inputs_v30.jsonl'
rp.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rules))
lp.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in llm))
manifest={'status':'source_verified_material_completion','n':4924,'labels_added_or_changed':False,
    'unit_texts_unchanged':4924,'rules_and_llm_contexts_identical':4924,
    'rule_input_sha256':sha(rp),'llm_input_sha256':sha(lp),
    'changed_unit_count':len({x['id'] for x in changed}),'changes':changed,'source_parent_checks':source_checks,
    'table_header_source':{'path':str(table_doc),'sha256':sha(table_doc),'header':header},
    'limits':'Repairs the source-defined list branches and this complete table. Source integrity/structure does not alone prove semantic coding accuracy.'}
(HERE/'uniform_context_completion_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['status','n','changed_unit_count','rule_input_sha256','llm_input_sha256']},ensure_ascii=False))
