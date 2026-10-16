"""Verify final attention CSVs against independently audited exact ratios."""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import json

OUT=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target=OUT/'三部门注意力分布与敏感性.json'
    qa_path=OUT/'三部门数据独立QA.json'
    qa=json.loads(qa_path.read_text())
    assert qa['status']=='passed' and qa['mismatch_count']==0 and qa['target_sha256']==sha(target)
    result=json.loads(target.read_text())
    methods=set(result['primary'])
    assert methods=={'rules_v31','llm_gpt56_sol_v30','A_AI_reference','C_AI_reference'}
    tables={}
    for method in methods:
        sensitivity=result['sensitivities'][method]
        cases={'primary':result['primary'][method],**sensitivity['scenarios'],
               **{'leave_out:'+r['discarded_file']:r['distribution'] for r in sensitivity['leave_one_policy_file_out']}}
        assert len(cases)==61
        tables[method]=cases
    paths=[target,qa_path,OUT/'三部门注意力分布.csv',OUT/'三部门注意力敏感性.csv',Path(__file__)]
    hashes={str(p):sha(p) for p in paths}
    checks=0;row_counts={}
    for filename,n in (('三部门注意力分布.csv',80),('三部门注意力敏感性.csv',4880)):
        rows=list(csv.DictReader((OUT/filename).open(encoding='utf-8-sig')))
        assert len(rows)==n
        keys=set();sums={}
        for row in rows:
            method,scenario,group,dim=(row[k] for k in ('method','scenario','group','dimension'))
            key=(method,scenario,group,dim)
            assert key not in keys;keys.add(key)
            source=tables[method][scenario][group]['dimensions'][dim]
            value=source['attention_share']
            assert value is not None
            ratio=Fraction(value['exact_fraction'])
            assert Fraction(row['attention_share_exact_fraction'])==ratio
            assert float(row['attention_share'])==float(ratio)
            assert float(row['attention_percent'])==100*float(ratio)
            sums[method,scenario,group]=sums.get((method,scenario,group),Fraction())+ratio
            if filename=='三部门注意力分布.csv':
                assert scenario=='primary'
                assert Fraction(row['weighted_known_hit_count_exact_fraction'])==Fraction(source['weighted_known_hit_count']['exact_fraction'])
                denominator=tables[method][scenario][group]['weighted_five_dimension_known_hit_sum']
                assert Fraction(row['five_dimension_known_hit_denominator_exact_fraction'])==Fraction(denominator['exact_fraction'])
                assert ratio==Fraction(row['weighted_known_hit_count_exact_fraction'])/Fraction(row['five_dimension_known_hit_denominator_exact_fraction'])
            checks+=1
        assert all(x==1 for x in sums.values())
        row_counts[filename]=len(rows)
    assert hashes=={p:sha(Path(p)) for p in hashes}
    report={'status':'passed','target_sha256':sha(target),'rows_verified':checks,
            'csv_row_counts':row_counts,'exact_ratio_checks':True,'sum_to_one_checks':True,
            'independent_attention_qa_sha256':sha(qa_path),'source_sha256':hashes}
    (OUT/'注意力CSV核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
