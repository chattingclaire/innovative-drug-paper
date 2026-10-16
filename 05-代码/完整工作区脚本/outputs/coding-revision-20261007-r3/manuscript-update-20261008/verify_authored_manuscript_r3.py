"""Read-only verification of an actually authored adopted-results manuscript.

This does not author files, call models, or certify page appearance. It requires
the real authoring provenance and QA-approved numeric payload. Its report never
states render review or true human validation has occurred.
"""
from pathlib import Path
from fractions import Fraction
from zipfile import ZipFile
from collections import Counter
from lxml import etree as E
import argparse, hashlib, json, re, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'outputs/final-three-department-20261007/论文修订稿-三部门版.docx'
N = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
     'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
     'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
     'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
DIMS = ('S','E','Ec','I','F')
CITE = re.compile(r'\[(\d+(?:\s*[,，;；–—-]\s*\d+)*)\]|〔([A-Za-z][A-Za-z0-9_]*(?:\s*[;；,，]\s*[A-Za-z][A-Za-z0-9_]*)*)〕')
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p:json.loads(Path(p).read_text())
plain = lambda x:''.join(x.xpath('.//w:t/text()',namespaces=N)).replace('\u2060','')


def require(value, message):
    if not value: raise ValueError(message)


def numbers(s):
    values=[]
    for item in re.split('[,，;；]',s):
        ends = re.split('[–—-]',item.strip())
        values.extend(range(int(ends[0]),int(ends[-1])+1))
    return values


def converted(text, refs):
    def replace(m):
        vals = ([refs['old_number_to_new'][str(i)] for i in numbers(m[1])]
                if m[1] else [refs['source_key_to_new'][k.strip()] for k in re.split('[;；,，]',m[2])])
        return '['+','.join(map(str, sorted(set(vals))))+']'
    return CITE.sub(replace,text).replace('\u2060','')


def package(path):
    with ZipFile(path) as z:
        require(z.testzip() is None,'Damaged DOCX ZIP: '+str(path))
        parts={x.filename:z.read(x.filename) for x in z.infolist()}
    root=E.fromstring(parts['word/document.xml']);body=root.find('w:body',N)
    return parts,body,body.findall('w:p',N),body.findall('w:tbl',N)


def cells(table):
    return [[plain(c) for c in row.findall('w:tc',N)] for row in table.findall('w:tr',N)]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--folder',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path);args=ap.parse_args()
    require(not args.out.exists(),'Preserve previous verification reports')
    provenance=read(args.folder/'文稿生成与来源绑定.json')
    require(provenance['status']=='authored_requires_fresh_full_render_and_content_QA','Missing actual authoring provenance')
    require(provenance['render_QA_completed'] is False,'This verifier does not infer image review from authoring')
    for b in provenance['outputs']+provenance['authoring_sources']+[provenance['payload']]:
        require(sha(b['path'])==b['sha256'],'Authoring input/output changed: '+b['path'])
    payload=read(provenance['payload']['path'])
    require(payload['status']=='ready_for_authoring' and payload['remaining_fields']==[]
            and payload['remaining_gates']==[],'Authoring payload was not independently approved')
    for b in payload['input_bindings']:
        require(sha(b['path'])==b['sha256'],'Adopted input changed: '+b['path'])
    binding_index={str(Path(b['path']).resolve()):b['sha256'] for b in payload['input_bindings']}
    core={k:v for k,v in payload.items() if k not in {'status','input_bindings','limits',
          'payload_content_sha256','remaining_gates','independent_payload_QA_binding'}}
    core_sha=hashlib.sha256(json.dumps(core,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    require(core_sha==payload['payload_content_sha256'],'Payload content SHA differs')
    qa=read(payload['independent_payload_QA_binding']['path'])
    for b in (payload['independent_payload_QA_binding'],payload['root_adoption_binding'],qa['script']):
        require(sha(b['path'])==b['sha256'] and binding_index.get(str(Path(b['path']).resolve()))==b['sha256'],
                'Independent QA/adoption binding mismatch')
    require(qa['status']=='PASS' and qa['all_checks_pass'] is True
            and qa['independent_of_adapter_execution'] is True
            and qa['payload_content_sha256']==core_sha
            and qa['adoption_sha256']==payload['root_adoption_binding']['sha256']
            and qa['checked_counts']=={'fields':39,'replacements':52,'table2_points':80,
              'table2_primary_CIs':80,'table3_q':30,'department_directions':15},'Independent numeric QA does not match')
    preflight=Path(provenance['preflight']); refs=read(preflight/'引用重排与未用文献清单.json')
    require(Path(payload['bibliography_binding']['path']).resolve()==(preflight/'引用重排与未用文献清单.json').resolve()
            and payload['bibliography_binding']['sha256']==sha(preflight/'引用重排与未用文献清单.json'),
            'Final bibliography does not match independently verified payload')
    # Reuse only the author's read-only dependency/QA gate. All document,
    # citation, table, and figure checks below are independently reconstructed.
    author=HERE/'emit_manuscript_after_adoption.py'
    require(any(Path(b['path']).resolve()==author.resolve() and b['sha256']==sha(author)
                for b in provenance['authoring_sources']), 'Actual authoring script is not bound')
    gate=subprocess.run([sys.executable,str(author),'--payload',provenance['payload']['path'],
                         '--preflight',str(preflight),'--check-only'],capture_output=True,text=True)
    require(gate.returncode==0,'Actual author read-only adoption/dependency gate failed: '+gate.stdout+gate.stderr)
    current,body,ps,tables=package(args.folder/'论文修订稿-三部门实测结果版.docx')
    original,old_body,old_ps,old_tables=package(BASE)
    require(sha(BASE)==provenance['baseline_sha256'],'Original delivered manuscript changed')
    require(set(current)==set(original),'OOXML package part inventory changed')
    changed={n for n in current if current[n]!=original[n]}
    require(changed==set(provenance['changed_package_parts']),'Package change provenance differs')
    require(changed<={'word/document.xml','docProps/app.xml','word/media/image4.png'},'Unexpected package mutation')
    require(len(tables)==4 and len(ps)==111+len(refs['used_bibliography']),'Final paragraph/table count differs')
    require(E.tostring(body.find('w:sectPr',N))==E.tostring(old_body.find('w:sectPr',N)), 'Page/section settings changed')
    replacements={x['zero_based_body_p_index']:x for x in payload['resolved_replacements']}
    require(len(replacements)==52,'Expected52 replacement paragraphs')
    for i in range(110):
        expected=replacements[i]['replacement_text'] if i in replacements else plain(old_ps[i])
        require(plain(ps[i])==converted(expected,refs),'Final paragraph differs at '+str(i))
    require(plain(ps[110])=='参考文献','Reference heading moved')
    for i,item in enumerate(refs['used_bibliography'],111):
        require(plain(ps[i])==f"[{item['new_number']}] {item['entry']}", 'Bibliography entry differs')
    require(cells(tables[1])==payload['tables']['2']['rows'],'Table2 differs from independently verified80 points')
    require(cells(tables[2])==payload['tables']['3']['rows'],'Table3 differs from independently verified30 shares')
    t2,t3=cells(tables[1]),cells(tables[2])
    require(len(t2)==11 and len(t3)==7,'Table row counts differ')
    point_n=sum(len(cell.split('/')) for row in t2[1:] for cell in row[2:])
    require(point_n==80 and all(len(cell.split('/'))==2 for row in t2[1:] for cell in row[2:]),
            'Table2 A/C point count differs')
    ci_n=0; seen=set()
    adoption=read(payload['root_adoption_binding']['path'])
    classifications={role:read(adoption['methods'][role]['classification']['path']) for role in ('rules','LLM')}
    dim_names=dict(zip(DIMS,('安全性','有效性','经济性','创新性','公平性')))
    for ti,row in enumerate(payload['tables']['2']['audit'],1):
        dim,role=row['dimension'],row['method_role']; key=(dim,role)
        require(key not in seen,'Duplicate Table2 audit row'); seen.add(key)
        method=adoption['methods'][role]
        require(row['method_id']==method['method_id'] and row['classification_binding']==method['classification'],
                'Table2 audit binds another method/classification')
        require(t2[ti][:2]==[dim_names[dim],'规则' if role=='rules' else 'LLM'],'Table2 dimension/method row mapping differs')
        require(set(row['references'])=={'A','C'},'Table2 audit reference scope differs')
        expected_cells={metric:[] for metric in ('kappa','precision','recall','f1')}
        for reference in ('A','C'):
            entry=row['references'][reference]
            selector={'component':'probability_canonical','group':'ALL','weighting':'eligible_design_weighted',
                      'method':method['statistics_method_key'],'reference':reference,'dimension':dim}
            pointer=re.fullmatch(r'/comparisons/(\d+)',entry['row_json_pointer'])
            require(pointer is not None and entry['selector']==selector,'Table2 audit selector/pointer differs')
            source=classifications[role]['comparisons'][int(pointer[1])]
            require(all(source[k]==v for k,v in selector.items()),'Table2 source statistical record differs')
            for metric in expected_cells:
                ci=entry['metrics'][metric]['ci95_primary']
                require(ci['defined_repetitions']+ci['undefined_repetitions']==5000,'Incomplete primary CI')
                require(ci==source['metrics'][metric]['ci95_primary']
                        and entry['metrics'][metric]['estimate']==source['metrics'][metric]['estimate']
                        and entry['metrics'][metric]['json_pointer']==entry['row_json_pointer']+'/metrics/'+metric,
                        'Table2 CI/point is not from its actual source record')
                value=source['metrics'][metric]['estimate']
                expected_cells[metric].append('NA' if value is None else f'{value:.3f}')
                ci_n+=1
        require(t2[ti][2:]==['/'.join(v) for v in expected_cells.values()], 'Final Table2 point formatting differs from source')
    require(seen=={(d,r) for d in DIMS for r in ('rules','LLM')},'Table2 ten-row coverage differs')
    require(ci_n==80,'Table2 primary CI count differs')
    q_n=sum(len(row[2:]) for row in t3[1:]); require(q_n==30,'Table3 share count differs')
    for index in (0,3):
        require(E.tostring(tables[index])==E.tostring(old_tables[index]),'Preserved table changed: '+str(index+1))
    font_checks=0
    for table in (tables[1],tables[2]):
        expected_cols=6 if table is tables[1] else 7
        require(len(table.find('w:tblGrid',N))==expected_cols,'Table grid/cell columns differ')
        for row in table.findall('w:tr',N):
            require(len(row.findall('w:tc',N))==expected_cols,'Table row columns differ')
        for run in table.xpath('.//w:r',namespaces=N):
            size=run.find('w:rPr/w:sz',N)
            require(size is not None and size.get('{'+N['w']+'}val')=='21','Table font is not10.5pt')
            font_checks+=1
    figures=body.xpath('.//w:drawing',namespaces=N)
    require(len(figures)==2,'Expected two active manuscript figures')
    require(current['word/media/image3.png']==original['word/media/image3.png'],'Figure1 changed')
    require(current['word/media/image4.png']==(args.folder/'图2-三部门五维注意力占比.png').read_bytes(),'Figure2 embedded bytes differ')
    require(provenance['figure2_data']==payload['figure2_data'],'Figure2 numerical provenance differs')
    rel=E.fromstring(current['word/_rels/document.xml.rels'])
    rels={x.get('Id'):x.get('Target') for x in rel}
    for i,rid,target in ((33,'rId3','media/image3.png'),(64,'rId4','media/image4.png')):
        require(ps[i].xpath('.//a:blip/@r:embed',namespaces=N)==[rid] and rels[rid]==target,
                'Figure position/relationship differs at paragraph'+str(i))
    for row in payload['figure2_data']:
        require(sum(Fraction(row['dimensions'][d]['exact_fraction']) for d in DIMS)==1,'Figure2 exact shares do not sum100%')
    observed=[]; superscript_checks=0; citation_token_n=0
    for block in body:
        if block.tag=='{'+N['w']+'}p' and plain(block)=='参考文献': break
        paras=[block] if block.tag=='{'+N['w']+'}p' else block.xpath('.//w:p',namespaces=N)
        for p in paras:
            run_spans=[];start=0
            for run in p.xpath('.//w:r',namespaces=N):
                value=plain(run);run_spans.append((start,start+len(value),run));start+=len(value)
            require(start==len(plain(p)),'Cannot map citation characters to runs')
            for token in re.finditer(r'\[(\d+(?:[,–—-]\d+)*)\]',plain(p)):
                citation_token_n+=1
                for number in numbers(token[1]):
                    if number not in observed:observed.append(number)
                carriers=[run for start,end,run in run_spans if start<token.end() and end>token.start()]
                require(carriers,'Citation has no text runs')
                for run in carriers:
                    vertical=run.find('w:rPr/w:vertAlign',N)
                    require(vertical is not None and vertical.get('{'+N['w']+'}val')=='superscript','Citation is not superscript')
                superscript_checks+=1
    require(observed==list(range(1,len(refs['used_bibliography'])+1)),'First-appearance citation ordering differs')
    require(superscript_checks==citation_token_n,'Not all citation spans checked')
    full='\n'.join(plain(p) for p in body.xpath('.//w:p',namespaces=N))
    require(not re.search(r'\{\{|\}\}|〔[A-Za-z]',full),'Unresolved field/source key remains')
    for term in ('综合政策','阳性维度','旧LLM','v28.2','内部排版预览','H427的A/C'):
        require(term not in full,'Obsolete or inconsistent term: '+term)
    require('三者均为AI评审流' in full and '独立真人验证尚待实施' in full,'Reference identity/exposure was not preserved')
    memo_parts,memo_body,memo_ps,memo_tables=package(args.folder/'校核与待确认事项.docx')
    memo=plain(memo_body)
    require('真实人工提交目前为0' in memo and '现有A/C/T均为AI代理' in memo,'Memo identity is false or missing')
    for key in ('FINAL_RULES_ID','FINAL_LLM_ID','FINAL_CONCLUSION_ATTENTION_SUMMARY','FINAL_ERROR_PATTERN_SUMMARY'):
        require(payload['resolved_fields39'][key] in memo,'Memo differs from adopted fields: '+key)
    # Text counts are explicitly separate from later LibreOffice measurements.
    before_blocks=list(body)[:list(body).index(ps[110])]
    before_refs='\n'.join(plain(p) for block in before_blocks
                          for p in ([block] if block.tag=='{'+N['w']+'}p' else block.xpath('.//w:p',namespaces=N)))
    count=lambda t:{'han_characters':len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]',t)),
                    'latin_word_tokens':len(re.findall(r'[A-Za-z]+(?:[-\u2019\'][A-Za-z]+)*',t)),
                    'non_whitespace_characters':len(re.sub(r'\s','',t))}
    report={'status':'PASS_MACHINE_DOCUMENT_CONTENT_ONLY','all_machine_checks_pass':True,
      'script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
      'authoring_provenance_sha256':sha(args.folder/'文稿生成与来源绑定.json'),
      'payload_content_sha256':core_sha,'replacement_paragraphs_checked':52,
      'table2_points_checked':point_n,'table2_primary_CIs_correspondence_checked':ci_n,
      'table3_shares_checked':q_n,'reference_n':len(refs['used_bibliography']),
      'table_font_runs_checked':font_checks,'superscript_citations_checked':superscript_checks,
      'active_figure_n':2,'exact_share_rows_checked':6,'all_before_reference_paragraphs_checked':110,
      'text_count_scope':'OOXML paragraphs and table-cell paragraphs separated by newlines; before_references includes title, both-language abstracts, body, captions, tables and appendix. Not Microsoft Word or LibreOffice word count.',
      'counts':{'full':count(full),'before_references':count(before_refs),'Chinese_abstract':count(plain(ps[1]))},
      'source_identity_retained':True,'visual_all_pages_review_completed':False,
      'actual_human_validation_completed':False,
      'limits':'A numerical/content PASS does not prove source truth, metric threshold compliance, visual rendering, human validation, or journal acceptance.'}
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','reference_n','table2_points_checked','table3_shares_checked','active_figure_n')},ensure_ascii=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
