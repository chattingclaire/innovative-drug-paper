"""Constructed and exposed-source boundary regressions; not validation scores."""
import copy
import json
from pathlib import Path
import unittest
import policy_coding_v27 as coder
import source_context_adapter_v33 as adapter

ROOT = Path(__file__).resolve().parents[2]


def record(text, paragraph=None, parent=None):
    r={'unit_text':text,'paragraph_context':[],'source_sha256':'constructed-test-source'}
    if paragraph:
        r['paragraph_context']=[{'paragraph_id':'constructed','text':paragraph,'pages':[]}]
    if parent:
        r['verified_parent_context']=[{'paragraph_id':'constructed-parent','text':parent,'pages':[]}]
    return r


class Relations(unittest.TestCase):
    def check(self, text, dim, expected, paragraph=None, parent=None):
        out=coder.code_unit(record(text,paragraph,parent))
        self.assertEqual(out['labels'][dim],expected,(text,out))
        for e in out['evidence']:
            self.assertEqual(text[e['start']:e['end']],e['text'])
        for e in out['suppressions']:
            if all(k in e for k in ('start','end','text')):
                self.assertEqual(text[e['start']:e['end']],e['text'])
        return out

    def test_unmet_need_vs_general_effect_or_population(self):
        pairs=[
            ('评价药品填补临床治疗空白的价值。',1),
            ('药物研发需要解决临床未满足的需求。',1),
            ('患者往往无法接受到充分、有效的治疗。',1),
            ('在境内尚无药物获批拟开发的罕见疾病适应症。',1),
            ('药品适用于老年患者和罕见病患者。',0),
            ('该药物能显著提高疗效。',0),
            ('开展药物研究以满足特殊人群用药需求。',0),
            ('药品的临床价值较高，适用于危重患者。',0)]
        for t,e in pairs:
            with self.subTest(t=t):self.check(t,'F',e,
                 paragraph='这是药物早期临床研究。'+t if '无法接受' in t else None)

    def test_trial_access_exception_and_ordinary_trial(self):
        for t,e in [
            ('该试验使肿瘤患者可以更快地获得治疗药物。',1),
            ('终止无效的试验药物治疗，从而有机会接受获益风险明确的治疗。',1),
            ('申办者免费向已入组受试者提供试验药物。',0),
            ('采用2:1随机分组提高患者获得试验药物的概率。',0),
            ('降低试验访视频率，提高患者参与研究的便利性。',0)]:
            with self.subTest(t=t):self.check(t,'F',e)

    def test_supply_continuity_vs_price_cap(self):
        for t,e in [
            ('药品竞价企业须保证市场供应，无合理理由，不得断供。',1),
            ('药品企业应确保药品持续供应。',1),
            ('企业向医保机构供应药品的价格不得超过报价。',0),
            ('办公室应确保打印纸持续供应。',0),
            ('常规试验药品配送应登记签收。',0)]:
            with self.subTest(t=t):self.check(t,'F',e)

    def test_current_payment_vs_benchmark_and_background(self):
        for t,e in [
            ('药品价格高于支付标准的，高出部分由参保人承担。',1),
            ('参保人使用药品发生的费用，符合以下条件的，可由医保基金支付：',1),
            ('药品通过竞价纳入药品目录的，取最低报价作为支付标准。',0),
            ('支付标准是参保人员使用目录内药品时，医保基金支付药品费用的基准。',0),
            ('每月反馈谈判药品纳入医保支付范围的药品费用和基金支出。',0)]:
            with self.subTest(t=t):self.check(t,'F',e)
        self.check('企业可以申报新增药品适应症并申请调整支付范围。','F',0)
        self.check('对申请调整支付范围的药品，根据谈判结果确定是否调整支付范围。','F',1)

    def test_continuity_vs_renegotiation_route(self):
        p='现制定协议期内谈判药品的续约规则如下。'
        self.check('满足以下条件的药品，可以简易续约，续约有效期2年。','F',1,parent=p)
        self.check('谈判失败后可以按原支付范围重新谈判或简易续约。','F',0,parent=p)
        self.check('企业可以提交重新谈判申请。','F',0,parent=p)

    def test_actual_channels_and_configuration(self):
        for t,e in [
            ('动态调整国家基本药物目录。',1),
            ('以药品评价结果作为药品采购目录制定的重要依据。',1),
            ('将定点零售药店纳入“双通道”管理。',1),
            ('将患者纳入临床试验管理。',0),
            ('药品向基层下沉，满足转诊用药需求。',1),
            ('研究药品物流信息系统向基层下沉部署。',0),
            ('推动常见病药品向基层下沉，满足转诊用药需求。',1),
            ('医疗机构应规范开具药品处方。',0),
            ('对药品配送问题建立机制，定期集中配送所需药品。',1),
            ('强化基层药品支付保障和质量安全。',1),
            ('及时报告基层用药品种优化调整情况。',1)]:
            with self.subTest(t=t):self.check(t,'F',e)

    def test_innovation_identity_instrument_and_personnel(self):
        for t,e in [
            ('基础研究和药物作用机制创新是药物研发动力。',1),
            ('提出改进药品剂型、规格的建议。',1),
            ('本规范所指品种为1类创新药。',1),
            ('按现行注册标准批准的1类化学药品可以重新谈判。',0),
            ('鼓励新药研发人员与审评机构沟通。',0),
            ('计划开展创新药物研发鼓励试点计划。',0),
            ('为创新药研发优先配置沟通资源。',1),
            ('申请人通过平台提交创新药沟通申请。',0),
            ('为鼓励药品创新，制定本工作程序。',0)]:
            with self.subTest(t=t):self.check(t,'I',e)
        p='药品上市许可申请时，以下具有明显临床价值的药品，可以申请适用优先审评审批程序：'
        for t in ['（一）防治重大传染病的创新药和改良型新药；','（一）用于急需疾病的创新药；']:
            o=self.check(t,'I',1,parent=p)
            self.assertIn('research_support',o['innovation_subtypes'])
            self.assertNotIn('qualification_advantage',o['innovation_subtypes'])
        self.check('（一）用于急需疾病的创新药；','I',0)
        self.check('（一）申请人上传创新药材料；','I',0,parent=p)

    def test_harm_content_vs_project_and_credit(self):
        for t,e in [
            ('在安全可控的前提下可以采用较低剂量滴定抗肿瘤药。',1),
            ('提交药物的临床、药理毒理及药学研发情况。',1),
            ('执行三查七对，确保给药时间、剂量准确无误。',1),
            ('提交药物临床试验项目风险管理计划。',0),
            ('提交药物毒性风险管理计划。',1),
            ('药物临床试验机构药品安全信用档案制度由中心制定。',0),
            ('报告药品质量安全风险。',1)]:
            with self.subTest(t=t):self.check(t,'S',e)

    def test_economics_actual_payment_and_procedure(self):
        for t,e in [
            ('将创新药支付纳入基金监管重点范围。',1),
            ('强化基层药品支付保障。',1),
            ('该药品通用名被纳入政府定价范围。',1),
            ('通过目录调整模块确认协议信息，包括药品名称、支付标准。',0),
            ('评估药品支付标准并确定新的支付标准。',1),
            ('评价设备采购费用。',0)]:
            with self.subTest(t=t):self.check(t,'Ec',e)


class SourceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[json.loads(x) for x in (ROOT/'rule_inputs_shared_v9.jsonl').read_text().splitlines()]
        cls.scope=next(r['input'] for r in cls.rows if r['input'].get('verified_scope_context_v8'))
        cls.list=next(r['input'] for r in cls.rows if r['input'].get('verified_parent_list_v8'))
        cls.doc=next(r['input'] for r in cls.rows if r['input'].get('verified_document_object_v9'))

    def test_source_authentication_all_supplied_rows(self):
        selected=[r for r in self.rows if any(k in r['input'] for k in
                  ('verified_scope_context_v8','verified_parent_list_v8','verified_document_object_v9'))]
        self.assertEqual(len(selected),209)
        for r in selected:
            with self.subTest(id=r['id']):
                before=copy.deepcopy(r['input']); out=adapter.prepare(r['input'])
                self.assertEqual(r['input'],before)
                self.assertTrue(out['source_context_adaptation_log_v33'])

    def test_scope_text_and_boundary_tampering_rejected(self):
        for kind in ['text','boundary','target','shared']:
            r=copy.deepcopy(self.scope)
            if kind=='text':
                r['verified_scope_context_v8'][0]['text']+='伪造'
                r['llm_v29_shared_context']['verified_scope_context_v8']=copy.deepcopy(r['verified_scope_context_v8'])
            elif kind=='boundary':
                r['llm_v29_shared_context']['verified_context_certificates']['verified_scope_context_v8']['next_structure']='伪造'
            elif kind=='target':r['unit_text']+='伪造'
            else:r['llm_v29_shared_context']['verified_scope_context_v8']=[]
            with self.subTest(kind=kind), self.assertRaises(ValueError):adapter.prepare(r)

    def test_parent_child_and_source_tampering_rejected(self):
        for kind in ['parent','child','source']:
            r=copy.deepcopy(self.list)
            if kind=='parent':r['verified_parent_context'][0]['text']+='伪造'
            elif kind=='child':r['unit_text']='不存在于真实列表的药物条目'
            else:r['verified_parent_list_v8']['source_sha256']='0'*64
            with self.subTest(kind=kind), self.assertRaises(ValueError):adapter.prepare(r)

    def test_document_scope_target_source_and_component_tampering(self):
        for kind in ['unit','actual_source','container','component','quote','role']:
            r=copy.deepcopy(self.doc);c=r['verified_document_object_v9']
            if kind=='unit':c['current_unit_id']='wrong-unit'
            elif kind=='actual_source':c['source_sha256']='0'*64
            elif kind=='container':c['container_source_sha256']='0'*64
            elif kind=='component':c['component_last_paragraph']=c['component_first_paragraph']
            elif kind=='quote':c['contexts'][0]['text']+='伪造'
            else:c['contexts'][0]['role']='inherit_all_dimensions'
            r['llm_v29_shared_context']['verified_context_certificates']['verified_document_object_v9']=copy.deepcopy(c)
            r['llm_v29_shared_context']['verified_document_object_v9']=copy.deepcopy(c['contexts'])
            # The selected row may itself be the declaration. Narrowing the
            # interval still contradicts the actual component end boundary.
            with self.subTest(kind=kind), self.assertRaises(ValueError):adapter.prepare(r)


if __name__=='__main__':unittest.main()
