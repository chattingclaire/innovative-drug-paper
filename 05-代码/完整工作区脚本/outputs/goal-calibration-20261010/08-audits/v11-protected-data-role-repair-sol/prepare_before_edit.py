from pathlib import Path
import copy, json, hashlib, datetime
R=Path(__file__).resolve().parents[2]
A=Path(__file__).resolve().parent
V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v11-protected-data-role-sol'
B=V.parent/'joint-v10-if-e-combined-v2-root'
M=R/'01-review/source-interface-v16-article6-addendum-sol'
NAMES=['evidence','source_packet','source_receipts','relations','dimensions']
def h(b):return hashlib.sha256(b).hexdigest()
def bind(p):
 p=p.resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=h(b))
def save(name,x):
 with (A/name).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
packet=M/'packets/RECODE25-01402.json'
raw=json.loads(packet.read_bytes())['source_bundle'];article=raw['explicit_or_primary_source_resources'][1]
literal=[x['text'] for x in article['source_texts'][:4]]
def fixture(texts=None,current=None,mode=None):
 texts=copy.deepcopy(texts or literal);current=current or texts[-1]
 sha=h(('synthetic supplied source\n'+'\n'.join(texts)).encode());htmlsha=h(('synthetic original HTML\n'+'\n'.join(texts)).encode())
 doc=copy.deepcopy(article);doc['source_resource_id']='SYNTHETIC-ARTICLE';doc['source_sha256']=doc['snapshot_sha256']=sha;doc['source_version_id']='SYNTHETIC-VERSION-'+sha;doc['source_document_resource_id']='SOURCE-'+sha;doc['snapshot']='synthetic://complete.json'
 doc['availability_scope']='Synthetic finite original article, not a population asset';doc['representation']='synthetic_same_version_complete_original_article'
 items=[]
 for i,t in enumerate(texts+['第七条']):
  src=copy.deepcopy(article['source_texts'][min(i,4)]);rid='SYNTHETIC-P'+str(i)
  src.update(text=t,text_sha256=h(t.encode()),source_resource_id=rid,source_sha256=sha,source_version_id=doc['source_version_id'],source_document_resource_id='SOURCE-'+sha,article='第六条' if i<len(texts) else '第七条')
  src.pop('neutral_extraction_provenance',None);loc=src['source_locator'];s=loc['structured_snapshot'];ht=loc['raw_html'];s.update(absolute_path='synthetic://complete.json',sha256=sha,json_pointer='/normative_paragraphs/'+str(13+i),normative_paragraphs_index_zero_based=13+i);ht.update(absolute_path='synthetic://complete.html',sha256=htmlsha,p_element_index_zero_based_document_wide=27+i,raw_utf8_byte_interval_half_open=[1000+100*i,1100+100*i]);
  if i<len(texts):src.update(clause_index_one_based=i+1,role='original_normative_paragraph');ht.pop('header_only',None)
  else:src.pop('clause_index_one_based',None);src['role']='next_article_boundary_header_only';ht['header_only']=True
  items.append(src)
 doc['source_texts']=items;g=doc['ordered_article_groups'][0];g.update(ordered_source_resource_ids=[x['source_resource_id'] for x in items[:-1]],next_article_boundary_resource_id=items[-1]['source_resource_id'],raw_HTML_p_indices_zero_based=list(range(27,27+len(texts))),structured_index_range_half_open=[13,13+len(texts)])
 if mode=='missing_holder':
  doc['source_texts']=items[2:];g['ordered_source_resource_ids']=g['ordered_source_resource_ids'][2:]
  for i,x in enumerate(doc['source_texts'][:-1],1):x['clause_index_one_based']=i
  g['structured_index_range_half_open']=[15,17];g['raw_HTML_p_indices_zero_based']=[29,30]
 if mode=='broken_order':doc['source_texts'][1]['source_locator']['structured_snapshot']['normative_paragraphs_index_zero_based']+=1
 if mode=='missing_boundary':doc['source_texts']=doc['source_texts'][:-1]
 if mode=='cross_version':doc['source_texts'][0]['source_sha256']='d'*64
 if mode=='wrong_article':doc['source_texts'][0]['article']='第五条'
 if mode=='duplicate_current':
  duplicate=copy.deepcopy(doc);duplicate['source_resource_id']='SYNTHETIC-OTHER-ARTICLE';duplicate['ordered_article_groups'][0]['article']='第五条'
  for x in duplicate['source_texts'][:-1]:x['article']='第五条'
  duplicate['source_texts'][0]['text']=duplicate['source_texts'][0]['text'].replace('第六条','第五条');duplicate['source_texts'][0]['text_sha256']=h(duplicate['source_texts'][0]['text'].encode())
  docs=[doc,duplicate]
 else:docs=[doc]
 ref=dict(sha256=sha,source_resource_id='SOURCE-'+sha,locator={'paragraph_ids':['p0040']})
 cur=dict(context_id='cur',kind='paragraph',text=current,source_ref={**ref,'locator':{'paragraph_id':'p0040'}},structure={'paragraph_id':'p0040'})
 unit=dict(text=current,source_ref=ref,contexts=[cur],source_bundle={'source_record':{'text':current,'source_ref':ref,'contexts':[cur]},'explicit_or_primary_source_resources':docs},derived_context_origins={})
 for di,d in enumerate(docs):
  for ti,x in enumerate(d['source_texts']):
   cid=f'source-{di}-{ti}';pointer=f'/explicit_or_primary_source_resources/{di}/source_texts/{ti}'
   c=dict(context_id=cid,kind='source_resource_text',text=x['text'],source_ref=dict(sha256=x['source_sha256'],source_resource_id=x['source_document_resource_id'],locator=copy.deepcopy(x['source_locator'])),structure={'source_resource_id':x['source_resource_id'],'source_bundle_pointer':pointer,'article':x['article'],'source_role':x['role']})
   unit['contexts'].append(c);unit['derived_context_origins'][cid]=dict(source_bundle_pointer=pointer,source_resource_id=x['source_resource_id'],role=x['role'],source_sha256=x['source_sha256'],document_resource_id=d['source_resource_id'],origin_inventory_resource_id=x['source_resource_id'],origin_inventory_view='text',origin_inventory_view_sha256=x['text_sha256'])
 return unit
cases=[]
def add(name,u,expected,reason,no_new=False):cases.append(dict(name=name,semantic_input=u,expected=expected,hard_assertion=True,synthetic=True,semantic_reason=reason,must_not_add_v11_positive=no_new))
add('v11_improved_holder_full_article',fixture(),{'I':1},'改良持有人、实质临床优势数据范围、当前限制及自取例外闭合。')
innov=['第六条　自创新药首次境内上市许可之日起，给予6年数据保护期。',literal[-1]]
add('v11_innovative_holder_full_article',fixture(innov),{'I':1},'同条法定创新药持有人的差异化保护权利由当前限制实际执行；不把仿制申请人判创新。')
add('v11_missing_holder_first_paragraphs',fixture(mode='missing_holder'),{'I':None},'确指受保护持有人操作已在场，但本条定义缺失；I必要材料未知不得记0。',True)
ordinary=copy.deepcopy(literal);ordinary[0]=ordinary[0].replace('改良型药品','普通药品');ordinary[1]=ordinary[1].replace('改良型药品','普通药品');ordinary[2]='本条款中药品仅实行普通资料保密，数据保护范围为一般行政数据，不以药物创新或临床优势为条件。'
add('v11_ordinary_data_holder',fixture(ordinary),{'I':0},'完整本条对象与保护内容为普通资料，创新/改良资格不成立。',True)
gap=copy.deepcopy(literal);gap[2]='本条款中药品的数据保护范围为一般新资料，不要求与已知药品相比具有临床优势。'
add('v11_improved_without_substantive_data_qualification',fixture(gap),{},'完整改良条内无所需临床优势新试验数据范围；仅断言本新增路径不得产正，不强制覆盖可能的旧路径。',True)
for name,mode in [('v11_wrong_article_same_sha','wrong_article'),('v11_nonconsecutive_original_positions','broken_order'),('v11_missing_next_article_boundary','missing_boundary'),('v11_cross_version_member','cross_version'),('v11_ambiguous_same_wording_articles','duplicate_current')]:
 add(name,fixture(mode=mode),{'I':None},'当前实质依赖关系明确，但唯一同版完整当前条款绑定未建立；不借兄弟/跨版/不连续材料，I专属必要材料保留。',True)
other=literal[-1].replace('该持有人受保护的数据','另一持有人受保护的数据')
add('v11_other_holder_data',fixture(current=other),{'I':0},'当前显式是另一持有人，不能承接本条原受保护对象。',True)
add('v11_independent_data_formality',fixture(current='申请人提交自行取得并未依赖他人受保护数据的资料时须签章。'),{'I':0},'自取资料的签章手续不展开原保护权利。',True)
add('v11_protection_purpose_only',fixture(current='为保护创新药试验数据，制定本办法。'),{'I':0},'制定宗旨没有当前实质待遇操作，不展开条文。',True)
add('v11_protection_document_receipt',fixture(current='申请人须在数据保护期内递交持有人签章文件，文件格式完整。'),{'I':0},'收件签章格式无当前依赖—许可限制关系。',True)
add('v11_confirmed_nonreliance_not_the_restriction',fixture(current='在数据保护期内，其他申请人已经取得持有人同意并未依赖其受保护数据，仅按普通手续提交申请。'),{'I':0},'同意/无依赖事实加普通手续不是当前保护数据许可限制操作；不得仅关键词给新增I。',True)
real=dict(name='v11_new01402_same_version_v16_separate',packet_binding=bind(packet),expected={'I':1},hard_assertion=True,semantic_reason='新材料独立开发控制：第六条完整四段原持有人资格、保护范围、许可限制及例外闭合；原v15控制不替换。',new_material_control=True)
save('new-role-controls-fixed-before-edit.json',dict(at_utc=now,real_cases=[real],cases=cases,independent_validation=False,old_225_controls_unchanged=True))
manual=R/'03-manual/full4481-common-release-20261010-root/manual.txt'
design=dict(at_utc=now,status='design_and_controls_fixed_before_classifier_edit',base=[bind(B/(n+'.py')) for n in NAMES],manual=bind(manual),material_seal=bind(M/'output-seal.json'),B_material_diagnostic_seal=bind(R/'08-audits/01402-v16-material-only-diagnostic-sol/output-seal.json'),role_scope='protected original innovative/improved holder; restricted generic/similar applicant is counterparty, never innovation object',manual_basis=[{'quote':'当前明确设立、实施、开放、适用、限制或终止同一制度安排时，可用共同材料中已经核明的该安排定义、适用对象和直接机制补全所指','section':'二有限补全'},{'quote':'I4同样要求创新/改良资格与当前实质权利义务相连','section':'六I4'},{'quote':'所需片段缺失登记补材，不记0','section':'二有限补全'}],positive_requirements=['strong full current protection-period unauthorized holder-data reliance→licensing restriction plus independent-data exception','unique full normalized current paragraph in exactly one supplied complete original article','same primary source/version; first article header matches group; consecutive original structured positions and HTML paragraphs; next article header boundary','first paragraph actual innovative/improved holder and protection entitlement','improved holder additionally requires immediately preceding same-article comparative clinical-advantage new-trial data scope with exclusions preserved','all role evidence and exception stored literally'],negative_requirements=['no cross-article holder borrowing','no generic/similar applicant innovation identity','no ordinary data privacy/IP existence alone','no title/purpose/form/receipt propagation'],missing_policy='Strong current reference plus unavailable or unproved complete own article yields isolated I-only necessary material request; complete ordinary object/content yields no new positive. Old I1 expected remains unchanged and actual null remains failure.',static_gate='Pure normalized current data-protection/protected-data wording; gate-out no new body execution. All gate-in old0/1/null selected, no labels/IDs/department/score.',unchanged_contract={'modules':['evidence','source_packet','source_receipts'],'complete_decisions':['S','E','Ec','F'],'old_relation_source_and_request_state':'byte/data-equivalent; only new typed relation/receipt permitted','gate_out':'all5 complete decisions and all relations/source/request state equal'},local_control_attempt_limit=2,model_calls=0,production_calls=0,expected_changes=0,control_binding=bind(A/'new-role-controls-fixed-before-edit.json'),actual_role_quotes=[dict(paragraph=i+1,text=t) for i,t in enumerate(literal)])
save('design-and-controls-before-edit.json',design)
save('pre-edit-seal.json',dict(at_utc=now,files=[bind(A/n) for n in ['prepare_before_edit.py','new-role-controls-fixed-before-edit.json','design-and-controls-before-edit.json']],self_excluded=True))
print(json.dumps(dict(new_real_N=1,new_synthetic_N=len(cases),classifier_executions=0,design_and_controls_frozen=True),ensure_ascii=False))
