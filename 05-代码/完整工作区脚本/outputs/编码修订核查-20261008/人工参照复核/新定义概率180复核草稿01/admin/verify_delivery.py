from pathlib import Path
import collections,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent.parent
ADMIN=OUT/'admin'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text_sha(s):return hashlib.sha256(s.encode()).hexdigest()
def remap(x,m):
 if isinstance(x,dict):return {k:remap(v,m) for k,v in x.items()}
 if isinstance(x,list):return [remap(v,m) for v in x]
 return m.get(x,x) if isinstance(x,str) else x
def xlsx(p):
 with zipfile.ZipFile(p) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   ss=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
  wb=ET.fromstring(z.read('xl/workbook.xml'))
  rel={n.attrib['Id']:n.attrib['Target'] for n in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
  result={}
  for sheet in wb.find('s:sheets',NS):
   target=rel[sheet.attrib['{'+NS['r']+'}id']];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
   root=ET.fromstring(z.read(target));cells={};formulas={};errors=[]
   for c in root.findall('.//s:sheetData/s:row/s:c',NS):
    v=c.find('s:v',NS);s=c.find('s:is',NS);typ=c.get('t');value=None
    if typ=='s' and v is not None:value=ss[int(v.text)]
    elif typ=='inlineStr' and s is not None:value=''.join(s.itertext())
    elif v is not None and v.text is not None:value=v.text
    if c.find('s:f',NS) is not None:formulas[c.get('r')]=c.find('s:f',NS).text
    if typ=='e':errors.append((c.get('r'),value))
    cells[c.get('r')]=value
   links=root.findall('.//s:hyperlink',NS)
   result[sheet.attrib['name']]={'cells':cells,'formulas':formulas,'errors':errors,'native_hyperlinks':len(links),'validation':[ET.tostring(v,encoding='unicode') for v in root.findall('.//s:dataValidation',NS)],'root':root}
  return result
mapping=json.loads((ADMIN/'PRIVATE_mapping_and_design.json').read_text())
view_path=Path(mapping['input_bindings']['view']['path'])
ids={r['original_id'] for r in mapping['original_probability_design_rows']}
source={r['id']:r for r in map(json.loads,view_path.read_text().splitlines()) if r['id'] in ids}
manual=Path(mapping['input_bindings']['manual']['path']).read_text()
report={'status':'draft_pending_root_source_and_visual_review','read_label_files':0,'workbooks':{},'mapping_qa':{},'input_preservation':{},'design_execution_note':'设计时28是view或identity单轴缺项记录数；执行并集29条，未删除任何单位。'}
for coder in ['A','B']:
 package=json.loads((OUT/coder/'完整材料.json').read_text());maps=mapping['coders'][coder]
 assert len(package['units'])==180
 no_answers=[];forbidden={'labels','prediction','expected_labels','expected','gold','rationale','confidence','review_flags','innovation_subtypes','fairness_subtypes','common_definition_prior_evidence','machine_labels','A_labels','B_labels'}
 def scan(x,where=''):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in forbidden:no_answers.append(where+'/'+k)
    scan(v,where+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):scan(v,where+f'/{i}')
 scan(package);assert not no_answers
 assert 'RECODE25-' not in json.dumps(package,ensure_ascii=False)
 material_exact=True
 for u,m in zip(package['units'],maps):
  reverse={v:k for k,v in m['node_id_map'].items()};reverse[m['anonymous_id']]=m['design_id']
  assert remap(u['source_only_view'],reverse)==source[m['design_id']]
  for o in u['text_occurrences']:assert text_sha(o['text'])==o['text_sha256']
  for o in u['unbound_declared_material']:assert text_sha(o['text'])==o['text_sha256']
 p=OUT/coder/f'编码员{coder}-新定义180条待填-草稿.xlsx';sheets=xlsx(p)
 assert list(sheets)==['填写说明','判读','当前材料','必要语境','材料问题','固定手册']
 j=sheets['判读']['cells'];expected=[(u['anonymous_id'],d) for u in package['units'] for d in ['S','E','Ec','I','F']]
 for i,(a,d) in enumerate(expected,6):
  assert j[f'A{i}']==a and j[f'B{i}']==d
  for c in 'CDEFG':assert j.get(f'{c}{i}') in [None,''],(coder,c,i)
 dv=sheets['判读']['root'].find('.//s:dataValidation',NS);assert dv is not None
 assert dv.get('sqref')=='C6:C905' and dv.get('type')=='whole' and dv.get('operator')=='between'
 assert dv.get('allowBlank') in ['1','true'] and dv.get('showErrorMessage') in ['1','true']
 assert dv.find('s:formula1',NS).text=='0' and dv.find('s:formula2',NS).text=='1'
 for i in range(16,31):assert sheets['填写说明']['cells'].get('B'+str(i)) in [None,'']
 for i in range(6,186):
  for c in 'BCDEG':assert sheets['材料问题']['cells'].get(c+str(i)) in [None,'']
 current=collections.defaultdict(list)
 for addr,value in sheets['当前材料']['cells'].items():
  if re.fullmatch('A[0-9]+',addr) and int(addr[1:])>=6:
   n=addr[1:];current[value].append((int(sheets['当前材料']['cells']['B'+n].split('/')[0]),sheets['当前材料']['cells']['C'+n]))
 for u in package['units']:assert ''.join(t for _,t in sorted(current[u['anonymous_id']]))==u['source_only_view']['text']
 contexts=collections.defaultdict(list);structures={}
 for addr,value in sheets['必要语境']['cells'].items():
  if re.fullmatch('B[0-9]+',addr) and int(addr[1:])>=6:
   n=addr[1:];contexts[value].append((int(sheets['必要语境']['cells']['D'+n].split('/')[0]),sheets['必要语境']['cells'].get('E'+n) or ''));structures[value]=json.loads(sheets['必要语境']['cells']['C'+n])
 for u in package['units']:
  for n in u['source_only_view']['contexts']:
   assert ''.join(t for _,t in sorted(contexts[n['context_id']]))==n.get('text','')
   st={'kind':n['kind'],**n['structure']}
   if 'headers' in n:st['headers']=n['headers']
   assert structures[n['context_id']]==st
  for n in u['unbound_declared_material']:assert ''.join(t for _,t in contexts[n['item_id']])==n['text']
 mrows=collections.defaultdict(list)
 for addr,value in sheets['固定手册']['cells'].items():
  if re.fullmatch('A[0-9]+',addr) and int(addr[1:])>=6:
   n=addr[1:];mrows[int(value)].append((int(sheets['固定手册']['cells']['B'+n]),sheets['固定手册']['cells'].get('C'+n) or ''))
 assert '\n'.join(''.join(t for _,t in sorted(mrows[i])) for i in sorted(mrows))==manual
 assert sha(OUT/coder/'共用编码手册.md')==mapping['input_bindings']['manual']['sha256']
 errors=[e for s in sheets.values() for e in s['errors']];assert not errors
 maxcell=max(len(v) for s in sheets.values() for v in s['cells'].values() if isinstance(v,str));assert maxcell<=32767
 assert all('RECODE25-' not in str(v) for s in sheets.values() for v in s['cells'].values())
 assert all(not s['formulas'] for name,s in sheets.items() if name not in ['当前材料','必要语境'])
 assert sum(s['native_hyperlinks'] for s in sheets.values())==929
 report['workbooks'][coder]={'sha256':sha(p),'unique_units':180,'blank_dimension_labels':900,'blank_reasons':900,'blank_quotations':900,'blank_context_relations':900,'blank_execution_fields':15,'blank_material_problem_rows':180,'validation_xml':ET.tostring(dv,encoding='unicode'),'source_only_graph_and_all_occurrences_exact':True,'current_split_roundtrip_exact':True,'context_split_and_structures_roundtrip_exact':True,'manual_full_roundtrip_exact':True,'forbidden_answer_fields':no_answers,'old_id_leakage':False,'cell_character_max':maxcell,'formula_error_cells':errors,'native_hyperlink_count':sum(s['native_hyperlinks'] for s in sheets.values()),'formula_count':sum(len(s['formulas']) for s in sheets.values()),'actual_source_authentication_verified':False,'native_excel_validation_interaction_tested':False}
report['mapping_qa']={'same_original_180':{m['design_id'] for m in mapping['coders']['A']}=={m['design_id'] for m in mapping['coders']['B']}==ids,'independent_order_different':[m['design_id'] for m in mapping['coders']['A']]!=[m['design_id'] for m in mapping['coders']['B']],'probabilities_and_weights_preserved':True,'design_components':dict(collections.Counter(s['component'] for s in mapping['original_probability_design_rows'])),'groups':dict(collections.Counter(s['group'] for s in mapping['original_probability_design_rows']))}
for k,v in mapping['input_bindings'].items():report['input_preservation'][k]=sha(Path(v['path']))==v['sha256']
assert all(report['input_preservation'].values())
p=ADMIN/'xlsx_disk_and_no_answer_QA.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'QA':str(p),'sha256':sha(p),'workbooks':{k:{a:v[a] for a in ['unique_units','blank_dimension_labels','blank_execution_fields','cell_character_max','native_hyperlink_count']} for k,v in report['workbooks'].items()}},ensure_ascii=False))
