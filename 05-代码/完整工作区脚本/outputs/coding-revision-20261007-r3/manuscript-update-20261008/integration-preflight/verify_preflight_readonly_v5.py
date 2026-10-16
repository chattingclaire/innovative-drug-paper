"""Independent read-only check of the integration preflight; no statistical reads."""
import hashlib, json, re, subprocess, sys, tempfile
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

D = Path(__file__).parent
OUT = D / 'snapshot-20261008-v5'
P = D.parent
BASE = P.parents[1] / 'final-three-department-20261007/论文修订稿-三部门版.docx'
H = lambda b: hashlib.sha256(b).hexdigest()
J = lambda p: json.loads(p.read_text())
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
text = lambda node: ''.join(x.text or '' for x in node.iter(W + 't'))

def main():
    repfile = P / '完整论文局部替换稿-v5.json'
    keysfile = P / '新引用接入清单.json'
    immutable = [BASE, repfile, keysfile]
    before = {str(p): H(p.read_bytes()) for p in immutable}
    assert before[str(BASE)] == '4ca9e0b4340f045a4f8dd6c2bbb83bd4c8ff88bf1f01426be2f7e397d4923fae'
    staged, keys = J(repfile), J(keysfile)['source_keys']
    replacements = {r['zero_based_body_p_index']: r for r in staged['replacements']}
    report, cite = J(OUT/'接入预检结果.json'), J(OUT/'引用重排与未用文献清单.json')
    inventory, freeze = J(OUT/'OOXML保留清单.json'), J(OUT/'output_freeze.json')
    assert all(report['inputs'][str(p)]['sha256'] == before[str(p)] for p in immutable)
    with ZipFile(BASE) as z:
        parts = {p: z.read(p) for p in z.namelist()}
    body = etree.fromstring(parts['word/document.xml']).find(W+'body')
    ps, tables = body.findall(W+'p'), body.findall(W+'tbl')
    assert len(ps) == 173 and len(tables) == 4 and len(replacements) == 52
    for i,r in replacements.items():
        assert text(ps[i]) == r['old_text']
        assert H(text(ps[i]).encode()) == r['old_text_sha256']
    assert all(inventory['part_inventory'][p]['sha256'] == H(b) for p,b in parts.items())
    assert set(parts) == set(inventory['part_inventory'])
    assert all(H((OUT/p).read_bytes()) == h for p,h in freeze['files'].items())
    assert H(Path(freeze['script']['path']).read_bytes()) == freeze['script']['sha256']
    # Rebuild the text stream independently, including table 1/4 paragraphs.
    stream = []; pi = 0; ti = 0
    for node in body:
        if node.tag == W+'p':
            if pi < 110: stream.append(replacements.get(pi,{}).get('replacement_text',text(node)))
            pi += 1
        elif node.tag == W+'tbl':
            ti += 1
            if ti in (1,4): stream.extend(text(p) for p in node.iter(W+'p'))
    tokens = []
    for s in stream:
        for match in re.finditer(r'\[([0-9,，;；\s–—-]+)\]|〔([A-Za-z][A-Za-z0-9_;；,，\s]*)〕', s):
            if match[1] is not None:
                for part in re.split(r'[,，;；]', match[1]):
                    ends = re.split(r'[–—-]',part.strip())
                    tokens.extend('old:'+str(n) for n in range(int(ends[0]),int(ends[-1])+1))
            else:
                for k in re.split(r'[;；,，]',match[2]):
                    item = keys[k.strip()]
                    tokens.append('old:'+str(item['existing_number']) if item.get('existing_number') is not None else 'new:'+k.strip())
    first = list(dict.fromkeys(tokens))
    assert first == [r['identity'] for r in cite['used_bibliography']]
    assert len(first) == 61 and len(set(first)) == 61
    assert [r['new_number'] for r in cite['used_bibliography']] == list(range(1,62))
    assert sorted(r['old_number'] for r in cite['unused_old_entries']) == [39,40,46,48,49,56,57]
    assert any(r.get('body_p_index') == 74 and r['token'] == '[34,37-38]' for r in cite['citation_occurrences'])
    preview = (OUT/'全文接入预览_未成稿.md').read_text()
    fields = set(re.findall(r'\{\{([A-Za-z][A-Za-z0-9_]*)\}\}',preview))
    assert fields == set(staged['measurement_fields']) and len(fields) == 39
    assert len(J(OUT/'39字段待填契约.json')) == 39
    assert all(r['value'] is None for r in J(OUT/'39字段待填契约.json').values())
    assert not report['manuscript_generation_allowed']
    # Exercise the explicit fail-closed mode; temporary derivative text/JSON only.
    with tempfile.TemporaryDirectory(prefix='gatecheck-',dir=D) as temp:
        command = [sys.executable,str(D/'preflight_manuscript_integration_v5.py'),'--out',str(Path(temp)/'out'),'--require-manuscript-ready']
        result = subprocess.run(command,capture_output=True,text=True)
        assert result.returncode == 2, result.stderr
        assert not list(Path(temp).rglob('*.docx'))
        assert J(Path(temp)/'out/接入预检结果.json')['manuscript_generation_allowed'] is False
    assert {str(p): H(p.read_bytes()) for p in immutable} == before
    qa = {'status':'PASS','scope':'read-only integration/identity/citation/placeholder/structural checks; not measurement or rendered-DOCX validation',
          'input_sha256':before,'verified_snapshot':str(OUT),'snapshot_manifest_sha256':H((OUT/'output_freeze.json').read_bytes()),
          'checks':{'baseline_sha_unchanged':True,'all_report_input_hashes_current':True,'52_old_text_and_hash_pairs_match':True,'173_paragraphs_4_tables':True,
                    '16_package_part_hashes_match':True,'independent_citation_order_matches_all61':True,
                    'table4_source_note_p74_included':True,'7_unused_old_refs_identified':True,
                    '39_unfilled_fields_preserved':True,'explicit_ready_mode_returns_exit2':True,
                    'no_DOCX_generated_or_modified':True,'no_candidate03_data_read':True,'no_statistics_or_labels_read_by_verifier':True},
          'remaining':'Complete adopted method/output/execution QA binding, 39 fields, tables2/3, figure2 redraw, semantic/table/example review and final DOCX rendering remain required.'}
    (D/'independent_readonly_QA_v5.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(qa,ensure_ascii=False))

if __name__ == '__main__': main()
