#!/usr/bin/env python3
"""Serialize source paragraphs and geometry inspected for two renewal references."""
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
SOURCE_SHA='d76f3d33e1ea70990992a99ae76371fcc1f99da93078e72b4376265679167a73'
SOURCE=OUT.parents[1]/'00-baseline/source-files/d76f3d33e1ea7099-3.pdf'
BINDING=json.loads((OUT/'input-binding.json').read_text())
RECORDS=[json.loads(x) for x in (OUT/'selected-source-records.jsonl').read_text().splitlines()]
STAMP=datetime.now(timezone.utc).isoformat()

def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub(r'\s+','',s)
def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

if (OUT/'SEALED.json').exists():raise SystemExit('Sealed source supplement: do not overwrite.')
assert sha(SOURCE.read_bytes())==SOURCE_SHA
assert len(RECORDS)==2 and sum(len(r['contexts']) for r in RECORDS)==30

# Positions are extracted from the same bytes, and the line membership was
# visually checked on all nine pages. Only page-number footer lines are omitted.
root=ET.parse(OUT/'source-bbox.html').getroot()
chars=[];positions=[];page_rows=[]
for pno,page in enumerate([x for x in root.iter() if x.tag.endswith('}page')],1):
    start=len(chars);lines=[]
    for line in (x for x in page.iter() if x.tag.endswith('}line')):
        words=[x for x in line if x.tag.endswith('}word')]
        t=''.join(x.text or '' for x in words)
        if t==str(pno) and float(line.attrib['yMin'])>760:continue
        lines.append({'text':t,'bbox_pdf_points':{k:float(v) for k,v in line.attrib.items() if k in ['xMin','yMin','xMax','yMax']}})
        for word in words:
            bbox={k:float(v) for k,v in word.attrib.items() if k in ['xMin','yMin','xMax','yMax']}
            for c in norm(word.text or ''):
                chars.append(c);positions.append({'physical_page':pno,'bbox_pdf_points':bbox})
    page_rows.append({'physical_page':pno,'printed_page':pno,'start_char':start,'end_char_exclusive':len(chars),'lines':lines})
TEXT=''.join(chars)
assert len(page_rows)==9

units=[]
def bounded(uid,start,end,path,kind='source_paragraph',search_from=0):
    a=TEXT.index(norm(start),search_from)
    b=TEXT.index(norm(end),a+len(norm(start))) if end else len(TEXT)
    quote=TEXT[a:b]
    pages=sorted({x['physical_page'] for x in positions[a:b]})
    regions=[]
    for p in pages:
        bb=[x['bbox_pdf_points'] for x in positions[a:b] if x['physical_page']==p]
        bounds=[min(x['xMin'] for x in bb),min(x['yMin'] for x in bb),max(x['xMax'] for x in bb),max(x['yMax'] for x in bb)]
        regions.append({'physical_page':p,'printed_page':p,'bbox_pdf_points_xyxy':bounds,
                        'bbox_220dpi_px_xyxy':[round(x*220/72,2) for x in bounds],
                        'page_asset':f'pages/d76f3d33e1ea7099-physical-{p:03d}.png'})
    u={'resource_id':uid,'kind':kind,'heading_path':path,'source_sha256':SOURCE_SHA,'source_path':str(SOURCE),
       'text':quote,'text_sha256':sha(quote.encode()),'quote_policy':'原页连续段/有界句抄录；去除排版换行和字间空白，保留原文字符、句读、编号与括注。PDF内部字形编码以源图为准。',
       'source_char_interval_footerless_whitespace_normalized':[a,b],
       'source_ref':{'sha256':SOURCE_SHA,'locator':{'physical_pages':pages,'printed_pages':pages,'heading_path':path,'regions':regions}},
       'origin_classification':'existing_same_sha_source_snapshot_not_projected_as_full_reference_in_selected_input',
       'dimension_decision':None}
    units.append(u)
    return u

DOC='谈判药品续约规则'
R1='规则一纳入常规目录管理';R2='规则二简易续约';R3='规则三重新谈判'
u_intro=bounded('RENEW25-DOC-PREFACE','按照《基本医疗保险用药管理暂行办法》',R1,[DOC])
full1=bounded('RENEW25-RULE1-FULL',R1,R2,[DOC,R1],'bounded_complete_rule')
full2=bounded('RENEW25-RULE2-FULL',R2,R3,[DOC,R2],'bounded_complete_rule')
s1=TEXT.index(R1);s2=TEXT.index(R2);s3=TEXT.index(R3)

def section_cuts(prefix,path,cuts,search_from):
    result=[]
    for n,(name,start) in enumerate(cuts[:-1]):
        end=cuts[n+1][1]
        result.append(bounded(prefix+'-'+name,start,end,path,search_from=search_from))
    return result

r1_conditions=section_cuts('RENEW25-R1',[DOC,R1,'一、条件'],[
    ('PREDICATE','满足以下条件之一的协议期内谈判药品'),
    ('C1','1.非独家药品'),
    ('C2','2.截至目录调整当年12月31日'),
    ('END','二、规则')],s1)
r1_rules=bounded('RENEW25-R1-RULES','二、规则','三、程序',[DOC,R1,'二、规则'],search_from=s1)
r1_payment_gate=bounded('RENEW25-R1-8YEAR-INDEPENDENT-PAYMENT-GATE','（4）满足上述条件2的独家药品','3.国家医保药品支付标准制定规则',[DOC,R1,'二、规则','2.支付标准的确定','（4）'],search_from=s1)
r1_procedure=bounded('RENEW25-R1-PROCEDURE','三、程序',R2,[DOC,R1,'三、程序'],search_from=s1)

r2_conditions=section_cuts('RENEW25-R2',[DOC,R2,'一、条件'],[
    ('PREDICATE','协议将于目录调整当年12月31日到期'),
    ('C1','1.独家药品。'),
    ('C2','2.本协议期实际发生的纳入支付范围的药品费用'),
    ('C3-PARENT','3.未来两年的纳入支付范围的药品费用预算增幅合理。'),
    ('C3-1','（1）不调整支付范围的药品：'),
    ('C3-2','（2）调整支付范围的药品：'),
    ('C4','4.市场环境未发生重大变化。'),
    ('C5','5.不符合纳入常规目录管理的条件。'),
    ('END','二、规则')],s2)
r2_payment=bounded('RENEW25-R2-PAYMENT-RULES','二、规则','三、程序',[DOC,R2,'二、规则'],search_from=s2)
r2_a=bounded('RENEW25-R2-RATIO-A-DEFINITION','以本协议期实际发生的纳入支付范围的药品费用与纳入支付范围的药品费用预算的比值','1.截至目录调整当年12月31日',[DOC,R2,'二、规则','（一）不调整支付范围的药品'],search_from=s2)
r2_b=bounded('RENEW25-R2-RATIO-B-DEFINITION','分两步。第一步先计算原支付范围的下调比例','1.截至目录调整当年12月31日',[DOC,R2,'二、规则','（二）调整支付范围的药品'],search_from=TEXT.index('（二）调整支付范围的药品。',s2))
r2_procedure=bounded('RENEW25-R2-PROCEDURE','三、程序','四、其他',[DOC,R2,'三、程序'],search_from=s2)
r2_other=section_cuts('RENEW25-R2-OTHER',[DOC,R2,'四、其他'],[
    ('1','1.按照现行药品注册管理办法及注册分类标准批准的1类化学药品'),
    ('2-PREDICATE','2.目录调整当年协议未到期的谈判药品'),
    ('2-C1','（1）独家药品。'),
    ('2-C2','（2）目录调整当年实际发生的纳入支付范围的药品费用'),
    ('2-C3','（3）未来一年因调整支付范围所致的纳入医保支付范围的药品费用预算增幅'),
    ('3','3.对申请调整支付范围的药品'),
    ('4','4.目录调整当年协议到期且前一年按简易程序增加了适应症的品种'),
    ('5','5.实际发生的纳入支付范围的药品费用由医保部门统计。'),
    ('6','6.企业和医保方对实际发生的纳入支付范围的药品费用存在较大分歧的'),
    ('END',R3)],s2)

r3_anchors=section_cuts('RENEW25-R3-ANCHOR',[DOC,R3,'一、条件'],[
    ('PREDICATE','满足以下条件之一的协议期内独家药品纳入重新谈判范围'),
    ('C1','1.不符合纳入常规目录管理及简易续约条件的药品。'),
    ('C2','2.按照现行药品注册管理办法及注册分类标准批准的1类化学药品'),
    ('END','二、规则')],s3)
ap1=bounded('RENEW25-APPENDIX-1','一、本规则适用于所有协议期内谈判药品。','二、药品连续纳入',[DOC,'附则','一'],search_from=TEXT.index('附则'))
ap2=bounded('RENEW25-APPENDIX-2','二、药品连续纳入','三、数据来源：',[DOC,'附则','二'],search_from=TEXT.index('附则'))
ap3=bounded('RENEW25-APPENDIX-3','三、数据来源：','四、国家医保局负责对本规则进行解释。',[DOC,'附则','三'],search_from=TEXT.index('附则'))
ap4=bounded('RENEW25-APPENDIX-4','四、国家医保局负责对本规则进行解释。',None,[DOC,'附则','四'],search_from=TEXT.index('附则'))

assets=[]
for page in range(1,10):
    p=OUT/'pages'/f'd76f3d33e1ea7099-physical-{page:03d}.png';b=p.read_bytes();w,h=struct.unpack('>II',b[16:24])
    assets.append({'asset_path':str(p.relative_to(OUT)),'sha256':sha(b),'bytes':len(b),'width_px':w,'height_px':h,
                   'source_sha256':SOURCE_SHA,'physical_page':page,'printed_page':page,'render_dpi':220,'renderer':'pdftoppm',
                   'view_tool':'tools.view_image','view_detail':'original','actually_viewed':True})

source_meta={'title':DOC,'source_sha256':SOURCE_SHA,'snapshot_path':str(SOURCE),'bytes':SOURCE.stat().st_size,'page_N':9,
             'annual_version_label':'2025','same_version_as_input_source_ref_verified_by_exact_sha':True,
             'version_evidence':['全部30个CTX source_ref SHA与快照字节SHA相同。','来源清单原路径为医保2025公告附件/3.pdf。','PDF CreationDate/ModDate为2025-07-09 09:15:29 CST；这是文件元数据，不是官方公布日期。','附则二原文以2025年目录调整（截至2025年12月31日）为例。'],
             'official_url':None,'official_publication_date':None,
             'official_url_and_publication_date_status':'not_in_source_files_manifest_and_not_network_retrieved_this_task',
             'acquisition_status':'existing_frozen_snapshot_restored_no_new_external_source',
             'origin_classification':'原source_ref已指向的完整同SHA快照；完整规则正文未投影至这两条输入CTX。本次补恢复，不是新增确指外源。'}

record_bindings=[]
for r in RECORDS:
    body_sha=sha(r['text'].encode())
    projected=[c for c in r['contexts'] if 'text' in c]
    full_condition_present=any(norm(c['text'])==r2_conditions[0]['text'] or norm(c['text'])==r1_conditions[0]['text'] for c in projected)
    assert not full_condition_present
    record_bindings.append({'record_id':r['id'],'existing_body':r['text'],'existing_body_text_sha256':body_sha,'existing_pages':r['pages'],
                            'all_contexts_inspected_N':len(r['contexts']),'text_contexts_N':len(projected),'structure_only_contexts_N':len(r['contexts'])-len(projected),
                            'existing_context_bindings':[{'context_id':c['context_id'],'kind':c['kind'],'text_sha256':sha(c['text'].encode()) if 'text' in c else None,
                                                         'source_ref':c['source_ref'],'structure':c.get('structure')} for c in r['contexts']],
                            'existing_complete_rule1_or_rule2_conditions_projected':False,
                            'same_common_supplement_resource_ids':[u['resource_id'] for u in units],
                            'anchor_resource_ids':[u['resource_id'] for u in r3_anchors],
                            'later_round_required_for_any_rejudgment':True})

supplement={'schema':'source-only-renewal-reference-supplement/v1','created_at_utc':STAMP,
            'identity':{'type':'AI','agent':'pilot01_a_sol','model':'GPT-6.1 Sol','reasoning_setting':'ultra','activity':'source restoration and visual verification'},
            'input_binding':BINDING,'source':source_meta,'target_record_bindings':record_bindings,'resources':units,
            'source_geometry':{
                'layout_type':'single_column_prose_and_numbered_lists','actual_viewed_physical_pages':list(range(1,10)),
                'table_cells_or_merges':[],'diagram_arrows':[],
                'rule1_condition_group':{'parent_resource_id':r1_conditions[0]['resource_id'],'operator_printed':'之一','operator':'any',
                                         'shared_scope':'协议期内谈判药品','numbered_members':[r1_conditions[1]['resource_id'],r1_conditions[2]['resource_id']]},
                'rule2_due_condition_group':{'parent_resource_id':r2_conditions[0]['resource_id'],'operator_printed':'并同时满足以下条件','operator':'all',
                                             'shared_scope':'协议将于目录调整当年12月31日到期','renewal_period_text':'续约有效期2年',
                                             'numbered_members':[x['resource_id'] for x in r2_conditions if x['resource_id'].endswith(('C1','C2','C3-PARENT','C4','C5'))],
                                             'member3_submembers':[x['resource_id'] for x in r2_conditions if x['resource_id'].endswith(('C3-1','C3-2'))],
                                             'geometry_note':'第3项总谓词和（1）开头在物理2页，子项（1）接物理3页；子项（2）、第4/5项也在3页。两个括号子项同属第3项，不能另编号成第6/7项。'},
                'rule2_not_due_adjustment_group':{'parent_resource_id':'RENEW25-R2-OTHER-2-PREDICATE','operator_printed':'同时符合以下条件','operator':'all',
                                                 'shared_scope':'目录调整当年协议未到期的谈判药品，如需调整支付范围',
                                                 'numbered_members':['RENEW25-R2-OTHER-2-C1','RENEW25-R2-OTHER-2-C2','RENEW25-R2-OTHER-2-C3'],
                                                 'geometry_note':'该组属于规则二“四、其他”第2条，（3）跨物理6–7页。没有把规则二“一、条件”五项全文移接为这组原文条件。'},
                'cross_page_joins':[{'resource_id':'RENEW25-R2-C3-1','pages':[2,3]},
                                    {'resource_id':'RENEW25-R2-OTHER-2-C3','pages':[6,7]},
                                    {'resource_id':'RENEW25-R2-PROCEDURE','pages':[5,6]},
                                    {'rule3_heading_page':7,'rule3_common_predicate_page':8,'note':'标题/一、条件在7页，共同谓词及成员在8页。'}],
                'rule2_other_shared_definitions':['RENEW25-R2-OTHER-5','RENEW25-R2-OTHER-6','RENEW25-APPENDIX-2','RENEW25-APPENDIX-3'],
                'global_scope_resources':['RENEW25-DOC-PREFACE','RENEW25-APPENDIX-1']},
            'asset_manifest':'source-page-assets-manifest.json',
            'complete_rule_text_status':{'rule1':'complete_same_snapshot_bounded_between_rule1_and_rule2_headings',
                                         'rule2':'complete_same_snapshot_bounded_between_rule2_and_rule3_headings'},
            'common_material_policy':'两个目标及两方/机器各方法后续使用同一补材资源版本和SHA；现有首判、body、CTX、任何标签均不覆盖。',
            'not_included':['No S/E/Ec/I/F advice or values.','No predictions, reference labels or human answers read.','No other year used as substitute.'],
            'unresolved_source_material_requests':[],
            'metadata_limits':['官方URL和公布日期在本次允许来源清单未提供，未外搜；文件创建时间不冒称公布时间。该限制不妨碍以同source_ref SHA核同版本完整规则正文。']}
dump('source-only-supplement.json',supplement)
dump('source-page-assets-manifest.json',{'schema':'source-page-assets/v1','source':source_meta,'assets':assets})
dump('source-page-lines-and-geometry.json',{'schema':'source-pdf-line-geometry/v1','source_sha256':SOURCE_SHA,'pages':page_rows,
                                        'note':'页码脚注被单独省去；原PDF字节未改；段/句定位使用同字节bbox提取并经原页视觉核验。'})

review={'schema':'renewal-reference-source-review/v1','completed_at_utc':STAMP,'identity':supplement['identity'],
        'input_binding':BINDING,'source':source_meta,'record_N':2,'contexts_inspected_N':30,'resources_N':len(units),'actual_viewed_page_N':9,
        'findings':[
            '同版完整PDF已在固定快照中；本次属于原来源已有未投影材料的恢复，新增外源0份。',
            '两条输入的全部CTX均指向同SHA；当前CTX包含规则三标题/共同谓词/两项成员及总序，但未投影规则一和规则二完整条件组。',
            '规则一“一、条件”是同一共同谓词下的2项之一；规则二“一、条件”是到期前提下的5项同时条件，第三项含2个对应支付范围子项。',
            '规则二“四、其他”第2条另有未到期调整支付范围的共同谓词及3项同时条件；第3项跨6–7页。',
            '规则一完整正文物理1–2页；规则二完整正文物理2–7页。全文、细分条件、完整四其他及共享附则均保留原文和各自SHA/区域。',
            '市场重大变化释义、药品费用/预算定义、8年年份计算及数据来源同时补入共享源资源，不按编码维度分别编造材料。'],
        'acquisition':'No download or new official-source acquisition was needed; exact already-snapshotted bytes were restored.',
        'unresolved_condition_or_full_text_requests_N':0,'unverified_origin_metadata_fields':['official_url','official_publication_date'],
        'later_execution_status':'Material preparation only; current judgments remain sealed. Shared supplement integration and later-round execution belong to parent task.',
        'no_coding_or_human_validation':True}
dump('source-review.json',review)

logs=[
    {'sequence':1,'action':'read_fixed_input_only_selected_two_records_and_all_CTX','input_sha256':BINDING['input_sha256'],'record_ids':BINDING['selected_record_ids'],'contexts_N':30},
    {'sequence':2,'action':'resolve_source_ref_SHA_through_baseline_manifest','manifest_sha256':BINDING['manifest_sha256'],'source_sha256':SOURCE_SHA,'snapshot':str(SOURCE)},
    {'sequence':3,'action':'verify_snapshot_bytes_and_source_metadata','actual_sha256':SOURCE_SHA,'bytes':SOURCE.stat().st_size,'page_N':9,
     'creation_and_modification_date':'2025-07-09 09:15:29 CST','publication_date_inferred':False},
    {'sequence':4,'action':'render_and_actually_view_original_pages','physical_pages':list(range(1,10)),'printed_pages':list(range(1,10)),'dpi':220,'view_tool':'tools.view_image',
     'reason':'1–3 complete rule1 and rule2 conditions; 4–5 complete rule2 operative rules/procedure boundary; 6–7 other scope/conditions/shared definitions; 8 current anchors; 9 scope/year/data-source appendix.'},
    {'sequence':5,'action':'serialize_verified_source_paragraphs_and_geometry','resource_N':len(units),'cross_page_joins_verified':True},
    {'sequence':6,'action':'acquisition_summary','new_external_source_N':0,'network_used':False,'official_url':None,'official_publication_date':None,
     'status':'same_source_existing_snapshot_missing_projection_restored','unresolved_rule_condition_requests_N':0},
]
(OUT/'acquisition-log.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in logs))

md=['# 续约规则确指来源补材（AI）','',
    '已核 RECODE25-00900、RECODE25-00902 的当前文字和全部30个CTX。两条都指向同一份已有快照，完整规则一/规则二可直接恢复；本次没有新增外源、下载不同年文件或生成五维判断。','',
    f'原PDF SHA：`{SOURCE_SHA}`；源输入 SHA：`{BINDING["input_sha256"]}`。','',
    '原件为9页《谈判药品续约规则》，已逐页实际查看。规则一正文位于物理/印刷1–2页；规则二正文位于2–7页；当前规则三条件锚点位于7–8页；附则位于9页。','',
    '版本由与当前source_ref完全相同的字节SHA锁定。归档路径为医保2025公告附件，PDF创建/修改元数据为2025年7月9日，附则使用2025年目录调整例。来源清单没有官方URL或公布日期，未外搜；没有把创建日期冒称公布日期。','',
    '## 原文条件与结构','',
    '- 规则一：协议期内谈判药品，满足2项条件之一；8年条件的独家药品另有先确定支付标准后纳入的原文前提。',
    '- 规则二到期适用：协议将于调整当年12月31日到期，并同时满足5项条件；第三项内的（1）（2）按是否调整支付范围对应。市场重大变化释义保留在第4项，常规目录条件的确指保留在第5项。',
    '- 规则二未到期适用：四、其他第2条另列共同谓词及（1）（2）（3）三个条件，不能把两个原文条件组混成同一个列表。',
    '- 共享定义：比值A/B、费用统计、年份计算、预算和数据来源按原文单独定位；没有按某个编码维度挑改措辞。','',
    '## 补材来源性质','',
    '这是原source_ref对应完整来源中已有、但未投影到这两条固定输入CTX的正文。输入内现有规则三总谓词、成员、标题和根序均保留；后续主任务可追加同版公共资源，不覆盖当前首判。','',
    f'共{len(units)}个有界原文资源，逐资源记录文字SHA、原页、PDF坐标区域及原图资产。source-only-supplement.json含规则一/二完整有界正文与细分段落；源字符只规范化排版空白，源几何仍可回查。','',
    '## 原文摘录（核心完整条件）','']
for group in [r1_conditions,r2_conditions,[x for x in r2_other if 'OTHER-2-' in x['resource_id']],r3_anchors,[ap1,ap2,ap3,ap4]]:
    for u in group:
        md += [f'**{u["resource_id"]}**（物理页 {u["source_ref"]["locator"]["physical_pages"]}）','',u['text'],'']
md += ['完整支付规则、程序和其他条款见JSON的 RULE1-FULL / RULE2-FULL 及各有界资源。这里只核来源，不提出 S/E/Ec/I/F 值或理由。','',
       '规则条件/正文版本没有未决材料请求；官方URL、确切公布日期仍未由本次材料证实。公共补材须同版提供给两方和机器，任何重判另轮执行。本交付是AI来源工作，不是真人编码或已完成验证。','']
(OUT/'source-review.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'status':'built','resources':len(units),'records':2,'contexts':30,'actual_pages':9,'new_external_sources':0},ensure_ascii=False))
