"""Independent cross-dimension controls, frozen before full metric inspection."""
import copy
import importlib.util
import unittest
from pathlib import Path
import policy_coding_v27 as coder


def rec(text):
    return {'unit_text':text,'source_sha256':'synthetic-source',
            'paragraph_context':[{'paragraph_id':'p1','text':text,'pages':[1]}]}


CASES = [
    ('该药物未发生严重不良反应。','S',1),
    ('该药物不具有肝毒性。','S',1),
    ('开展药品申报系统的网络安全检查。','S',0),
    ('药品申报工作由具有安全性评价经验的人员承担。','S',0),
    ('该药物对延长总生存期没有显著作用。','E',1),
    ('该药物的临床获益尚不能确认。','E',1),
    ('药品电子申报提高了信息系统运行效率。','E',0),
    ('企业提交药品申报材料，办公设备成本下降。','Ec',0),
    ('该药物的治疗费用由患者自行承担。','Ec',1),
    ('药品注册申请的缴费标准为每件一千元。','Ec',0),
    ('取消对创新药研发的资金支持。','I',1),
    ('药品管理采用创新性的信息系统。','I',0),
    ('药品企业管理创新经验交流会明日举行。','I',0),
    ('患者难以获得所需药物。','F',1),
    ('药品研究的数据可及性得到改善。','F',0),
    ('患者服用药物，医院审批工作面临困难。','F',0),
    ('要求提交《药品安全性、有效性、经济性、创新性和公平性资料清单》。','S',0),
    ('要求提交《药品安全性、有效性、经济性、创新性和公平性资料清单》。','E',0),
    ('要求提交《药品安全性、有效性、经济性、创新性和公平性资料清单》。','Ec',0),
    ('要求提交《药品安全性、有效性、经济性、创新性和公平性资料清单》。','I',0),
    ('要求提交《药品安全性、有效性、经济性、创新性和公平性资料清单》。','F',0),
    ('归档《药品安全性评价报告》，并评价该药物的不良反应。','S',1),
    ('药品企业评价信息平台创新程度，并鼓励创新药研发。','I',1),
    ('药品资料库可及性提高，同时应保障患者获得药物。','F',1),
]


class CrossDimensionTests(unittest.TestCase):
    def test_manual_boundary_controls_and_literal_evidence(self):
        for text,dim,value in CASES:
            with self.subTest(text=text,dimension=dim):
                out=coder.code_unit(rec(text))
                self.assertEqual(out['labels'][dim],value)
                for e in out['evidence']:
                    self.assertEqual(text[e['start']:e['end']],e['text'])

    def test_metadata_permutation_cannot_change_labels(self):
        original=rec('药品评价应充分讨论临床获益。')
        altered=copy.deepcopy(original)
        altered.update(review_id='anything',original_file_stem='公平性创新性药品安全性',
                       source='/arbitrary/location', coder_A_labels={d:1 for d in ('S','E','Ec','I','F')})
        self.assertEqual(coder.code_unit(original)['labels'],coder.code_unit(altered)['labels'])

    def test_missing_text_remains_an_explicit_input_error(self):
        result=coder.code_unit({'unit_text':None})
        self.assertEqual(result['judgement_status'],'undetermined')
        self.assertTrue(all(v is None for v in result['labels'].values()))


def inherited_suite():
    """Reuse frozen semantic controls, substituting only the tested coder."""
    suite=unittest.TestSuite()
    old=Path(__file__).parent/'frozen_legacy_tests'
    for name in ('test_policy_coding_v25','test_v25_review_repairs'):
        spec=importlib.util.spec_from_file_location('inherited_'+name,old/(name+'.py'))
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.coder=coder
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    return suite


def load_tests(loader,tests,pattern):
    tests.addTests(inherited_suite())
    return tests


if __name__=='__main__':
    unittest.main()
