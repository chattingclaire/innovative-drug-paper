from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
from lxml import etree
import hashlib,json
base=Path(__file__).resolve().parents[2]
p=base/'outputs/final-three-department-20261008-human-validation-template/创新药评价的注意力配置差异与协调路径.docx'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(p)
assert before=='7cdadcea312180484789926085718cc32ec986c08d498a0d41a9a52e0b4b485a'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+ns['w']+'}'
with ZipFile(p) as z:entries={i.filename:(i,z.read(i.filename)) for i in z.infolist()}
root=etree.fromstring(entries['word/document.xml'][1]);body=root.find('w:body',ns);ps=body.findall('w:p',ns)
plain=lambda x:''.join(x.xpath('.//w:t/text()',namespaces=ns))
assert plain(ps[51]).startswith('表2 ')
refs=[plain(x) for x in ps if plain(x).startswith('[')]
tables=[etree.tostring(x) for x in body.findall('w:tbl',ns)]
new=etree.Element(W+'p');new.append(deepcopy(ps[50].find('w:pPr',ns)))
rpr=ps[50].find('w:r/w:rPr',ns)
def add(text):
 r=etree.SubElement(new,W+'r')
 if rpr is not None:r.append(deepcopy(rpr))
 etree.SubElement(r,W+'t').text=text
add('κ=1表示两套判定完全一致，κ=0表示与按边际比例计算的机会一致相当，负值表示低于机会一致；P、R、F1取值为0—1，越接近1表示相对于所列参照的识别表现越好。参照Halterman和Keith')
cit=[r for r in ps[46].findall('w:r',ns) if '[43]' in plain(r)]
assert len(cit)==1
new.append(deepcopy(cit[0]))
add('按下游任务确定分类表现目标的做法，本文将0.80作为逐维编码检查目标，并结合四格、区间及原句核查解释方法差异。')
ps[50].addnext(new)
assert refs==[plain(x) for x in body.findall('w:p',ns) if plain(x).startswith('[')]
assert tables==[etree.tostring(x) for x in body.findall('w:tbl',ns)]
xml=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
t=p.with_suffix('.staging.docx')
with ZipFile(t,'w',compression=ZIP_DEFLATED) as z:
 for name,(info,data) in entries.items():z.writestr(info,xml if name=='word/document.xml' else data)
t.replace(p)
report={'document':str(p),'before_sha256':before,'after_sha256':sha(p),'new_paragraph':plain(new),'mathematical_interpretation':'Cohen1960 reference46; P/R/F1 definitions reference47','task_specific_target_framework':'HaltermanKeith2026 reference43 section5; that study used F1>0.7, this study 0.80 is its own check target, not their threshold or universal publication rule','no_p_values_calculated':True,'no_metric_numbers_changed':True,'tables_and_all66_references_unchanged':True,'render_status':'PENDING'}
(Path(__file__).parent/'metric_interpretation_revision_binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
