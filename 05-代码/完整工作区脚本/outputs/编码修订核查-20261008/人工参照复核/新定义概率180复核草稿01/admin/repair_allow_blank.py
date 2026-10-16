from pathlib import Path
import hashlib,json,re,zipfile,xml.etree.ElementTree as E
out=Path(__file__).resolve().parent.parent
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
sha=lambda b:hashlib.sha256(b).hexdigest()
records=[]
for coder in ['A','B']:
 p=out/coder/f'编码员{coder}-新定义180条待填-草稿.xlsx';before=p.read_bytes()
 with zipfile.ZipFile(p) as z:
  entries={n:z.read(n) for n in z.namelist()};infos=z.infolist()
 target='xl/worksheets/sheet2.xml';original=entries[target]
 dv=E.fromstring(original).find('.//s:dataValidation',ns)
 assert dv.get('allowBlank') is None and dv.get('sqref')=='C6:C905'
 fixed,n=re.subn(rb'(<(?:[A-Za-z0-9_]+:)?dataValidation)(\s)',rb'\1 allowBlank="1"\2',original)
 assert n==1 and E.fromstring(fixed).find('.//s:dataValidation',ns).get('allowBlank')=='1'
 tmp=p.with_suffix('.xlsx.tmp')
 with zipfile.ZipFile(tmp,'w') as z:
  for info in infos:z.writestr(info,fixed if info.filename==target else entries[info.filename])
 with zipfile.ZipFile(tmp) as z:changed=[n for n,b in entries.items() if z.read(n)!=b]
 assert changed==[target];tmp.replace(p)
 records.append({'coder':coder,'before_xlsx_sha256':sha(before),'after_xlsx_sha256':sha(p.read_bytes()),'changed_entry':target,'before_entry_sha256':sha(original),'after_entry_sha256':sha(fixed),'only_mutation':'insert allowBlank="1" on existing C6:C905 whole 0..1 validation; all other ZIP member bytes unchanged'})
 aux=Path(str(p)+'.inspect.ndjson')
 if aux.exists():aux.rename(out/'admin'/f'export_inspect_{coder}.ndjson')
q={'reason':'Artifact Tool public allowBlank:true was supplied but absent in exported XML. Minimal missing-capability serialization repair. No values, formulas, text or graphics changed.','records':records}
(out/'admin/validation_export_repair.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'patched_workbooks':len(records),'changes_per_workbook':1}))
