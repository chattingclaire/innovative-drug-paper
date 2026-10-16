"""Error-type regression, AI development evidence, never independent truth."""
import datetime,hashlib,json,sys,types,copy
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
NAMES=('source_packet','source_receipts','evidence','relations','dimensions')
def bind(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def modules():
    out={}
    for name in NAMES:
        module=types.ModuleType(name);module.__file__=str(HERE/(name+'.py'));sys.modules[name]=module
        exec(compile((HERE/(name+'.py')).read_bytes(),module.__file__,'exec'),module.__dict__);out[name]=module
    return out
def run(outdir):
    dest=Path(outdir);dest.mkdir(exist_ok=False);coders=modules();results=[]
    (dest/'code-snapshot').mkdir()
    for name in NAMES:
        (dest/'code-snapshot'/(name+'.py')).write_bytes((HERE/(name+'.py')).read_bytes())
    (dest/'code-snapshot'/'regression_tests.py').write_bytes(Path(__file__).read_bytes())
    literal=[
      ('bare right with no innovative eligibility','药品申请人享受数据保护。','I',0),
      ('ordinary programme withdrawal no qualification','终止药品登记的日常工作。','I',0),
      ('I3 actual service','药审中心为创新药研发提供研究方案反馈。','I',1),
      ('I3 negated service still issue','药审中心不再为创新药研发提供研究方案反馈。','I',1),
      ('ordinary public reference','创新药研发可参考本技术指导原则。','I',0),
      ('administrative innovation modifier','科学开展药品监管，创新性、系统性地推进管理工作。','I',0),
      ('ordinary applicant obligation','创新药申请人应收集安全资料并提交风险管理文件。','I',0),
      ('meeting form identity only','创新药申请人沟通交流采用电话、视频或面对面形式。','I',0),
      ('general dosage form identity','口服液体制剂具有易于吞咽的特点。','I',0),
      ('unconnected redesign','优化药品包装设计。','I',0),
      ('concrete limitation change','应优化药液浓度和推注速度，避免注射时间过长引起不适。','I',1),
      ('explicit negated improvement still content','药品设计为口崩片，但没有改善吞咽困难。','I',1),
      ('new form fixes existing unsuitability','现有上市剂型均不适用于儿童，新剂型属于儿童人群适宜剂型。','I',1),
      ('different product resource','创新药为讨论对象，其他药品研发可以获得研究方案反馈。','I',0),
      ('unlisted only no treatment gap','境外已上市境内未上市的药品。','F',0),
      ('unlisted priority unresolved relation','境外已上市境内未上市的罕见病药品可申请优先审评。','F',None),
      ('actual target indication gap','境内尚无药物获批拟开发适应症的药品可申请优先审评。','F',1),
      ('real supply gap restriction','对临床急需的短缺药品不再接受优先审评申请。','F',1),
      ('rare disease identity','治疗罕见病的药品应提交有关材料。','F',0),
      ('need-linked application opportunity','不限定申报药品的治疗领域，满足各治疗领域用药需求。','F',1),
      ('unrelated other product priority','药品尚无有效治疗手段，其他药品可以申请优先审评。','F',0),
    ]
    for name,text,dim,expected in literal:
        unit={'text':text,'contexts':[],'source_ref':{'sha256':'a'*64,'source_resource_id':'SOURCE-'+'a'*64,'locator':{}}}
        evaluate(name,unit,dim,expected,coders,results)
    # Applicability is a role, not an inherited label. Identical words from a
    # different source or component cannot supply the current support object.
    for variant,expected in [('closed scope and actual service',1),('different source',0),('different component',0),('scope with only an applicant duty',0)]:
        text='申请人可在关键性临床试验前提出沟通交流申请，围绕临床试验方案开展沟通交流。'
        if variant=='scope with only an applicant duty':text='申请人应按格式提交临床试验资料。'
        primary='a'*64;context_sha='b'*64 if variant=='different source' else primary
        current_ref={'sha256':primary,'source_resource_id':'SOURCE-'+primary,'locator':{'component_id':'current'}}
        scope_ref={'sha256':context_sha,'source_resource_id':'SOURCE-'+context_sha,'locator':{'component_id':'other'if variant=='different component'else 'current'}}
        def ctx(cid,kind,text,ref,structure):return {'context_id':cid,'kind':kind,'text':text,'source_ref':ref,'structure':structure}
        contexts=[ctx('current','paragraph',text,current_ref,{'component_id':'current'}),
                  ctx('container','source_paragraph','',scope_ref,{'first_paragraph':'p1','last_paragraph':'p3'}),
                  ctx('scope','source_paragraph','(一)适用范围：儿童专用创新药。',scope_ref,{'sequence_index':0}),
                  ctx('stage','source_paragraph','按照本工作规范开展上市前临床试验沟通交流。',scope_ref,{'sequence_index':1}),
                  ctx('service','source_paragraph','沟通交流时限为30日。',scope_ref,{'sequence_index':2}),
                  ctx('boundary','following_heading','二、工作流程',scope_ref,{'scope_context_ids':['scope','stage','service'],'component_first_paragraph':'p1','component_last_paragraph':'p3','follows_context_id':'service'})]
        evaluate(variant,{'text':text,'contexts':contexts,'source_ref':current_ref},'I',expected,coders,results)
    # Exact original source cases are regression fixtures only; record identity
    # stays in the test loader and never enters the semantic unit/predicates.
    packet=HERE.parents[2]/'full4481-common-v15-production-preparation-sol'/'packets'
    actual=[('00186','I',0),('00349','I',0),('00044','I',1),('00044','F',1),
            ('00104','I',1),('01484','I',1),('01484','F',1),('04164','I',1),
            ('04568','I',1),('03478','I',1),('01414','I',1),('01746','I',1),
            ('04196','I',1),('00110','F',None),('00118','F',None),
            ('03455','I',0),('01395','I',0),('03445','I',0),('03453','I',0),('03462','I',0),
            ('01431','I',1),('01426','I',1),('02272','I',1),('03825','I',1),('02505','I',1),
            ('01401','I',1),('00090','I',1),('00185','I',1),('03460','I',1),('02237','I',1),('01384','I',1),('01388','I',1),('01741','I',1),('04190','I',1),('00126','I',1),('00126','F',None),('02826','I',1),('04618','I',None),('04618','F',None),('02247','I',None),('04595','F',1)]
    for record,dim,expected in actual:
        path=packet/f'RECODE25-{record}.json';bundle=json.loads(path.read_bytes())['source_bundle']
        unit=coders['source_packet'].semantic_unit(bundle)
        evaluate('source fixture '+record,unit,dim,expected,coders,results,binding=bind(path))
    # Mutation fixtures check relation guards using exact frozen source bytes.
    # They are synthetic development cases, not revised production records.
    for variant in ['not first member','different parent source','no operative colon','ordinary non-operative parent']:
        path=packet/'RECODE25-04595.json';bundle=json.loads(path.read_bytes())['source_bundle']
        unit=coders['source_packet'].semantic_unit(bundle)
        if variant=='not first member':
            unit['text']=unit['text'].replace('(一)','(二)',1)
            for c in unit['contexts']:
                if c['kind']=='paragraph':c['text']=c['text'].replace('(一)','(二)',1)
        for c in unit['contexts']:
            if c['kind']=='preceding_paragraph':
                if variant=='different parent source':c['source_ref']['sha256']='b'*64
                if variant=='no operative colon':c['text']=c['text'].rstrip(':')+'.'
                if variant=='ordinary non-operative parent':c['text']='以下内容为普通药品名称:'
        evaluate('first operative member guard '+variant,unit,'F',0,coders,results,binding=bind(path),synthetic_mutation=True)
    for variant in ['different parent unit','different parent source','missing innovation object','ordinary encouragement']:
        path=packet/'RECODE25-02826.json';bundle=json.loads(path.read_bytes())['source_bundle']
        unit=coders['source_packet'].semantic_unit(bundle)
        for c in unit['contexts']:
            if c['kind']=='parent_paragraph' and 'DRMP是' in c.get('text',''):
                if variant=='different parent unit':c['structure']['unit_id']='another-unit'
                if variant=='different parent source':c['source_ref']['sha256']='b'*64
                if variant=='missing innovation object':c['text']=c['text'].replace('创新药','普通药品')
        if variant=='ordinary encouragement':unit['text']='鼓励申请人与药审中心保持密切沟通。'
        evaluate('specific consultation guard '+variant,unit,'I',0,coders,results,binding=bind(path),synthetic_mutation=True)
    raw='第一节 突破性治疗药物程序\n创新药可以申请适用突破性治疗药物程序。\n第二节 附条 件批准程序\n其他药品可以申请附条件批准。\n第三节 优先审评审批程序\n临床急需短缺药品可以申请。\n'
    ref={'sha256':'a'*64,'source_resource_id':'SOURCE-'+'a'*64,'locator':{'unicode_code_point_interval_half_open':[0,len(raw)]}}
    leaf={'context_id':'literal','kind':'source_textleaf','text':raw,'source_ref':ref,'structure':{}}
    unit={'text':'创新药可以申请适用突破性治疗药物程序。','contexts':[leaf],'source_ref':ref}
    view=coders['relations'].RelationView(unit);closed=view._closed_primary_programme('突破性治疗药物程序')
    end=raw.index('第二节')
    results.append({'name':'internal CJK whitespace closes programme boundary','passed':bool(closed and closed['programme_span'][1]==end),
                    'actual_programme_span':closed and closed['programme_span'],'expected_end':end,'raw':raw,
                    'no_dimension_label_from_other_programme':True})
    summary={'identity':'nonhuman AI development regression','actual_cohort_77_or_800_run':False,
             'reference_independent':False,'manual_definition_changed':False,
             'test_N':len(results),'pass_N':sum(r['passed']for r in results),'failure_N':sum(not r['passed']for r in results),
             'code_bindings':[bind(HERE/(name+'.py'))for name in NAMES]+[bind(__file__)],
             'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (dest/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (dest/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items()if k!='code_bindings'},ensure_ascii=False))
    return summary['failure_N']
def evaluate(name,unit,dim,expected,coders,results,**meta):
    try:
        view=coders['relations'].RelationView(unit);decisions=coders['dimensions'].judge(view)
        coders['evidence'].validate_decisions(unit,decisions)
        value=decisions[dim]['value']
        results.append({'name':name,'dimension':dim,'expected_development_relation':expected,'actual':value,'passed':value==expected,
            'current_text':unit['text'],'decisions':decisions,'source_relation_traces':view.traces(),**meta})
    except Exception as error:
        results.append({'name':name,'dimension':dim,'expected_development_relation':expected,'passed':False,
                        'error_type':type(error).__name__,'message':str(error),**meta})
if __name__=='__main__':
    raise SystemExit(bool(run(sys.argv[1])))
