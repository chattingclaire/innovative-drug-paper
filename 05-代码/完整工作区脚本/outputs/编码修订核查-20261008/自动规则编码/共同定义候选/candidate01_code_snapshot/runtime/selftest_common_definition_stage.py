"""Constructed migration checks; not policy observations or validity scores."""
from common_definition_stage import revise


def result_for(text, dimensions):
    return {'judgement_status': 'determined', 'drug_object_in_unit': True,
        'drug_object_evidence': {'text': '药品'}, 'evidence': [
            {'dimension': d, 'rule': 'legacy_fixture', 'start': 0, 'end': len(text),
             'text': text, 'subtype': None} for d in dimensions],
        'suppressions': []}


def main():
    cases = [
        ('申请变更药品适应症。', ['I'], {'I': 0}),
        ('连通医疗机构和药店的电子处方，患者凭方取药。', ['F'], {'F': 0}),
        ('检查药品质量标准和纯度。', ['S'], {'S': 0}),
        ('药品价格谈判成功的纳入目录，失败的退出目录。', ['Ec'], {'Ec': 0}),
        ('符合申报条件的药品可以申请调整医保支付范围。', ['Ec'], {'Ec': 0}),
        ('药品存在严重不良反应，须评价其疗效；检查药品纯度。', ['S', 'E'], {'S': 1, 'E': 1}),
        ('降低低收入患者使用该药的自付负担。', [], {'Ec': 1, 'F': 1}),
    ]
    for text, prior, expected in cases:
        got = revise({'unit_text': text}, result_for(text, prior))
        assert all(got['labels'][d] == v for d, v in expected.items()), (text, got['labels'])
        assert all(text[e['start']:e['end']] == e['text'] for e in got['evidence'])
        assert len(got['common_definition_prior_evidence']) == len(prior)
    print('7 constructed final-stage migration checks passed; no empirical validity claim')


if __name__ == '__main__':
    main()
