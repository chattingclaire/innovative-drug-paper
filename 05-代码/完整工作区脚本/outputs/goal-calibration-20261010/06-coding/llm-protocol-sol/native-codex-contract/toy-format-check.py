"""Constructed native batch format checks. No thread creation, coding or model inference."""
import copy
import io
import json
import unittest
from jsonschema import Draft202012Validator
from validate_native import ROOT, ContractError, canonical, sha, content_hash, validate_batch, select_first_valid, validate_unavailable_telemetry, comparison_gate

MANUAL = (ROOT.parent / 'snapshots/common-manual-v1.1-development.md').read_bytes()

def fixture():
    ids = [f'B-{90000+i}' for i in range(41)]
    sources, rows = {}, []
    for i, uid in enumerate(ids):
        text = f'构造句段{i+1}，仅验证格式。'
        source = {'packet_version': 'constructed-native-toy', 'manual_version': 'v1.1-development',
                  'blind_id': uid, 'unit_text': text, 'source_title': '构造toy，非政策原文',
                  'contexts': [], 'attachments': [], 'material_status': 'ready'}
        source['content_sha256'] = content_hash(source)
        sources[uid] = source
        evidence = {d: {'paths': ['excluded'], 'current_quote': text, 'current_span': {'start': 0, 'end': len(text)},
                       'contexts_used': [], 'structural_context_ids_used': [], 'image_sources_used': [],
                       'reason': '构造格式占位，不是分类结果或预期答案。', 'innovation_support': None, 'fairness_specific': None} for d in ('S','E','Ec','I','F')}
        rows.append({'blind_id': uid, 'content_sha256': source['content_sha256'], 'manual_sha256': sha(MANUAL),
                     'labels': {d: 0 for d in evidence}, 'evidence': evidence, 'material_requests': []})
    manifest = [{'blind_id': uid, 'packet_binding_sha256': sha(canonical(sources[uid]))} for uid in ids]
    plan = {'run_id': 'TOY_NATIVE_ONLY', 'batch_id': 'TOY_BATCH_41', 'condition': 'R1', 'expected_n': 41,
            'ordered_ids': ids, 'unit_order_sha256': sha(canonical(ids)), 'manual_sha256': sha(MANUAL),
            'source_manifest_sha256': sha(canonical(manifest)), 'prompt_sha256': sha(b'constructed prompt only')}
    payload = {'contract_version': 'native-codex-batch-v1-proposal', **{k: plan[k] for k in ('run_id','condition','batch_id','unit_order_sha256','manual_sha256','source_manifest_sha256','prompt_sha256')}, 'items': rows}
    return sources, plan, payload, {uid: [] for uid in ids}

def attempt(raw, plan, n):
    return {'thread_id': f'TOY_LOGICAL_THREAD_{n}', 'created_fresh': True, 'raw': raw,
            'initial_prompt_sha256': plan['prompt_sha256'], 'additional_user_messages': [],
            'history_mode': 'complete_batch_single_initial_prompt', 'known_context_compaction': False,
            'known_input_truncation': False, 'known_output_truncation': False,
            'visible_read_status': 'complete', 'candidate_sealed_before_check': True}

class NativeToy(unittest.TestCase):
    def setUp(self):
        self.sources, self.plan, self.payload, self.assets = fixture()

    def validate(self, payload):
        return validate_batch(canonical(payload), self.sources, self.plan, self.assets)

    def test_schema_and_original_unit_contract_preserved(self):
        schema = json.loads((ROOT/'native-output.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        original = json.loads((ROOT.parent/'schemas/output.schema.json').read_text())
        original.pop('$schema'); original.pop('$id')
        self.assertEqual(schema['$defs']['unit'], original)
        self.assertEqual(len(self.validate(self.payload)['items']), 41)

    def test_missing_duplicate_extra_and_reordered_rows_rejected(self):
        variants = []
        p=copy.deepcopy(self.payload); p['items'].pop(); variants.append(p)
        p=copy.deepcopy(self.payload); p['items'][1]=copy.deepcopy(p['items'][0]); variants.append(p)
        p=copy.deepcopy(self.payload); p['items'].append(copy.deepcopy(p['items'][0])); variants.append(p)
        p=copy.deepcopy(self.payload); p['items'][0],p['items'][1]=p['items'][1],p['items'][0]; variants.append(p)
        for p in variants:
            with self.assertRaises(ContractError): self.validate(p)

    def test_source_ctx_change_and_wrong_input_hash_rejected(self):
        uid=self.plan['ordered_ids'][0]
        self.sources[uid]['contexts'].append({'context_id':'TOY_NEW'})
        with self.assertRaises(ContractError): self.validate(self.payload)
        self.sources[uid]['contexts']=[]
        p=copy.deepcopy(self.payload); p['prompt_sha256']='0'*64
        with self.assertRaises(ContractError): self.validate(p)

    def test_first_valid_complete_batch_selected_without_splicing(self):
        bad=copy.deepcopy(self.payload); bad['items'][3]['labels']['E']=True
        trials=[attempt(canonical(bad),self.plan,1),attempt(canonical(self.payload),self.plan,2),attempt(canonical(self.payload),self.plan,3)]
        selected=select_first_valid(trials,self.sources,self.plan,self.assets)
        self.assertEqual(selected['selected_attempt'],2); self.assertEqual(len(selected['checks']),2)
        self.assertEqual(len(selected['candidate']['items']),41)

    def test_semantic_null_valid_and_stops_without_more_favorable_candidate(self):
        p=copy.deepcopy(self.payload); row=p['items'][0]
        row['labels']['I']=None; row['evidence']['I']['paths']=['material_missing']
        row['material_requests']=[{'dimension':'I','kind':'material_missing','detail':'构造待补原文请求。','context_ids':[]}]
        selected=select_first_valid([attempt(canonical(p),self.plan,1),attempt(canonical(self.payload),self.plan,2)],self.sources,self.plan,self.assets)
        self.assertEqual(selected['selected_attempt'],1); self.assertIsNone(selected['candidate']['items'][0]['labels']['I'])
        self.assertEqual(len(selected['checks']),1)

    def test_unstarted_and_technical_failure_have_no_semantic_answer(self):
        result=select_first_valid([],self.sources,self.plan,self.assets)
        self.assertEqual(result['state'],'not_executed'); self.assertIsNone(result['candidate'])
        result=select_first_valid([attempt(b'invalid-json',self.plan,1)],self.sources,self.plan,self.assets)
        self.assertIsNone(result['candidate']); self.assertIsNone(result['selected_attempt'])

    def test_reused_thread_feedback_truncation_and_compaction_rejected(self):
        base=attempt(canonical(self.payload),self.plan,1)
        for key,value in [('created_fresh',False),('additional_user_messages',['纠错或续写']),('known_context_compaction',True),('known_input_truncation',True),('known_output_truncation',True),('visible_read_status','unknown')]:
            trial=copy.deepcopy(base); trial[key]=value
            self.assertIsNone(select_first_valid([trial],self.sources,self.plan,self.assets)['candidate'])
        first=attempt(b'bad',self.plan,1); second=copy.deepcopy(base)
        self.assertIsNone(select_first_valid([first,second],self.sources,self.plan,self.assets)['candidate'])

    def test_changed_retry_prompt_and_unsealed_candidate_rejected(self):
        for key,value in [('initial_prompt_sha256','0'*64),('candidate_sealed_before_check',False)]:
            trial=attempt(canonical(self.payload),self.plan,1); trial[key]=value
            self.assertIsNone(select_first_valid([trial],self.sources,self.plan,self.assets)['candidate'])

    def test_quote_traceability_and_duplicate_json_key(self):
        p=copy.deepcopy(self.payload); p['items'][0]['evidence']['S']['current_quote']='不存在的原文'
        with self.assertRaises(ContractError): self.validate(p)
        with self.assertRaises(ContractError): validate_batch(b'{"run_id":"a","run_id":"b"}',self.sources,self.plan,self.assets)

    def test_comparison_waits_for_all_seals_and_rejects_cross_condition_thread_reuse(self):
        records={c:{'state':'first_format_valid_sealed','seal_sha256':sha(c.encode()),'attempt_thread_ids':[f'TOY_{c}'],'selected_candidate_sha256':sha(canonical(self.payload)),**{k:self.plan[k] for k in ('manual_sha256','source_manifest_sha256','unit_order_sha256','prompt_sha256')}} for c in ('R1','R2','R3','W','H')}
        self.assertTrue(comparison_gate(records))
        incomplete=copy.deepcopy(records); incomplete['H']['state']='format_valid_unsealed'
        with self.assertRaises(ContractError): comparison_gate(incomplete)
        changed=copy.deepcopy(records); changed['R2']['prompt_sha256']='0'*64
        with self.assertRaises(ContractError): comparison_gate(changed)
        missing=copy.deepcopy(records); missing['R1']['selected_candidate_sha256']=None
        with self.assertRaises(ContractError): comparison_gate(missing)
        records['W']['attempt_thread_ids']=['TOY_R1']
        with self.assertRaises(ContractError): comparison_gate(records)

    def test_native_assignment_evidence_does_not_become_provider_telemetry(self):
        ledger=json.loads((ROOT/'native-execution-ledger.blank.json').read_text())
        self.assertTrue(validate_unavailable_telemetry(ledger))
        for key,value in [('actual_provider_model_identity','GPT-6.1 Sol'),('seed',0),('temperature',0),('provider_api_call_count',0)]:
            p=copy.deepcopy(ledger); p['telemetry'][key]=value
            with self.assertRaises(ContractError): validate_unavailable_telemetry(p)

    def test_whitespace_and_heading_variants_are_equivalent_and_separate(self):
        source={'text':'构造原文  空格\n保留','contexts':[{'context_id':'TOY','text':None}]}
        main='判读要求\n'+MANUAL.decode()+'\n'+json.dumps(source,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        w='判读要求\n'+MANUAL.decode()+'\n'+json.dumps(source,ensure_ascii=False,sort_keys=True,indent=2)
        h='判读说明\n'+main[len('判读要求\n'):]
        self.assertNotEqual(main,w); self.assertNotEqual(main,h)
        self.assertEqual(json.loads(main.split(MANUAL.decode()+'\n',1)[1]),json.loads(w.split(MANUAL.decode()+'\n',1)[1]))
        self.assertEqual(main[len('判读要求\n'):],h[len('判读说明\n'):])
        self.assertTrue(all(MANUAL.decode() in text for text in (main,w,h)))

def main():
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeToy))
    report={'scope':'constructed_format_only','tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
            'native_threads_created':0,'native_coding_runs_executed':0,'real_policy_units_coded':0,'provider_api_call_count':None,
            'actual_provider_model_identity':None,'stability_executed':False,'checks':stream.getvalue().splitlines()}
    (ROOT/'toy-format-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(stream.getvalue())
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':
    main()
