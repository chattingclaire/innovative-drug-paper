"""Edit the retained manuscript only from a complete, adopted measurement payload.

Preparing this script does not author a DOCX. Before the first actual invocation,
run the documents skill operation marker for edit /2 outputs/docx, then render and
inspect every page of both documents. --check-only never writes any artifact.
"""
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from zipfile import ZipFile
import argparse
import hashlib
import json
import re
import sys
from lxml import etree as E

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'outputs/final-three-department-20261007'
BASE = OLD / '论文修订稿-三部门版.docx'
MEMO = OLD / '校核与待确认事项.docx'
BASE_SHA = '4ca9e0b4340f045a4f8dd6c2bbb83bd4c8ff88bf1f01426be2f7e397d4923fae'
MEMO_SHA = 'fcd88872388a4f12c21dc7fe93a18eeeb1935c50519cd61c3efdb23190696f47'
ADAPTER = HERE/'measurement-adapter-v3/assemble_manuscript_payload_r3.py'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
W = lambda name: '{' + NS['w'] + '}' + name
DIMS = ['S', 'E', 'Ec', 'I', 'F']
GROUPS = ['NMPA', 'NHSA', 'NHC']
CN = ['安全性', '有效性', '经济性', '创新性', '公平性']
CITE = re.compile(r'\[(\d+(?:\s*[,，;；–—-]\s*\d+)*)\]|〔([A-Za-z][A-Za-z0-9_]*(?:\s*[;；,，]\s*[A-Za-z][A-Za-z0-9_]*)*)〕')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
plain = lambda node: ''.join(node.xpath('.//w:t/text()', namespaces=NS))


def require(value, message):
    if not value: raise ValueError(message)


def payload_core_sha(payload):
    excluded = {'status','input_bindings','limits','payload_content_sha256',
                'remaining_gates','independent_payload_QA_binding'}
    core = {k:v for k,v in payload.items() if k not in excluded}
    return hashlib.sha256(json.dumps(core, ensure_ascii=False, sort_keys=True,
                                    separators=(',',':'), allow_nan=False).encode()).hexdigest()


def remove_stale_properties(parts):
    if 'docProps/app.xml' not in parts: return
    app = E.fromstring(parts['docProps/app.xml'])
    for node in list(app):
        if E.QName(node).localname in ['Pages','Words','Characters','CharactersWithSpaces','Paragraphs','Lines']:
            app.remove(node)
    parts['docProps/app.xml'] = E.tostring(app, xml_declaration=True, encoding='UTF-8', standalone=True)


def verify_bindings(value):
    found = []
    def walk(obj):
        if isinstance(obj, dict):
            if 'path' in obj and 'sha256' in obj:
                require(Path(obj['path']).is_absolute(), 'Bound input must be absolute')
                require(sha(obj['path']) == obj['sha256'], 'Bound input SHA mismatch: '+obj['path'])
                found.append(obj)
            for item in obj.values(): walk(item)
        elif isinstance(obj, list):
            for item in obj: walk(item)
    walk(value)
    return found


def renumber(text, references):
    def substitution(match):
        numbers = []
        if match[1]:
            for segment in re.split('[,，;；]', match[1]):
                ends = re.split('[–—-]', segment.strip())
                numbers.extend(references['old_number_to_new'][str(i)]
                               for i in range(int(ends[0]), int(ends[-1])+1))
        else:
            numbers.extend(references['source_key_to_new'][key.strip()]
                           for key in re.split('[;；,，]', match[2]))
        return '[' + ','.join(str(n) for n in sorted(set(numbers))) + ']'
    return CITE.sub(substitution, text)


def plot_attention(rows, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    font = FontProperties(fname='/System/Library/Fonts/Supplemental/Songti.ttc')
    colors = ['#2E5266', '#408A8C', '#D9B44A', '#81759B', '#B46D63']
    names = {'NMPA':'药监', 'NHSA':'医保', 'NHC':'卫健'}
    data = {(r['group'], r['method_role']): r for r in rows}
    assert len(data) == 6
    figure, axes = plt.subplots(2, 1, figsize=(8.4, 5.8), sharex=True)
    for ax, role, title in zip(axes, ['rules', 'LLM'], ['自动规则编码', 'LLM编码']):
        for index, group in enumerate(GROUPS):
            row = data[group, role]
            shares = [Fraction(row['dimensions'][d]['exact_fraction']) for d in DIMS]
            assert sum(shares) == 1 and int(row['denominator']) > 0
            start = Fraction(0)
            for j, share in enumerate(shares):
                width = float(100*share)
                ax.barh(index, width, left=float(100*start), height=.57,
                        color=colors[j], edgecolor='white', linewidth=.7,
                        label=CN[j] if index == 0 else None)
                if share >= Fraction(3, 100):
                    ax.text(float(100*(start+share/2)), index, f'{width:.1f}',
                            ha='center', va='center', fontsize=8,
                            color='black' if j == 2 else 'white')
                start += share
        ax.set_yticks(range(3), [names[g] for g in GROUPS], fontproperties=font)
        ax.invert_yaxis(); ax.set_xlim(0, 100)
        ax.set_title(title, fontproperties=font, fontsize=11, loc='left')
        ax.set_xticks(range(0, 101, 20)); ax.set_axisbelow(True)
        ax.grid(axis='x', color='#dddddd', linewidth=.5)
        for side in ['top', 'right', 'left']: ax.spines[side].set_visible(False)
    axes[0].legend(loc='lower center', bbox_to_anchor=(.5, 1.16), ncol=5,
                   frameon=False, prop=font)
    axes[1].set_xlabel('注意力占比（%）', fontproperties=font)
    figure.subplots_adjust(top=.85, bottom=.10, left=.09, right=.985, hspace=.34)
    figure.savefig(destination, dpi=300, facecolor='white')
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload', required=True, type=Path)
    parser.add_argument('--preflight', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args(); payload = read(args.payload)
    if payload.get('status') != 'ready_for_authoring' or payload.get('remaining_fields') != [] or payload.get('remaining_gates') != []:
        print(json.dumps({'status':'not_ready_no_DOCX_written',
                          'payload_status':payload.get('status'),
                          'remaining_fields':payload.get('remaining_fields', 'not supplied')},
                         ensure_ascii=False)); return 2
    leaves = verify_bindings(payload['input_bindings'])
    bindings = {str(Path(b['path']).resolve()):b['sha256'] for b in leaves}
    required = [BASE, HERE/'完整论文局部替换稿-v6.json', args.preflight/'接入预检结果.json',
                args.preflight/'output_freeze.json', args.preflight/'引用重排与未用文献清单.json',
                args.preflight/'OOXML保留清单.json']
    for path in required:
        require(bindings.get(str(path.resolve())) == sha(path), 'Required input not bound: '+str(path))
    require(sha(BASE) == BASE_SHA and sha(MEMO) == MEMO_SHA, 'Retained document template changed')
    adoption_binding = payload['root_adoption_binding']; qa_binding = payload['independent_payload_QA_binding']
    verify_bindings([adoption_binding, qa_binding])
    for b in (adoption_binding, qa_binding):
        require(bindings.get(str(Path(b['path']).resolve())) == b['sha256'], 'Required adoption/QA input not bound')
    require(payload_core_sha(payload) == payload['payload_content_sha256'], 'Payload content changed after independent QA')
    qa = read(qa_binding['path']); adoption = read(adoption_binding['path'])
    verify_bindings(qa['script'])
    require(bindings.get(str(Path(qa['script']['path']).resolve())) == qa['script']['sha256'],
            'Independent QA script is not an unchanged bound input')
    require(qa['status'] == 'PASS' and qa['all_checks_pass'] is True and qa['independent_of_adapter_execution'] is True,
            'Independent numerical QA has not passed')
    require(qa['adoption_sha256'] == adoption_binding['sha256'] and qa['adapter_sha256'] == sha(ADAPTER)
            and qa['payload_content_sha256'] == payload['payload_content_sha256'], 'Independent QA is for other inputs/code')
    require(qa['checked_counts'] == {'fields':39,'replacements':52,'table2_points':80,
                                   'table2_primary_CIs':80,'table3_q':30,'department_directions':15}, 'QA coverage incomplete')
    require(adoption['status'] == 'root_confirmed_complete_method_adoption'
            and adoption['root_adopted_methods_confirmed'] is True
            and adoption['root_semantic_adoption_confirmed'] is True, 'Methods not adopted by root')
    # The binding list is outside the numerical content hash. Rebuild its
    # required dependency closure from the adopted configuration itself.
    sys.path.insert(0, str(ADAPTER.parent))
    from assemble_manuscript_payload_r3 import BoundIO
    adopted_inputs = BoundIO(); adopted_inputs.tree(adoption)
    for path, binding in adopted_inputs.bindings.items():
        require(bindings.get(str(Path(path).resolve())) == binding['sha256'],
                'Adopted dependency missing from payload input bindings: '+path)
    require(args.preflight.resolve() == (HERE/'integration-preflight/snapshot-20261008-v6').resolve(),
            'Use the reviewed v6 preflight snapshot')
    for key, path in [('preflight_report', args.preflight/'接入预检结果.json'),
                      ('preflight_freeze', args.preflight/'output_freeze.json'),
                      ('bibliography', args.preflight/'引用重排与未用文献清单.json'),
                      ('staged_replacements', HERE/'完整论文局部替换稿-v6.json')]:
        require(Path(adoption[key]['path']).resolve() == path.resolve()
                and adoption[key]['sha256'] == sha(path), 'Authoring input differs from adopted '+key)
    require(payload['bibliography_binding'] == adoption['bibliography'], 'Payload bibliography differs from adoption')
    freeze = read(args.preflight/'output_freeze.json')
    for name, expected_sha in freeze['files'].items():
        path = args.preflight/name
        require(sha(path) == expected_sha and bindings.get(str(path.resolve())) == expected_sha,
                'Preflight freeze or binding mismatch: '+name)
    staged = read(HERE/'完整论文局部替换稿-v6.json')
    references = read(args.preflight/'引用重排与未用文献清单.json')
    preservation = read(args.preflight/'OOXML保留清单.json')
    assert set(payload['resolved_fields39']) == set(staged['measurement_fields'])
    replacements = {r['zero_based_body_p_index']:r for r in payload['resolved_replacements']}
    assert len(replacements) == len(staged['replacements']) == 52
    assert len(payload['tables']['2']['rows']) == 11
    assert len(payload['tables']['3']['rows']) == 7
    require(all(len(row) == 6 for row in payload['tables']['2']['rows']), 'Table2 must have six columns')
    require(all(len(row) == 7 for row in payload['tables']['3']['rows']), 'Table3 must have seven columns')
    assert len(payload['figure2_data']) == 6
    require({(r['group'],r['method_role']) for r in payload['figure2_data']} ==
            {(g,m) for g in GROUPS for m in ('rules','LLM')}, 'Figure2 group/method scope differs')
    require(payload['source_scope']['human_validation_completed'] is False
            and payload['source_scope']['three_department_n'] == 4481
            and payload['source_scope']['full_output_n_each'] == 4924, 'Source scope differs from manuscript')
    fields = payload['resolved_fields39']
    for original in staged['replacements']:
        row = replacements[original['zero_based_body_p_index']]
        expected = re.sub(r'\{\{([A-Za-z][A-Za-z0-9_]*)\}\}', lambda m:fields[m[1]], original['replacement_text'])
        require(row['old_text_sha256'] == original['old_text_sha256'] and row['replacement_text'] == expected,
                'Resolved paragraph differs from adopted field substitutions')
    for row in replacements.values():
        assert '{{' not in row['replacement_text'] and '}}' not in row['replacement_text']
    with ZipFile(BASE) as source:
        parts = {info.filename:source.read(info.filename) for info in source.infolist()}
    baseline_parts = dict(parts)
    document = E.fromstring(parts['word/document.xml']); body = document.find('w:body', NS)
    paragraphs = body.findall('w:p', NS); tables = body.findall('w:tbl', NS)
    assert len(paragraphs) == 173 and len(tables) == 4
    for i, row in replacements.items():
        assert hashlib.sha256(plain(paragraphs[i]).encode()).hexdigest() == row['old_text_sha256']
        assert not paragraphs[i].xpath('.//w:drawing', namespaces=NS)
    if args.check_only:
        print(json.dumps({'status':'ready_checks_passed_no_DOCX_written',
                          'bound_files':len(leaves), 'references':len(references['used_bibliography'])})); return 0
    assert args.out is not None and not args.out.exists(), 'Use a fresh authoring output directory'
    args.out.mkdir(parents=True)
    # Formatting helpers are read from the retained manuscript's own builder.
    # They do not import or fill any old statistical data; main() is never called.
    sys.path.insert(0, str(OLD))
    from build_final_manuscript import replace, tablefill, write_parts, toggle
    for i in range(110):
        text = replacements[i]['replacement_text'] if i in replacements else plain(paragraphs[i])
        updated = renumber(text, references)
        if updated != plain(paragraphs[i]): replace(paragraphs[i], updated)
    tablefill(tables[1], payload['tables']['2']['rows'], [1000,1100,2200,1900,1900,1900])
    tablefill(tables[2], payload['tables']['3']['rows'], [1000,1100,1560,1560,1560,1560,1560])
    for index in (0, 3):
        for paragraph in tables[index].xpath('.//w:p', namespaces=NS):
            original = plain(paragraph); updated = renumber(original, references)
            if original != updated: replace(paragraph, updated)
    figure_path = args.out/'图2-三部门五维注意力占比.png'
    plot_attention(payload['figure2_data'], figure_path)
    from PIL import Image
    image = preservation['drawings'][1]; assert image['body_p_index'] == 64
    part = image['images'][0]['part']; parts[part] = figure_path.read_bytes()
    width, height = Image.open(figure_path).size
    for extent in paragraphs[64].xpath('.//wp:extent | .//a:xfrm/a:ext', namespaces=NS):
        extent.set('cy', str(round(int(extent.get('cx'))*height/width)))
    template = deepcopy(paragraphs[111])
    for paragraph in paragraphs[111:]: body.remove(paragraph)
    section = body.find('w:sectPr', NS)
    for item in references['used_bibliography']:
        paragraph = deepcopy(template)
        replace(paragraph, f"[{item['new_number']}] {item['entry']}", False)
        body.insert(body.index(section), paragraph)
    parts['word/document.xml'] = E.tostring(document, xml_declaration=True, encoding='UTF-8', standalone=True)
    remove_stale_properties(parts)
    adopted_inputs.unchanged(); verify_bindings(payload['input_bindings'])
    manuscript = args.out/'论文修订稿-三部门实测结果版.docx'
    write_parts(BASE, manuscript, parts)
    with ZipFile(MEMO) as source:
        memo_parts = {info.filename:source.read(info.filename) for info in source.infolist()}
    memo_xml = E.fromstring(memo_parts['word/document.xml']); memo_body = memo_xml.find('w:body', NS)
    memo_paragraphs = memo_body.findall('w:p', NS); memo_section = memo_body.find('w:sectPr', NS)
    lines = [
        ('title','三部门论文校核与待确认事项'),
        ('body','本文档供作者补齐投稿资料。正文数值由本次核定的完整编码输出及同版统计接入，保留真实执行身份与验证范围。'),
        ('heading','一 当前采用结果'),
        ('body',f"规则版本：{payload['resolved_fields39']['FINAL_RULES_ID']}；LLM版本：{payload['resolved_fields39']['FINAL_LLM_ID']}。三部门51个来源条目、4481个分析单元；4个中央来源条目443单元作制度背景。"),
        ('body','注意力占比为某维编码句次占本部门五维编码句次合计的比例，每组精确五项合计100%。表2为180条概率样本的设计加权比较；60条挑战材料单列，不并入概率估计。'),
        ('body',payload['resolved_fields39']['FINAL_CONCLUSION_ATTENTION_SUMMARY']),
        ('heading','二 真人验证'),
        ('body','现有A/C/T均为AI代理，本轮240条已向开发环节暴露，不能作为独立真人验证。真实人工提交目前为0。预留真人v5两份各240条空白材料尚待实际实施。'),
        ('body','真人应在最终手册与方法冻结后独立阅读句段及同版必要语境，保存首次标签和判定理由，先计算协商前一致性，再记录分歧裁定。新人工参考需要重新计算对应指标，不能只把正文中的身份名称改为真人。'),
        ('body','核心经济性—公平性发现还需核查两维联合判定及分母。双机器方向一致和同提示重复性，不等同于已完成真人效度验证。'),
        ('heading','三 投稿资料'),
        ('body','请作者补齐真实作者顺序、单位中英文名称、通信作者及基金信息，并确认访谈与研讨材料的使用授权和匿名方式。当前正文保留匿名稿身份。'),
        ('body','《科学决策》现行公开格式为中文题名与摘要在前、英文对应内容在后，摘要约300字、关键词3—8个，9000—15000字为宜；最终字数、页数与图表布局以本轮完整渲染核查为准。'),
        ('heading','四 证据范围'),
        ('body',payload['resolved_fields39']['FINAL_ERROR_PATTERN_SUMMARY']),
        ('body','0.80是本项目的诊断目标，不能作为期刊统一录用保证。保留实际低值、四格、零分母和区间状态；不据预期结论选择标签、混合方法版本或填入未发生的检验。'),
        ('body','参考文献核查区分书目、原文取得与具体论点支持。已核2025年官方预警名单；2026年名单发布尚未确认。正文、完整统计、执行记录和待确认事项应共同保留。'),
    ]
    for child in list(memo_body):
        if child.tag != W('sectPr'): memo_body.remove(child)
    for role, text in lines:
        paragraph = deepcopy(memo_paragraphs[0 if role == 'title' else 2 if role == 'heading' else 1])
        replace(paragraph, text, False); toggle(paragraph, 'keepNext', int(role != 'body'))
        memo_body.insert(memo_body.index(memo_section), paragraph)
    memo_parts['word/document.xml'] = E.tostring(memo_xml, xml_declaration=True, encoding='UTF-8', standalone=True)
    remove_stale_properties(memo_parts)
    memo = args.out/'校核与待确认事项.docx'; write_parts(MEMO, memo, memo_parts)
    changed = [name for name, value in parts.items() if value != baseline_parts[name]]
    assert set(changed) <= {'word/document.xml', 'docProps/app.xml', part}
    assert sha(BASE) == BASE_SHA
    report = {'status':'authored_requires_fresh_full_render_and_content_QA',
              'payload':{'path':str(args.payload),'sha256':sha(args.payload)},
              'preflight':str(args.preflight), 'baseline_sha256':BASE_SHA,
              'memo_template_sha256':MEMO_SHA,
              'authoring_sources':[{'path':str(p),'sha256':sha(p)} for p in
                                   (Path(__file__).resolve(), ADAPTER, OLD/'build_final_manuscript.py', OLD/'final_prose.py')],
              'preserved_package_parts':[n for n in parts if n not in changed],
              'changed_package_parts':changed, 'references':len(references['used_bibliography']),
              'figure2_data':payload['figure2_data'],
              'outputs':[{'path':str(p),'sha256':sha(p)} for p in [manuscript,memo]],
              'render_QA_completed':False, 'true_human_validation_completed':False}
    (args.out/'文稿生成与来源绑定.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'status':report['status'],'outputs':[str(manuscript),str(memo)]}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
