from pathlib import Path
import ast,hashlib,json,datetime,difflib
p=Path(__file__).resolve().parent;root=p.parents[3]
paths={'baseline':root/'06-coding/full4481-rule-production-adapter-sol','IF_v2':root/'06-coding/rule-v20-semantic-audit-repair-sol/versions/v2','IF_v3':root/'06-coding/rule-v20-semantic-audit-repair-sol/versions/v3','SE_v2':root/'06-coding/rule-v20-SEEconomic-repair-sol/versions/v2'}
names=['relations','dimensions','evidence','source_packet','source_receipts']
def bind(q):
 q=Path(q).resolve();x=q.read_bytes();return {'path':str(q),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
def write(n,x):
 with(p/n).open('x',encoding='utf-8')as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def inventory(q):
 raw=q.read_text();tree=ast.parse(raw);f={};const={};duplicates=[]
 def walk(nodes,prefix=''):
  for n in nodes:
   if isinstance(n,ast.ClassDef):walk(n.body,prefix+n.name+'.')
   elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    key=prefix+n.name;text=ast.get_source_segment(raw,n)
    if key in f:duplicates.append({'name':key,'overridden_line':f[key]['line'],'effective_line':n.lineno})
    f[key]={'line':n.lineno,'end_line':n.end_lineno,'sha256_utf8':hashlib.sha256(text.encode()).hexdigest(),'text':text,'calls':sorted({ast.unparse(x.func)for x in ast.walk(n)if isinstance(x,ast.Call)})}
   elif not prefix and isinstance(n,(ast.Assign,ast.AnnAssign)):
    targets=n.targets if isinstance(n,ast.Assign)else[n.target]
    for t in targets:
     if isinstance(t,ast.Name)and t.id.isupper():const[t.id]={'line':n.lineno,'text':ast.get_source_segment(raw,n),'sha256_utf8':hashlib.sha256(ast.get_source_segment(raw,n).encode()).hexdigest()}
 walk(tree.body);return {'functions':f,'constants':const,'duplicate_effective_definitions':duplicates}
inv={};bindings={}
for version,d in paths.items():
 inv[version]={};bindings[version]=[bind(d/(n+'.py'))for n in names]
 dest=p/'code-snapshot'/version;dest.mkdir(parents=True)
 for n in names:
  raw=(d/(n+'.py')).read_bytes();(dest/(n+'.py')).write_bytes(raw);inv[version][n]=inventory(d/(n+'.py'))
# Bind the actual sealed releases, not the earlier volatile SE observation.
seals={}
for version,files in {'IF_v3':['algorithm-bindings.json','candidate-seal.json','delivery-seal.json','delivery-integrity-readback.json'],'SE_v2':['algorithm-bindings.json','candidate-seal.json','delivery-seal.json']}.items():
 seals[version]=[bind(paths[version]/n)for n in files]
 expected=json.loads((paths[version]/'algorithm-bindings.json').read_bytes())['modules']
 for x in expected:
  key='path';assert bind(x[key])['sha256']==x['sha256']
write('sealed-release-bindings.json',{'identity':'nonhuman AI static interface preflight','modules':bindings,'sealed_releases':seals,'manual':bind(root/'03-manual/full4481-common-release-20261010-root/manual.txt'),'reads':'five modules, seals, shared patches and dependency metadata only; no corpus outcomes/LLM labels read','run_any_engine_or_cohort':False,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
rows=[];constants=[]
for n in names:
 versions={v:inv[v][n]['functions']for v in paths};base=versions['baseline']
 for f in sorted(set().union(*(set(z)for z in versions.values()))):
  row={'module':n,'function':f,'versions':{v:z.get(f)for v,z in versions.items()}}
  def changed(v):
   a,b=base.get(f),versions[v].get(f)
   return(a is None)!=(b is None)or bool(a and b and a['sha256_utf8']!=b['sha256_utf8'])
  row['IF_v2_changed']=changed('IF_v2');row['IF_v3_changed']=changed('IF_v3');row['SE_v2_changed']=changed('SE_v2');row['both_changed']=row['IF_v3_changed']and row['SE_v2_changed']
  if row['both_changed']:
   a,b=versions['IF_v3'].get(f),versions['SE_v2'].get(f)
   row['identical_final_function']=bool(a and b and a['sha256_utf8']==b['sha256_utf8'])
  if any(row[k]for k in ['IF_v2_changed','IF_v3_changed','SE_v2_changed']):rows.append(row)
 vals={v:inv[v][n]['constants']for v in paths};basec=vals['baseline']
 for c in sorted(set().union(*(set(z)for z in vals.values()))):
  versionsc={v:z.get(c)for v,z in vals.items()};a=basec.get(c)
  changedc={v:(a is None)!=(b is None)or bool(a and b and a['sha256_utf8']!=b['sha256_utf8'])for v,b in versionsc.items()if v!='baseline'}
  if any(changedc.values()):constants.append({'module':n,'constant':c,'versions':versionsc,'changed':changedc})
write('function-level-differences.json',{'rows':rows,'changed_functions_N':len(rows),'effective_definition_rule':'last definition in AST source order','overlap':[{'module':r['module'],'function':r['function'],'identical':r.get('identical_final_function')}for r in rows if r['both_changed']],'duplicate_effective_definitions':{v:{n:inv[v][n]['duplicate_effective_definitions']for n in names if inv[v][n]['duplicate_effective_definitions']}for v in paths}})
write('constant-level-differences.json',constants)
recommendations={
 'RelationView.__init__':'以IF v3为底保留全部原有/IF有界调用，追加SE专用调用；记录依赖解析时序。不可选一方整段覆盖。',
 'RelationView._add':'IF v3未修改旧text+SHA签名，必须采用SE v2精确context_id/start/end/text/SHA、subtype、consumers、only_IF、norm projection和shared_predicate身份；有限关系引用相同文字时不得吞另一消费者。',
 'dimensions._generic':'合并SE对S/E/Ec旧宽泛路径跳过及IF行政创新owner排除。保留I/F通用实际内容路径；否定仍指议题，不能当满足/兑现。',
 'dimensions.judge':'保留IF v3先affected_dimensions、再与only_IF交集并分别调用各维消费者的调度；SE提供各维专用判据，不能照抄SE judge先无条件generic/safety/economic的整段。',
 'dimensions._units':'加入SE closure_proof.boundary_quotes只作闭合证明、不形成标签内容，及SE_scope_verified保持完整证据；不对IF资格完整组错误清空actual_members。',
 'complete qualification and requests':'IF _standards新resolved receipt须原路径、当前reference、同源SHA、programme/family、确切完整组和leaf/seed等信息匹配。当前实现不自动删除任何其他请求；ROOT不得按同一text、同一标题或任一新关系成功批量清除旧请求。',
 'parent predicates':'IF首项preceding角色可role_only但唯一/同源/当前第一项/实质父句；已供原坐标冲突阻断并补材。SE同段/父句有限predicate应并存，禁止角色当无条件共享permission。',
 'programme/article closure':'保留IF稳健CJK内部空格节目边界和完整literal标准范围，及SE同条/末边界补足；边界引文属于闭合证明而非评价成员。',
 'manual/constants':'同SHA5ea7保持，合并各维注释引用即可；并集IF GAPS/priority-feedback与SE专用局部常量，既有manual boundary/Accumulator保留。',
 'unchanged modules':'evidence/source_packet/source_receipts三模块双方与基线字节相同，不产生三方内容冲突。'}
write('merge-interface-recommendations.json',{'status':'sealed versions precise static advice; no mutation or classification execution','recommendations':recommendations,'remaining_questions':['SE新有界完整内容能否精确解析对应旧请求须由共同合并的对照控制验证，不能由本静态检查声称解除。','I/F已供完整资格标准可供五维依法逐维判断；不得用IF命名规则误将全部cited_standard限制I/F。','同一具名安排当前服务对应阶段、对象、机会仍需独立范围复审，本预审不改变材料或手册门槛。'],'expected_or_ID_specific_merge_overlays':False})
lines=['五维合并接口封存补充：非真人静态审查，未执行分类或整批。','精确绑定：IF v3与SE v2均已封存；旧IF v2/SE挥发观察保留原报告。','双方同时修改函数：']
lines.extend(f"{r['module']}.{r['function']}；最终相同={r.get('identical_final_function')}"for r in rows if r['both_changed'])
lines.append('\n函数级建议：');lines.extend(k+'：'+v for k,v in recommendations.items());(p/'合并接口补充说明.txt').write_text('\n'.join(lines)+'\n')
# Frozen module bindings must remain identical after all reads.
assert all(bind(x['path'])==x for vs in bindings.values()for x in vs)
files=sorted(q for q in p.rglob('*')if q.is_file() and q.name not in ['output-seal.json','integrity-readback.json'])
write('output-seal.json',{'status':'sealed static supplement','members':[bind(q)for q in files],'member_N':len(files),'owner_code_changed':False,'classification_or_cohort_run':False})
seal=json.loads((p/'output-seal.json').read_bytes());assert all(bind(x['path'])==x for x in seal['members'])
write('integrity-readback.json',{'status':'all output members and frozen module inputs unchanged','member_N':len(files),'output_seal':bind(p/'output-seal.json'),'failed_N':0})
print(json.dumps({'modified_effective_functions_N':len(rows),'both_changed':[r['module']+'.'+r['function']for r in rows if r['both_changed']],'seal':bind(p/'output-seal.json')},ensure_ascii=False))
