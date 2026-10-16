import unittest
from analyze_current_reruns import scenario_labels

class SensitivityTest(unittest.TestCase):
    def row(self,**fields):return {'labels':{'S':1,'E':0,'Ec':0,'I':1,'F':1},**fields}
    def test_only_quality_removed_mixed_kept(self):
        for data in [{'safety_quality_basis':'quality_only'},{'safety_subtypes':['quality_safety']}]:
            self.assertEqual(scenario_labels(self.row(**data),'exclude_quality_only')['S'],0)
        self.assertEqual(scenario_labels(self.row(safety_subtypes=['quality_safety','other_safety']),'exclude_quality_only')['S'],1)
    def test_subtype_filters_preserve_other_basis(self):
        r=self.row(fairness_subtypes=['access','clinical_management'],innovation_subtypes=['attribute','qualification_advantage'])
        self.assertEqual(scenario_labels(r,'exclude_F_clinical_management_only')['F'],1)
        self.assertEqual(scenario_labels(r,'exclude_I_qualification_advantage_only')['I'],1)
        self.assertEqual(scenario_labels(r,'F_access_affordability_only')['F'],1)
    def test_unknown_metadata_not_forced_to_zero(self):
        for scenario,dim in [('exclude_quality_only','S'),('F_access_affordability_only','F'),('exclude_I_qualification_advantage_only','I')]:
            self.assertEqual(scenario_labels(self.row(),scenario)[dim],'待定')
    def test_pending_unchanged_and_input_not_mutated(self):
        r=self.row(fairness_subtypes=['clinical_management']);r['labels']['S']='待定'
        self.assertEqual(scenario_labels(r,'exclude_quality_only')['S'],'待定')
        self.assertEqual(scenario_labels(r,'F_access_affordability_only')['F'],0)
        self.assertEqual(r['labels']['F'],1)
    def test_explicit_null_metadata_is_unknown(self):
        for field,scenario,dim in [
            ('safety_subtypes','exclude_quality_only','S'),
            ('fairness_subtypes','F_access_affordability_only','F'),
            ('innovation_subtypes','exclude_I_qualification_advantage_only','I')]:
            r=self.row(**{field:None})
            self.assertEqual(scenario_labels(r,scenario)[dim],'待定')
            self.assertEqual(scenario_labels(r,'primary'),r['labels'])
            self.assertIsNone(r[field])
    def test_invalid_metadata_type_is_explicitly_rejected(self):
        for field,value in [('fairness_subtypes','access'),('innovation_subtypes',1),('safety_subtypes',[None])]:
            with self.assertRaises(ValueError):scenario_labels(self.row(**{field:value}),'primary')

if __name__=='__main__':unittest.main()
