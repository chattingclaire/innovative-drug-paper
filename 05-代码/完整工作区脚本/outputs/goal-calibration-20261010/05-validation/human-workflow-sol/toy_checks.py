#!/usr/bin/env python3
"""只构造 toy 来源、未填表；不读研究数据，不输出任一记录的语义答案。"""
import copy
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import workflow as w

HERE = Path(__file__).resolve().parent


def png():
    # 构造 48×32 三行两列格线与合并首行的原图替身；不是实际政策原页。
    width, height = 48, 32
    data = bytearray()
    for y in range(height):
        data.append(0)
        for x in range(width):
            line = x in (0, 47) or y in (0, 10, 20, 31) or (x == 24 and y > 10)
            data += bytes((0, 0, 0) if line else (255, 255, 255))
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(bytes(data))) + chunk(b'IEND', b'')


def make_toy(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    source = root / 'source'
    source.mkdir(mode=0o700)
    image = png()
    ih = w.sha_bytes(image)
    w.put(source / 'assets' / 'constructed-page.png', image)
    # 本toy原始来源本来就是PNG；原页替身、上下页替身逐字节另绑定。
    image2 = image + b'TOY_SECOND_PAGE'  # PNG IEND 后文本不构成研究内容，仅独立字节资产。
    ih2 = w.sha_bytes(image2)
    w.put(source / 'assets' / 'constructed-page2.png', image2)
    def ref(page=1):
        return {'source_sha256': ih if page == 1 else ih2,
                'source_locator': {'physical_pages': [page], 'paragraph_ids': ['P-'+str(page)]},
                'provenance_status': 'binary_source_verified'}
    def ctx(cid, kind, text=None, structure=None, page=1):
        c = {'context_id': cid, 'kind': kind, 'structure': structure or {}, 'source_ref': ref(page)}
        if text is not None:
            c['text'] = text
        return c
    attachments = [{'attachment_id': 'ASSET-page1', 'sha256': ih, 'kind': 'original_source_page', 'source_ref': ref()},
                   {'attachment_id': 'ASSET-page2', 'sha256': ih2, 'kind': 'original_source_page', 'source_ref': ref(2)}]
    rows = []
    units = ['构造甲：以下两项由同一共同谓词连接。', '构造乙：合并总类行包含两个成员。',
             '构造丙：此段跨页，文字“标签/score”是原文，不是答案字段。', '构造丁：引用原文暂缺，按维分别登记所需材料。']
    for i, text in enumerate(units, 1):
        contexts = [ctx('CTX-parent', 'ordered_list', structure={'child_groups': [{'ordered_context_ids': ['CTX-1','CTX-2'], 'position': 1}], 'current_unit_id': 'CURRENT_UNIT'}),
                    ctx('CTX-1', 'paragraph', '构造成员一，原文必须原样保存。'),
                    ctx('CTX-2', 'paragraph', '构造成员二在下一页。', page=2)]
        if i == 2:
            contexts += [ctx('CTX-table', 'table_group_row', structure={
                'physical_grid_row_index_zero_based': 0,
                'physical_merged_cells': [{'start_row': 0, 'end_row': 0, 'start_column': 0, 'end_column': 1}],
                'table_text_context_ids': ['CTX-1', 'CTX-2'], 'image_evidence_ref': 'ASSET-page1',
                'geometry': {'attachment_id': 'ASSET-page1', 'bbox': [0,0,48,32]}})]
            contexts[-1]['headers'] = ['构造总类', '构造成员']
            contexts[-1]['row_cells'] = [{'text': '成员一', 'column_index': 0, 'row_index': 1}, {'text': '成员二', 'column_index': 1, 'row_index': 2}]
        if i == 4:
            contexts.append({'context_id': 'CTX-missing', 'kind': 'cited_reference', 'structure': {'reference_address': '构造指代；非真实缺材案例'},
                             'source_ref': {'source_sha256': None, 'source_locator': {'article': '构造条款'}, 'provenance_status': 'unresolved'}})
        rows.append({'record_id': 'TOY-'+str(i), 'unit_text': text, 'unit_source_ref': ref(),
                     'source_title': '完全构造的非研究教学材料', 'contexts': contexts, 'attachments': copy.deepcopy(attachments),
                     'material_status': 'source_reference_pending' if i == 4 else 'ready',
                     'neutral_material_note': '构造条款原文未提供；不预定任何维度标签。' if i == 4 else None})
    w.put_lines(source / 'records.jsonl', rows)
    asset_list = [{'sha256': ih, 'relative_path': 'assets/constructed-page.png', 'mime_type': 'image/png'},
                  {'sha256': ih2, 'relative_path': 'assets/constructed-page2.png', 'mime_type': 'image/png'}]
    w.put_json(source / 'source-manifest.json', {'schema_version':'neutral-source-draft-1', 'status':'frozen', 'purpose':'toy',
               'records_file':'records.jsonl', 'records_sha256':w.sha_file(source/'records.jsonl'), 'record_count':4,
               'assets':asset_list, 'original_sources':copy.deepcopy(asset_list), 'context_selection_version':'toy-only-1'})
    w.put(root / 'manual.md', '仅用于接口测试的构造手册。此文件不作研究冻结手册。\n'.encode())
    design_rows = [{'record_id':r['record_id'], 'department':'TOY', 'family_id':'TOY-F'+str(i), 'stratum':'TOY-ALL',
                    'N_h':4,'n_h':4,'pi':1,'weight':1} for i,r in enumerate(rows,1)]
    d = {'schema_version':'frozen-draw-draft-1','status':'frozen','purpose':'toy','sampling_execution':'completed',
         'draw_id':'toy-no-research-draw','round_id':'toy-round01','parent_round_id':None,
         'source_manifest_sha256':w.sha_file(source/'source-manifest.json'), 'manual_sha256':w.sha_file(root/'manual.md'),
         'manual_version':'toy-only', 'manual_status':'frozen', 'statistical_plan_sha256':w.sha_bytes(b'toy-only-no-statistical-estimate'),
         'selected_record_ids':[r['record_id'] for r in rows], 'presentation_seeds':{'A':'toy-A-20261010','B':'toy-B-20261010'},
         'executors':{side:{'anonymous_code':'TOY-'+side,'assignment_status':'synthetic_toy','identity_registry_sha256':w.sha_bytes(('synthetic-'+side).encode())} for side in ('A','B')},
         'design_rows':design_rows}
    w.put_json(root/'draw-manifest.json', d)
    return root


class ToyTests(unittest.TestCase):
    def setUp(self):
        # 所有临时测试写在本交付目录；不在系统/tmp或研究目录写入。
        self.temp = tempfile.TemporaryDirectory(prefix='.toy-test-', dir=HERE)
        self.root = make_toy(Path(self.temp.name)/'fixture')

    def tearDown(self):
        self.temp.cleanup()

    def build(self):
        return w.build(self.root/'source', self.root/'draw-manifest.json', self.root/'manual.md', ('TOY-A','TOY-B'), self.root/'output')

    def mutate_source(self, edit):
        p = self.root/'source'/'records.jsonl'
        rows = w.load_lines(p)
        edit(rows)
        p.write_bytes(b''.join(w.canonical(r)+b'\n' for r in rows))
        mp = self.root/'source'/'source-manifest.json'
        m = w.load_json(mp)
        m['records_sha256'] = w.sha_file(p)
        mp.write_bytes(w.canonical(m))

    def test_same_content_different_order_blank_and_images(self):
        result = self.build()
        self.assertEqual(result['N'],4)
        a = w.load_lines(self.root/'output/coder-A/packet.jsonl')
        b = w.load_lines(self.root/'output/coder-B/packet.jsonl')
        self.assertNotEqual([x['content_sha256'] for x in a], [x['content_sha256'] for x in b])
        self.assertEqual(sorted(x['content_sha256'] for x in a),sorted(x['content_sha256'] for x in b))
        self.assertTrue(all(x['blind_id'].startswith('A-') for x in a))
        self.assertTrue(all(x['blind_id'].startswith('B-') for x in b))
        for side in ('A','B'):
            m, records = w.read_packet(self.root/'output'/('coder-'+side))
            blank = w.load_lines(self.root/'output'/('coder-'+side)/'labels.blank.jsonl')
            self.assertEqual(len(blank),4)
            self.assertTrue(all(x['completion_status']=='unfilled' and set(x['dimensions'])==set(w.DIMS) for x in blank))
            self.assertTrue(all(d['value'] is None and d['reason'] is None and d['current_quote'] is None for x in blank for d in x['dimensions'].values()))
            self.assertEqual(len(m['assets']),2)
            for p in records.values():
                w.reject_results(p)
                self.assertNotIn('record_id',p)
                self.assertNotIn('department',p)
            self.assertTrue(any('text' not in c for p in records.values() for c in p['contexts']))
            self.assertTrue(any(c['structure'].get('physical_merged_cells') for p in records.values() for c in p['contexts']))
            self.assertTrue(any(c['source_ref']['source_locator'].get('physical_pages')==[2] for p in records.values() for c in p['contexts']))

    def test_no_overwrite(self):
        self.build()
        before = w.sha_file(self.root/'output/coder-A/packet.jsonl')
        with self.assertRaises(w.ContractError): self.build()
        self.assertEqual(before,w.sha_file(self.root/'output/coder-A/packet.jsonl'))

    def test_deep_result_leak_rejected(self):
        self.mutate_source(lambda rs:rs[0]['contexts'][0]['structure'].update({'child_groups':[{'ordered_context_ids':['CTX-1'],'score':1}]}))
        with self.assertRaises(w.ContractError): self.build()

    def test_unknown_structure_rejected_not_dropped(self):
        self.mutate_source(lambda rs:rs[0]['contexts'][0]['structure'].update({'new_unfrozen_relation':{'x':1}}))
        with self.assertRaises(w.ContractError): self.build()

    def test_dangling_context_rejected(self):
        self.mutate_source(lambda rs:rs[0]['contexts'][0]['structure'].update({'related_context_ids':['CTX-not-there']}))
        with self.assertRaises(w.ContractError): self.build()

    def test_original_unit_id_not_distributed(self):
        self.mutate_source(lambda rs:rs[0]['contexts'][0]['structure'].update({'current_unit_id':'REAL-OLD-ID'}))
        with self.assertRaises(w.ContractError): self.build()

    def test_missing_image_rejected(self):
        (self.root/'source/assets/constructed-page2.png').unlink()
        with self.assertRaises(w.ContractError): self.build()

    def test_corrupt_image_hash_rejected(self):
        (self.root/'source/assets/constructed-page.png').write_bytes(b'wrong bytes')
        with self.assertRaises(w.ContractError): self.build()

    def test_path_traversal_rejected(self):
        with self.assertRaises(w.ContractError): w.local_file(self.root,'../outside.png')
        with self.assertRaises(w.ContractError): w.local_file(self.root,'/absolute.png')

    def test_symlink_rejected(self):
        (self.root/'source/assets/link.png').symlink_to(self.root/'source/assets/constructed-page.png')
        with self.assertRaises(w.ContractError): w.local_file(self.root/'source','assets/link.png')

    def test_manual_hash_mismatch_rejected(self):
        (self.root/'manual.md').write_text('changed',encoding='utf-8')
        with self.assertRaises(w.ContractError): self.build()

    def test_unfrozen_manual_rejected(self):
        p=self.root/'draw-manifest.json'; d=w.load_json(p); d['manual_status']='development'; p.write_bytes(w.canonical(d))
        with self.assertRaises(w.ContractError): self.build()

    def test_unconfirmed_human_rejected(self):
        # 只试接口身份状态，不生成真人材料或改变现有研究状态。
        m,rs,assets,originals,digest=w.read_source(self.root/'source')
        d=w.load_json(self.root/'draw-manifest.json'); d['purpose']='independent_validation'
        with self.assertRaises(w.ContractError): w.check_draw(d,digest,rs,w.sha_file(self.root/'manual.md'),'independent_validation',('TOY-A','TOY-B'))

    def test_blank_submission_cannot_complete_or_seal(self):
        self.build(); folder=self.root/'output/coder-A'
        with self.assertRaises(w.ContractError): w.verify(folder,folder/'labels.blank.jsonl',folder/'submission.blank.json')
        with self.assertRaises(w.ContractError): w.seal(folder,folder/'labels.blank.jsonl',folder/'submission.blank.json',self.root/'invalid-seal')
        self.assertFalse((self.root/'invalid-seal').exists())

    def test_strict_continuous_quote(self):
        w.quote_in('共同谓词',['构造甲：以下两项由同一共同谓词连接。'],'toy')
        with self.assertRaises(w.ContractError): w.quote_in('甲共同谓词',['构造甲：以下两项由同一共同谓词连接。'],'toy')

    def test_label_type_and_null_request_unit_checks_only(self):
        # 单独检验值域与null请求；内存中的符号测试不是对toy/研究记录的语义判读，不写答案文件。
        packet={'unit_text':'构造关系原文','contexts':[],'attachments':[]}
        d={'value':None,'evidence_path':'unknown','current_quote':'构造关系原文','context_quotes':[], 'image_evidence':[],
           'reason':'符号格式测试','path_evidence':{},'material_requests':[]}
        with self.assertRaises(w.ContractError): w.check_evidence(d,'S',packet)
        d['material_requests']=[{'type':'missing_source','current_reference_quote':'构造关系原文','needed_material':'构造确指原文','why_decisive':'仅检验非空请求结构'}]
        self.assertEqual(w.check_evidence(d,'S',packet),1)
        for invalid in (True,False,0.0,1.0,2,'1'):
            bad=copy.deepcopy(d);bad['value']=invalid
            with self.assertRaises(w.ContractError): w.check_evidence(bad,'S',packet)

    def test_i3_f_specific_path_shape_only(self):
        p={'unit_text':'符号测试原文','contexts':[],'attachments':[]}
        for dim,path in [('I','I3'),('F','F_specific')]:
            d={'value':1,'evidence_path':path,'current_quote':'符号测试原文','context_quotes':[], 'image_evidence':[],
               'reason':'不作语义编码，只检验必要字段缺失应拒收','path_evidence':{},'material_requests':[]}
            with self.assertRaises(w.ContractError): w.check_evidence(d,dim,p)

    def test_exclusive_file_write(self):
        p=self.root/'exclusive.txt'; w.put(p,b'first')
        with self.assertRaises(FileExistsError): w.put(p,b'second')
        self.assertEqual(p.read_bytes(),b'first')

    def test_collision_rotation_is_fixed(self):
        result, collision=w.orders(['TOY-1','TOY-2'],{'A':'same','B':'same'})
        self.assertTrue(collision)
        self.assertNotEqual(result['A'],result['B'])


def main():
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToyTests))
    # 保留一套完全构造的可复核输出；所有提交表仍未填，实际研究数据从不读取。
    demo=HERE/'toy-example'
    if not demo.exists():
        make_toy(demo)
        w.build(demo/'source',demo/'draw-manifest.json',demo/'manual.md',('TOY-A','TOY-B'),demo/'output')
    report={'purpose':'constructed_toy_interface_checks_only','tool_version':w.VERSION,'executed_at':w.utc(),
            'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),
            'real_research_units_read':0,'real_sample_drawn':False,'human_coding_executed':False,'semantic_labels_generated':False,
            'all_delivered_label_tables':'unfilled; all five values null; no semantic answers',
            'report':stream.getvalue()}
    # 此QA输出是运行日志，可重复更新；正式首判/包不会使用此覆盖函数。
    (HERE/'toy-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(stream.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
