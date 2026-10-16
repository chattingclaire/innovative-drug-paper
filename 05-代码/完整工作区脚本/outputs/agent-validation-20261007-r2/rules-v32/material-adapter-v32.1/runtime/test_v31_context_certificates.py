"""Validate source-bound v31 material without reading any reference labels."""
import unittest,json,copy,hashlib
from pathlib import Path
from context_validation import validate_added_parents

INPUT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/recall-revision-20261007/rule_inputs_v31_shared_v3.jsonl')
class SourceContextCertificates(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=[json.loads(x)['input'] for x in INPUT.read_text().splitlines()]
  cls.parent=next(r for r in cls.rows if any(p.get('repair_version')=='v31-source-list-predicate' for p in r.get('verified_parent_context',[])))
  cls.scope=next(r for r in cls.rows if any(p.get('repair_version')=='v31-source-object-scope' for p in r.get('verified_parent_context',[])))
  cls.table=next(r for r in cls.rows if r.get('verified_table_header'))
 def assertInvalid(self,r):
  with self.assertRaises((ValueError,OSError)):validate_added_parents(r)
 def cert(self,r):return next(p for p in r['verified_parent_context'] if p.get('repair_version')=='v31-source-list-predicate')
 def test_all_material_certificates_valid(self):
  for r in self.rows:validate_added_parents(r)
  self.assertEqual(sum(p.get('repair_version')=='v31-source-list-predicate' for r in self.rows for p in r.get('verified_parent_context',[])),310)
  self.assertEqual(sum(p.get('repair_version')=='v31-source-object-scope' for r in self.rows for p in r.get('verified_parent_context',[])),434)
  self.assertEqual(sum(bool(r.get('verified_table_header')) for r in self.rows),40)
 def test_parent_unit_source_candidate_bindings(self):
  for key in ['unit_text','unit_id','unit_source_sha256','candidate_sha256']:
   r=copy.deepcopy(self.parent);r[key]+='tampered';self.assertInvalid(r)
 def test_parent_text_tampered_even_with_recomputed_hash(self):
  r=copy.deepcopy(self.parent);c=self.cert(r);c['text']+='不存在的创新资格';c['text_sha256']=hashlib.sha256(c['text'].encode()).hexdigest();self.assertInvalid(r)
 def test_parent_target_text_tampered_even_with_recomputed_hash(self):
  r=copy.deepcopy(self.parent);r['unit_text']+='不存在的新条件';c=self.cert(r);c['original_unit_sha256']=hashlib.sha256(r['unit_text'].encode()).hexdigest();self.assertInvalid(r)
 def test_parent_source_and_candidate_paths_tampered(self):
  for key in ['source_path','candidate_path']:
   r=copy.deepcopy(self.parent);self.cert(r)[key]+='-missing';self.assertInvalid(r)
 def test_parent_locator_verified_and_content_tampering(self):
  for key,value in [('paragraph_id','nonexistent'),('pages',[999]),('source_lines',['forged']),('text_sha256','bad')]:
   r=copy.deepcopy(self.parent);self.cert(r)[key]=value;self.assertInvalid(r)
  r=copy.deepcopy(self.parent);self.cert(r)['verification']['verified']=False;self.assertInvalid(r)
 def test_table_hash_source_and_text_tampering(self):
  for key,value in [('source_sha256','forged'),('source_path','/nonexistent'),('text','错误标题\n序号\n评估维度\n评估指标\n指标导向')]:
   r=copy.deepcopy(self.table);r['verified_table_header'][key]=value;r['llm_v29_shared_context']['verified_table_header']=copy.deepcopy(r['verified_table_header']);self.assertInvalid(r)
 def test_table_column_order_source_bound(self):
  r=copy.deepcopy(self.table);c=r['verified_table_header'];c['header_cells'][1],c['header_cells'][2]=c['header_cells'][2],c['header_cells'][1];c['text']='各省行动效果监测指标体系\n'+'\n'.join(c['header_cells']);r['llm_v29_shared_context']['verified_table_header']=copy.deepcopy(c);self.assertInvalid(r)
 def test_table_different_shared_material_or_missing_header(self):
  r=copy.deepcopy(self.table);r['llm_v29_shared_context']['verified_table_header']['text']+='变更';self.assertInvalid(r)
  r=copy.deepcopy(self.table);del r['verified_table_header'];self.assertInvalid(r)
 def test_table_row_column_count_must_match(self):
  r=copy.deepcopy(self.table);r['unit_text']+=' | 额外列';self.assertInvalid(r)
 def scopeCert(self,r):return next(p for p in r['verified_parent_context'] if p.get('repair_version')=='v31-source-object-scope')
 def test_scope_source_candidate_unit_bindings(self):
  for key in ['unit_text','unit_id','unit_source_sha256','candidate_sha256']:
   r=copy.deepcopy(self.scope);r[key]+='tampered';self.assertInvalid(r)
  for key in ['source_path','candidate_path']:
   r=copy.deepcopy(self.scope);self.scopeCert(r)[key]+='-missing';self.assertInvalid(r)
 def test_scope_text_and_target_even_recomputed_hash(self):
  r=copy.deepcopy(self.scope);c=self.scopeCert(r);c['text']+='不存在的新目录条件';c['text_sha256']=hashlib.sha256(c['text'].encode()).hexdigest();self.assertInvalid(r)
  r=copy.deepcopy(self.scope);r['unit_text']+='不存在的新条件';self.scopeCert(r)['original_unit_sha256']=hashlib.sha256(r['unit_text'].encode()).hexdigest();self.assertInvalid(r)
 def test_scope_locator_pages_lines_verification_bindings(self):
  for key,value in [('paragraph_id','nonexistent'),('pages',[999]),('source_lines',['forged']),('text_sha256','bad')]:
   r=copy.deepcopy(self.scope);self.scopeCert(r)[key]=value;self.assertInvalid(r)
  r=copy.deepcopy(self.scope);self.scopeCert(r)['verification']['verified']=False;self.assertInvalid(r)
if __name__=='__main__':unittest.main()
