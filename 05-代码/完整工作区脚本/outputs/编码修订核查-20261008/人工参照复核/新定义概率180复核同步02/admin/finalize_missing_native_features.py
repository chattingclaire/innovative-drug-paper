from pathlib import Path
from urllib.parse import quote
import hashlib,html,json,re,zipfile,xml.etree.ElementTree as E
OUT=Path(__file__).resolve().parent.parent
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
RID='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
sha=lambda b:hashlib.sha256(b).hexdigest()
logs=[]
for coder in ['A','B']:
 p=OUT/coder/f'编码员{coder}-新定义180条待填-同步02.xlsx';before=p.read_bytes()
 with zipfile.ZipFile(p) as z:infos=z.infolist();members={n:z.read(n) for n in z.namelist()}
 changed={};target='xl/worksheets/sheet2.xml'
 new,n=re.subn(rb'(<(?:[A-Za-z0-9_]+:)?dataValidation)(\s)',rb'\1 allowBlank="1"\2',members[target]);assert n==1
 assert E.fromstring(new).find('.//{'+NS+'}dataValidation').get('allowBlank')=='1';changed[target]=new
 manifests=json.loads((OUT/'admin'/f'native_hyperlinks_{coder}.json').read_text())
 for sheet,kind in [(3,'current'),(4,'contexts')]:
  key=f'xl/worksheets/sheet{sheet}.xml';xml=members[key].decode();root=E.fromstring(xml)
  assert root.find('{'+NS+'}hyperlinks') is None
  prefix=re.search(r'<((?:[A-Za-z0-9_]+:)?)worksheet\b',xml).group(1)
  relroot=E.Element('Relationships',{'xmlns':REL});hs=[]
  for k,item in enumerate(manifests[kind],1):
   r=f'rIdMaterial{k}';hs.append(f'<{prefix}hyperlink xmlns:r="{RID}" ref="{item["cell"]}" r:id="{r}"/>')
   E.SubElement(relroot,'Relationship',{'Id':r,'Type':RID+'/hyperlink','Target':quote(item['target'],safe='/#'),'TargetMode':'External'})
  content=f'<{prefix}hyperlinks>'+''.join(hs)+f'</{prefix}hyperlinks>'
  after=['printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst']
  positions=[xml.find('<'+prefix+t) for t in after if xml.find('<'+prefix+t)>=0]
  pos=min(positions) if positions else xml.rfind('</'+prefix+'worksheet>');assert pos>=0
  changed[key]=(xml[:pos]+content+xml[pos:]).encode()
  changed[f'xl/worksheets/_rels/sheet{sheet}.xml.rels']=E.tostring(relroot,encoding='utf-8',xml_declaration=True)
  assert len(E.fromstring(changed[key]).find('{'+NS+'}hyperlinks'))==len(manifests[kind])
 temp=p.with_suffix('.xlsx.tmp')
 with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED) as z:
  for info in infos:z.writestr(info,changed.get(info.filename,members[info.filename]))
  for k,v in changed.items():
   if k not in members:z.writestr(k,v)
 with zipfile.ZipFile(temp) as z:
  assert all(z.read(k)==v for k,v in members.items() if k not in changed)
 temp.replace(p)
 logs.append({'coder':coder,'before_sha256':sha(before),'after_sha256':sha(p.read_bytes()),'changed_entries':{k:sha(v) for k,v in changed.items()},'hyperlinks':sum(len(v) for v in manifests.values()),'unaffected_zip_member_bytes_equal':True,'source_or_answer_values_changed':False})
 aux=Path(str(p)+'.inspect.ndjson')
 if aux.exists():aux.rename(OUT/'admin'/f'final_export_inspect_{coder}.ndjson')
j={'purpose':'Minimal native XLSX serialization for missing Artifact Tool capabilities: exported allowBlank and unimplemented HYPERLINK calculation. Workbook authoring/rendering remains Artifact Tool; HYPERLINK formulas replaced by visible text in builder, then native hyperlinks added without formula caches.','records':logs}
(OUT/'admin/native_feature_finalization.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'workbooks_finalized':len(logs),'native_hyperlinks_per_workbook':[r['hyperlinks'] for r in logs]}))
