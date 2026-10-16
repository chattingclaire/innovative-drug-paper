import copy
import unittest
import llm_recoder as m


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.inputs=[{'id':'FICTION-1','text':'提交药品疗效和不良反应资料。','contexts':{}}]
        self.output={'protocol_version':'CAL-5D-20260926-v1.3','rows':[{
            'id':'FICTION-1','labels':dict(S=1,E=1,Ec=0,I=0,F=0),
            'dimension_reasons':{d:'合成接口控制，非政策样本。' for d in m.DIMS},
            'evidence':[{'dimension':'S','source':'unit','quote':'不良反应'},
                        {'dimension':'E','source':'unit','quote':'疗效'}],
            'material_issue':'无','fairness_subtypes':[],'innovation_subtypes':[],
            'safety_quality_basis':'no_quality_basis'}]}

    def test_literal_valid_output(self):
        self.assertEqual(m.validate(self.output,self.inputs),[])

    def test_no_silent_evidence_repair(self):
        self.output['rows'][0]['evidence'][0]['quote']='文中没有的不良事件'
        self.assertIn('FICTION-1:S:nonliteral_evidence',m.validate(self.output,self.inputs))

    def test_missing_or_duplicated_record_fails(self):
        self.output['rows'].append(copy.deepcopy(self.output['rows'][0]))
        self.assertIn('ID_count_order_or_duplicate',m.validate(self.output,self.inputs))

    def test_context_only_label_not_accepted(self):
        self.output['rows'][0]['evidence'][0]['source']='context'
        self.inputs[0]['contexts']={'paragraph_context':[{'text':'观察不良反应'}]}
        self.assertIn('FICTION-1:S:missing_unit_evidence',m.validate(self.output,self.inputs))

    def test_pending_not_zero_and_boolean_not_integer(self):
        self.output['rows'][0]['labels']['S']='待定'
        errors=m.validate(self.output,self.inputs)
        self.assertIn('FICTION-1:partial_pending_not_current_contract',errors)
        self.output['rows'][0]['labels']['S']=True
        self.assertIn('FICTION-1:S:label_type',m.validate(self.output,self.inputs))

    def test_full_protocol_and_clarification_supplied(self):
        prompt=m.system_prompt()
        self.assertIn((m.HERE/'protocol-v1.3.md').read_text(),prompt)
        self.assertIn((m.OLD/'V600-frozen-inputs/protocol_clarifications.md').read_text(),prompt)


if __name__=='__main__':unittest.main()
