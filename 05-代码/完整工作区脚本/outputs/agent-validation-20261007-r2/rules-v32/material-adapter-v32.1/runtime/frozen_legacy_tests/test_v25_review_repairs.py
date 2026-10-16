"""Paired controls for the five bounded review repairs only.

Includes one explicitly supplied old development excerpt and its constructed
punctuation variant. No candidate477 input or accuracy estimate.
"""
import copy
import hashlib
import unittest
import policy_coding_v25_review_fix as coder

CASES = [{'id': 'O1',
  'category': 'object_binding',
  'role': 'negative_control',
  'input': {'unit_text': '药品企业应评价信息平台建设工作的创新程度。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '药品企业应评价信息平台建设工作的创新程度。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 0},
 {'id': 'O2',
  'category': 'object_binding',
  'role': 'negative_control',
  'input': {'unit_text': '企业经营创新药，软件登记资料给予六年数据保护期。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '企业经营创新药，软件登记资料给予六年数据保护期。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 0},
 {'id': 'O3',
  'category': 'object_binding',
  'role': 'negative_control',
  'input': {'unit_text': '药品申报工作已完成，鼓励软件原创性成果专利布局。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '药品申报工作已完成，鼓励软件原创性成果专利布局。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 0},
 {'id': 'O4',
  'category': 'object_binding',
  'role': 'negative_control',
  'input': {'unit_text': '药品登记会议结束，医疗机构未向患者供应餐食。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '药品登记会议结束，医疗机构未向患者供应餐食。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 0},
 {'id': 'O5',
  'category': 'object_binding',
  'role': 'negative_control',
  'input': {'unit_text': '药品申报已经完成。报告数据库AE发生率。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '药品申报已经完成。报告数据库AE发生率。',
                                   'pages': [1]}]},
  'dimension': 'S',
  'expected': 0},
 {'id': 'O6',
  'category': 'title_anchor',
  'role': 'negative_control',
  'input': {'unit_text': '依据《创新药数据保护期办法》给予申请人文件副本。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '依据《创新药数据保护期办法》给予申请人文件副本。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 0},
 {'id': 'OP1',
  'category': 'object_binding',
  'role': 'positive_control',
  'input': {'unit_text': '根据药品的创新程度制定分类要求。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '根据药品的创新程度制定分类要求。', 'pages': [1]}]},
  'dimension': 'I',
  'expected': 1},
 {'id': 'OP2',
  'category': 'object_binding',
  'role': 'positive_control',
  'input': {'unit_text': '原研药品在满足试验数据提交及注册条件并完成相关申请程序之后，对全部试验数据给予六年数据保护期。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '原研药品在满足试验数据提交及注册条件并完成相关申请程序之后，对全部试验数据给予六年数据保护期。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 1},
 {'id': 'OP3',
  'category': 'object_binding',
  'role': 'positive_control',
  'input': {'unit_text': '加快药品医疗器械原创性成果专利布局。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '加快药品医疗器械原创性成果专利布局。',
                                   'pages': [1]}]},
  'dimension': 'I',
  'expected': 1},
 {'id': 'OP4',
  'category': 'object_binding',
  'role': 'positive_control',
  'input': {'unit_text': '三年未向定点医疗机构供应的药品应予核查。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '三年未向定点医疗机构供应的药品应予核查。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 1},
 {'id': 'OP5',
  'category': 'object_binding',
  'role': 'positive_control',
  'input': {'unit_text': '报告药品ADR发生率及严重程度。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '报告药品ADR发生率及严重程度。', 'pages': [1]}]},
  'dimension': 'S',
  'expected': 1},
 {'id': 'T1',
  'category': 'transaction_only',
  'role': 'negative_control',
  'input': {'unit_text': '药品ADR报告文件仅按编号归档。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '药品ADR报告文件仅按编号归档。', 'pages': [1]}]},
  'dimension': 'S',
  'expected': 0},
 {'id': 'T2',
  'category': 'transaction_only',
  'role': 'negative_control',
  'input': {'unit_text': '请将药品创新程度文件改名为A。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '请将药品创新程度文件改名为A。', 'pages': [1]}]},
  'dimension': 'I',
  'expected': 0},
 {'id': 'T3',
  'category': 'transaction_only',
  'role': 'negative_control',
  'input': {'unit_text': '药品配备情况表的文件格式应更新为PDF。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '药品配备情况表的文件格式应更新为PDF。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 0},
 {'id': 'TP1',
  'category': 'transaction_only',
  'role': 'positive_control',
  'input': {'unit_text': '评价药品创新程度。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '评价药品创新程度。', 'pages': [1]}]},
  'dimension': 'I',
  'expected': 1},
 {'id': 'TP2',
  'category': 'transaction_only',
  'role': 'positive_control',
  'input': {'unit_text': '企业应及时更新药品配备情况。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '企业应及时更新药品配备情况。', 'pages': [1]}]},
  'dimension': 'F',
  'expected': 1},
 {'id': 'L1',
  'category': 'list_completeness',
  'role': 'negative_control',
  'input': {'unit_text': '一类创新药申请应满足以下条件之一：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '一类创新药申请应满足以下条件之一：', 'pages': [1]}],
            'verified_parent_context': [{'text': '药品申报须采用电子提交方式。'}]},
  'dimension': None,
  'expected': 'all_pending'},
 {'id': 'L2',
  'category': 'list_completeness',
  'role': 'negative_control',
  'input': {'unit_text': '一类创新药申请应满足以下条件之一：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '一类创新药申请应满足以下条件之一：本办法自公布之日起施行。',
                                   'pages': [1]}]},
  'dimension': None,
  'expected': 'all_pending'},
 {'id': 'L3',
  'category': 'list_completeness',
  'role': 'positive_complete_input_control',
  'input': {'unit_text': '一类创新药申请应满足以下条件之一：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '一类创新药申请应满足以下条件之一：', 'pages': [1]}],
            'verified_supplemental_context': [{'kind': 'same_article_following_list',
                                               'original_unit_sha256': 'de730eefbf3cbb551b5a335b26eb1c9ae9a19c3f67257a1315721b9196fb0e0d',
                                               'contexts': [{'paragraph_id': 'synthetic-following-list',
                                                             'text': '（一）具有明确临床优势；（二）填补药物治疗空白。',
                                                             'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
                                                             'pages': [1],
                                                             'verification': 'synthetic bound following '
                                                                             'list'}]}]},
  'dimension': None,
  'expected': 'not_pending'},
 {'id': 'LC1',
  'category': 'list_completeness',
  'role': 'positive_missing_input_control',
  'input': {'unit_text': '一类创新药申请应满足以下条件之一：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '一类创新药申请应满足以下条件之一：',
                                   'pages': [1]}]},
  'dimension': None,
  'expected': 'all_pending'},
 {'id': 'LC2',
  'category': 'list_completeness',
  'role': 'positive_complete_input_control',
  'input': {'unit_text': '一类创新药申请应满足以下条件之一：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '一类创新药申请应满足以下条件之一：', 'pages': [1]}],
            'verified_list_context': [{'text': '具有明确临床优势。',
                                       'original_unit_sha256': 'de730eefbf3cbb551b5a335b26eb1c9ae9a19c3f67257a1315721b9196fb0e0d',
                                       'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
                                       'verification': 'synthetic explicit target/list binding',
                                       'pages': [1]}]},
  'dimension': None,
  'expected': 'not_pending'},
 {'id': 'LC3',
  'category': 'list_completeness',
  'role': 'negative_missing_input_control',
  'input': {'unit_text': '药品监督管理部门承担以下职责：',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p', 'text': '药品监督管理部门承担以下职责：', 'pages': [1]}]},
  'dimension': None,
  'expected': 'not_pending'},
 {'id': 'C1',
  'category': 'coreference_topic',
  'role': 'negative_control',
  'input': {'unit_text': '上述义务在协议中明确。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '企业必须保障药品供应。现仅规定财务审计义务。上述义务在协议中明确。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 0},
 {'id': 'CP1',
  'category': 'coreference_topic',
  'role': 'positive_control',
  'input': {'unit_text': '上述义务在协议中明确。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '企业必须保障药品供应。上述义务在协议中明确。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 1},
 {'id': 'CC1',
  'category': 'coreference_topic',
  'role': 'negative_control',
  'input': {'unit_text': '上述义务在协议中明确。',
            'source_sha256': '270c0d536da1e328c882cda409fc95a131d86851b817f538836313cad3b9ed03',
            'paragraph_context': [{'paragraph_id': 'synthetic-p',
                                   'text': '企业必须完成财务审计。上述义务在协议中明确。',
                                   'pages': [1]}]},
  'dimension': 'F',
  'expected': 0}]

class BoundedReviewRepairs(unittest.TestCase):
    def test_explicit_drug_attribute_enumeration(self):
        # V600-0423 text supplied explicitly by the coordinator, already
        # registered development material; not a new observation or holdout.
        text='中药、化学药和生物制品等药品的细化分类和相应的申报资料要求,由国家药品监督管理局根据注册药品的产品特性、创新程度和审评管理需要组织制定,并向社会公布。'
        for value in [text, text.replace('产品特性、','产品特性,')]:
            with self.subTest(punctuation=value):
                r={'unit_text':value,'source_sha256':hashlib.sha256(b'development-control').hexdigest(),
                   'paragraph_context':[{'paragraph_id':'development-control','text':value,'pages':[]}]}
                self.assertEqual(coder.code_unit(r)['labels']['I'],1)
        # The already registered platform-object counterexample remains zero.
        platform=next(c['input'] for c in CASES if c['id']=='O1')
        self.assertEqual(coder.code_unit(platform)['labels']['I'],0)

    def test_registered_constructed_controls(self):
        for case in CASES:
            with self.subTest(id=case['id']):
                original=copy.deepcopy(case['input'])
                out=coder.code_unit(case['input'])
                self.assertEqual(case['input'],original)
                if case['expected']=='all_pending':
                    self.assertEqual(set(out['labels'].values()),{None})
                    self.assertEqual(out['judgement_status'],'undetermined')
                elif case['expected']=='not_pending':
                    self.assertNotEqual(out['judgement_status'],'undetermined')
                    self.assertNotIn(None,out['labels'].values())
                else:
                    self.assertEqual(out['labels'][case['dimension']],case['expected'],out)
                for e in out['evidence']:
                    self.assertEqual(case['input']['unit_text'][e['start']:e['end']],e['text'])

    def test_following_list_binding_and_actual_condition(self):
        full=copy.deepcopy(next(c['input'] for c in CASES if c['id']=='L3'))
        self.assertNotEqual(coder.code_unit(full)['judgement_status'],'undetermined')
        # A stale target binding must be rejected by the existing source contract.
        stale=copy.deepcopy(full)
        stale['verified_supplemental_context'][0]['original_unit_sha256']='0'*64
        with self.assertRaises(AssertionError):coder.code_unit(stale)
        # Merely calling unrelated prose a following list cannot complete it.
        unrelated=copy.deepcopy(full)
        unrelated['verified_supplemental_context'][0]['contexts'][0]['text']='本办法自公布之日起施行。'
        self.assertEqual(coder.code_unit(unrelated)['judgement_status'],'undetermined')
        foreign=copy.deepcopy(full)
        foreign['verified_supplemental_context'][0]['contexts'][0]['source_sha256']='f'*64
        self.assertEqual(coder.code_unit(foreign)['judgement_status'],'undetermined')

    def test_explicit_list_requires_target_binding(self):
        bound=copy.deepcopy(next(c['input'] for c in CASES if c['id']=='LC2'))
        self.assertNotEqual(coder.code_unit(bound)['judgement_status'],'undetermined')
        del bound['verified_list_context'][0]['original_unit_sha256']
        self.assertEqual(coder.code_unit(bound)['judgement_status'],'undetermined')

    def test_preserve_real_evidence_next_to_file_operation(self):
        for text,dimension in [
            ('药品ADR报告文件仅按编号归档；另须报告药品ADR发生率。','S'),
            ('请将药品创新程度文件改名为A；另须评价药品的创新程度。','I'),
            ('药品配备情况表的文件格式应更新为PDF；企业另须更新药品配备情况。','F'),
        ]:
            with self.subTest(dimension=dimension):
                r={'unit_text':text,'source_sha256':hashlib.sha256(b'synthetic-source').hexdigest(),
                   'paragraph_context':[{'paragraph_id':'synthetic-mixed','text':text,'pages':[1]}]}
                self.assertEqual(coder.code_unit(r)['labels'][dimension],1)

if __name__=='__main__':unittest.main()
