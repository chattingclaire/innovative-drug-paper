"""Actual final-DOCX length and explicit official-template checks.

Does not edit the final manuscript or workbook. Two scratch excerpt copies are
QA derivatives of the root's already-started document editing batch; this tool
never starts an additional authoring operation. No old QA is copied as results.
"""
from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from collections import Counter
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import tempfile
from lxml import etree as E
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[1]
SOFFICE=Path('/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/MacOS/soffice')
TEMPLATE=PROJECT/'outputs/manuscript-completion-20261006/期刊官网快照/现行格式附件69.docx'
GUIDANCE=TEMPLATE.parent/'contribution-invited-正文.txt'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'meta':'urn:oasis:names:tc:opendocument:xmlns:meta:1.0'}
W=lambda x:'{'+NS['w']+'}'+x


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text(node):return ''.join(node.xpath('.//w:t/text()',namespaces=NS))
def compact(value):return re.sub(r'\s+','',value)


def read_docx(path):
    with ZipFile(path) as archive:
        return E.fromstring(archive.read('word/document.xml')),E.fromstring(archive.read('word/styles.xml'))


def scope_copy(source,destination,start,end):
    with ZipFile(source) as archive:
        parts={name:archive.read(name) for name in archive.namelist()}
        xml=E.fromstring(parts['word/document.xml'])
        body=xml.find('w:body',NS)
        for i,child in enumerate(list(body)):
            if child.tag!=W('sectPr') and not start<=i<end:body.remove(child)
        parts['word/document.xml']=E.tostring(xml,encoding='UTF-8',xml_declaration=True,standalone=True)
        with ZipFile(destination,'w') as target:
            for item in archive.infolist():target.writestr(item,parts[item.filename])
    return xml


def word_count(source,out_dir):
    # Dedicated bundled LO profile prevents interference with native apps and
    # the separate render job. The main source file is only opened for reading.
    with tempfile.TemporaryDirectory(prefix='recall-length-lo-') as folder:
        profile=Path(folder)/'profile'
        command=[str(SOFFICE),'-env:UserInstallation='+profile.as_uri(),
                 '--headless','--nologo','--nodefault','--nolockcheck',
                 '--convert-to','odt:writer8','--outdir',str(out_dir),str(source)]
        process=subprocess.run(command,capture_output=True,text=True,timeout=55)
    odt=out_dir/(source.stem+'.odt')
    assert process.returncode==0 and odt.is_file(), (command,process.returncode,process.stdout,process.stderr)
    with ZipFile(odt) as archive:meta=E.fromstring(archive.read('meta.xml'))
    node=meta.find('.//meta:document-statistic',NS)
    assert node is not None
    values={E.QName(k).localname:int(v) for k,v in node.attrib.items()}
    assert {'word-count','character-count','non-whitespace-character-count'}<=set(values)
    return values,odt,{'command':command,'exit_code':process.returncode,'stdout':process.stdout,'stderr':process.stderr}


def style_tools(styles):
    by_id={s.get(W('styleId')):s for s in styles.findall('w:style',NS)}
    defaults=styles.find('w:docDefaults',NS)
    def chain(style_id):
        seen=set();items=[]
        while style_id and style_id not in seen:
            seen.add(style_id);style=by_id.get(style_id)
            if style is None:break
            items.append(style)
            based=style.find('w:basedOn',NS);style_id=based.get(W('val')) if based is not None else None
        return list(reversed(items))
    def properties(paragraph,run=None):
        pp=paragraph.find('w:pPr',NS)
        sid=pp.find('w:pStyle',NS) if pp is not None else None
        sources=[]
        if defaults is not None:
            sources.extend([defaults.find('w:pPrDefault/w:pPr',NS),defaults.find('w:rPrDefault/w:rPr',NS)])
        for style in chain(sid.get(W('val')) if sid is not None else 'Normal'):
            sources.extend([style.find('w:pPr',NS),style.find('w:rPr',NS)])
        sources.append(pp)
        if run is not None:
            rp=run.find('w:rPr',NS)
            rs=rp.find('w:rStyle',NS) if rp is not None else None
            if rs is not None:
                sources.extend(s.find('w:rPr',NS) for s in chain(rs.get(W('val'))))
            sources.append(rp)
        result={}
        for source in sources:
            if source is None:continue
            for el in source:
                key=E.QName(el.tag).localname
                result.setdefault(key,{})
                result[key].update({E.QName(k).localname:v for k,v in el.attrib.items()})
        return result
    return properties


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--docx',type=Path,default=OUT/'论文修订稿-三部门版.docx')
    ap.add_argument('--render-pdf',type=Path,required=True)
    ap.add_argument('--visual-qa',type=Path,default=OUT/'final_evidence_visual_QA.json')
    ap.add_argument('--reuse-authoring-batch',action='store_true',required=True,
                    help='Root confirms its document editing batch has already started; scratch excerpts belong to that same QA batch')
    args=ap.parse_args()
    assert args.docx.resolve()==(OUT/'论文修订稿-三部门版.docx').resolve()
    assert args.render_pdf.resolve().is_relative_to(OUT) and args.visual_qa.resolve().is_relative_to(OUT)
    assert SOFFICE.is_file() and args.docx.is_file() and args.render_pdf.is_file()
    assert sha(TEMPLATE)=='9d53ceb26f2f3b869edf09c4ce260af1ba1dd39971a543f21a565c3b8014a7e3'
    assert sha(GUIDANCE)=='1308753d206005ce870fafd5f1dd8f0f3af51bd5d1c46663fe7f837968ce9412'
    initial={str(p):sha(p) for p in (args.docx,args.render_pdf,args.visual_qa,TEMPLATE,GUIDANCE,Path(__file__))}
    visual=json.loads(args.visual_qa.read_text())
    assert str(visual['status']).startswith('passed')
    document_binding=visual['document_bindings'][args.docx.name]
    assert Path(document_binding['path']).resolve()==args.docx.resolve() and document_binding['sha256']==sha(args.docx)
    assert visual['main_render_sha256']==sha(args.render_pdf)
    pages=len(pdfium.PdfDocument(args.render_pdf))
    assert visual['main_page_count']==pages
    page_reviews=[]
    for row in visual['actual_viewed_main_pages']:
        digest=row.get('png_sha256') or row.get('sha256')
        candidates=[Path(row['path'])] if row.get('path') else list(args.render_pdf.parent.glob(f'page-{row["page"]}.png'))
        matching=[p for p in candidates if p.resolve().is_relative_to(OUT) and p.is_file() and sha(p)==digest]
        assert len(matching)==1, ('Recorded actual page image mismatch',row)
        page_reviews.append({'page':row['page'],'path':str(matching[0].resolve()),'sha256':digest,
            'actually_opened_and_viewed':True,'review_record_source':str(args.visual_qa.resolve()),
            'finding':row.get('finding') or 'Actual viewing and layout findings are recorded in the root visual QA bound to this exact DOCX and render; this script does not claim a second visual review.'})
    assert len({r['page'] for r in page_reviews})==len(page_reviews)
    xml,styles=read_docx(args.docx);body=xml.find('w:body',NS);children=list(body)
    starts=[i for i,c in enumerate(children) if c.tag==W('p') and re.match(r'^1\s*引\s*言',text(c))]
    endings=[i for i,c in enumerate(children) if c.tag==W('p') and re.match(r'^(?:附录\s*[A-Z]|参考文献)',text(c))]
    assert len(starts)==1 and endings and starts[0]<min(endings)
    body_start,body_end=starts[0],min(endings)
    work=OUT/'final-length-audit';work.mkdir(exist_ok=True)
    fragments=work/'internal-excerpts';fragments.mkdir(exist_ok=True)
    front_path=fragments/'前置与正文不含附录参考文献.docx'
    body_path=fragments/'正文不含前置附录参考文献.docx'
    front_xml=scope_copy(args.docx,front_path,0,body_end)
    body_xml=scope_copy(args.docx,body_path,body_start,body_end)
    counts={};execution=[]
    scopes=[('full',args.docx,xml,'全文，含中英前置、正文、表内文字、附录、参考文献'),
            ('front_and_body',front_path,front_xml,'中英前置＋正文及表格，不含附录与参考文献'),
            ('body',body_path,body_xml,'从1引言至附录前的正文及表格，不含前置、附录与参考文献')]
    for name,path,tree,description in scopes:
        stats,odt,call=word_count(path,work)
        content=''.join(tree.xpath('//w:body//w:t/text()',namespaces=NS))
        counts[name]={'scope':description,'libreoffice_word_count':stats['word-count'],
            'libreoffice_character_count':stats['character-count'],
            'libreoffice_non_whitespace_character_count':stats['non-whitespace-character-count'],
            'ooxml_cjk_character_count':len(re.findall(r'[\u4e00-\u9fff]',content)),
            'ooxml_non_whitespace_character_count':len(compact(content)),
            'odt_path':str(odt.resolve()),'odt_sha256':sha(odt),'actual_odt_meta_document_statistics':stats,
            'source_scope_file':str(path.resolve()),'source_scope_file_sha256':sha(path)}
        execution.append({'scope':name,**call})
    paragraphs=body.findall('w:p',NS);texts=[text(p) for p in paragraphs]
    abstract=[t for t in texts if re.match(r'^摘\s*要\s*[：:]',t)]
    keywords=[t for t in texts if re.match(r'^关键词\s*[：:]',t)]
    english=[i for i,t in enumerate(texts) if re.match(r'^Abstract\s*:',t)]
    assert len(abstract)==len(keywords)==len(english)==1
    abstract_value=re.sub(r'^摘\s*要\s*[：:]\s*','',abstract[0])
    keyword_values=[x.strip() for x in re.split('[;；]',re.sub(r'^关键词\s*[：:]\s*','',keywords[0])) if x.strip()]
    effective=style_tools(styles)
    title=paragraphs[0];title_run=next(r for r in title.findall('w:r',NS) if text(r))
    title_props=effective(title,title_run)
    samples=[]
    for child in children[body_start:body_end]:
        if child.tag!=W('p') or len(text(child))<50 or re.match(r'^(?:\d+(?:\.\d+)*\s|图\s*\d|表\s*\d|注[：:]|资料来源[：:]|数据来源[：:]|Fig\.|Table)',text(child)):continue
        regular=[r for r in child.findall('w:r',NS) if text(r) and r.find('w:rPr/w:vertAlign',NS) is None]
        if regular:
            props=effective(child,regular[0]);samples.append({'paragraph_start':text(child)[:70],
                'font_points':float(props.get('sz',{}).get('val',0))/2,
                'fonts':props.get('rFonts',{}),'line_spacing':props.get('spacing',{})})
    assert samples
    tables=body.findall('w:tbl',NS);table_sizes=[]
    for table in tables:
        for paragraph in table.findall('.//w:p',NS):
            for run in paragraph.findall('w:r',NS):
                if text(run):table_sizes.append(float(effective(paragraph,run).get('sz',{}).get('val',0))/2)
    checks={
        'chinese_front_before_english':texts.index(abstract[0])<english[0],
        'chinese_abstract_non_whitespace_characters_excluding_label':len(compact(abstract_value)),
        'keywords_count':len(keyword_values),'keywords_within_official_3_to_8':3<=len(keyword_values)<=8,
        'table_count':len(tables),'table_font_size_points_counts':dict(Counter(table_sizes)),
        'all_table_content_font_size_10_5':bool(table_sizes) and set(table_sizes)=={10.5},
        'chinese_title_points':float(title_props.get('sz',{}).get('val',0))/2,
        'chinese_title_font':title_props.get('rFonts',{}).get('eastAsia'),
        'chinese_title_centered':title_props.get('jc',{}).get('val')=='center',
        'body_font_size_12':all(s['font_points']==12 for s in samples),
        'body_chinese_font_song':all(s['fonts'].get('eastAsia')=='宋体' for s in samples),
        'body_latin_font_Times_New_Roman':all(s['fonts'].get('ascii')=='Times New Roman' for s in samples),
        'body_line_spacing_1_5':all(s['line_spacing'].get('line')=='360' and s['line_spacing'].get('lineRule','auto')=='auto' for s in samples),
        'english_abstract_llm_expanded':bool(re.search(r'Large\s+Language\s+Model.*LLM',texts[english[0]],re.I)),
        'single_column':all(not x.get(W('num')) or x.get(W('num'))=='1' for x in xml.findall('.//w:sectPr/w:cols',NS)),
    }
    required=['chinese_front_before_english','keywords_within_official_3_to_8','all_table_content_font_size_10_5',
              'chinese_title_centered','body_font_size_12','body_chinese_font_song','body_latin_font_Times_New_Roman','body_line_spacing_1_5','english_abstract_llm_expanded','single_column']
    failures=[k for k in required if checks[k] is not True]
    if checks['chinese_title_points']!=14 or checks['chinese_title_font']!='黑体':failures.append('Chinese title black font 14 pt')
    assert initial=={p:sha(Path(p)) for p in initial}, 'Main document/render/source changed during length/template QA'
    version=subprocess.run([str(SOFFICE),'--version'],capture_output=True,text=True,timeout=15)
    report={'status':'passed_for_actual_length_and_explicit_template_items' if not failures else 'template_items_require_revision',
        'checked_at':datetime.datetime.now().astimezone().isoformat(),'reviewer':'statistics agent actual LO count and OOXML checks; root actual visual-review record reused with exact source binding',
        'main_docx_path':str(args.docx.resolve()),'main_docx_sha256':sha(args.docx),
        'render_pdf_path':str(args.render_pdf.resolve()),'render_pdf_sha256':sha(args.render_pdf),
        'rendered_pages':pages,'actually_reviewed_pages':[r['page'] for r in page_reviews],'page_reviews':page_reviews,
        'word_counts':counts,'count_method':{'engine':'Actual bundled headless LibreOffice conversion to ODT; fresh meta:document-statistic from each resulting ODT',
            'bundled_soffice_path':str(SOFFICE),'bundled_soffice_sha256':sha(SOFFICE),'bundled_version':version.stdout.strip(),
            'scopes':'Two internal OOXML excerpt copies from this exact final DOCX, retaining the original styles and tables; original DOCX untouched.',
            'authoring_batch':'Internal QA derivatives within root already-started document editing batch; no new final DOCX/XLSX or marker created.',
            'not_claimed':'No Microsoft Word execution, raster-image OCR count or unspecified journal counting convention. ODT metadata page-count is not pagination evidence.',
            'actual_conversion_calls':execution},
        'template':{'official_url':'https://www.qkkxjc.cn/news/exportNewFile?id=69','cached_snapshot_verified_at':'2026-10-06',
            'path':str(TEMPLATE),'sha256':sha(TEMPLATE),
            'length_guidance_source_url':'https://www.qkkxjc.cn/contribution-invited',
            'length_guidance_snapshot_path':str(GUIDANCE),'length_guidance_snapshot_sha256':sha(GUIDANCE),
            'length_guidance':'篇幅以9000–15000字为宜',
            'length_interpretation':'Official notice does not define the counting unit or inclusion of front matter/appendices/references. Actual three-scope LibreOffice word counts and separate character counts are disclosed; a numeric interval check does not redefine the journal unit.',
            'numeric_word_count_interval_checks':{k:9000<=v['libreoffice_word_count']<=15000 for k,v in counts.items()},
            'abstract_guidance':'300字左右；报告实测，不将模板没有给出的范围另设为合格线。',
            'checks':checks,'failed_explicit_items':failures,'body_typography_samples':samples,
            'pending_identity_items':['匿名稿作者、单位、作者简介和真实基金信息需由作者补齐。'],
            'scope_limits':'Checks actual length and the explicitly enumerated structural/font items. Actual page viewing is owned by root and separately bound; this script does not certify journal acceptance, every typographic rule or actual independent human coding.'},
        'source_sha256':initial}
    target=OUT/'最终篇幅与模板核验.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'word_counts':{k:v['libreoffice_word_count'] for k,v in counts.items()},
        'rendered_pages':pages,'failed_explicit_items':failures,'output':str(target)},ensure_ascii=False))


if __name__=='__main__':main()
