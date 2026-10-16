"""Independent read-only reconstruction of root's derived share region."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
import json
import hashlib

OUT=Path(__file__).resolve().parent
result_path=OUT/'attention_share_bounds.json'
implementation_path=OUT/'derive_attention_bounds.py'
result=json.loads(result_path.read_text())
source=Path(result['source_path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==result['source_sha256']
stats=json.loads(source.read_text())['statistics']
assert stats['metadata']['family_size']==580
assert stats['metadata']['family_components']=={'coders':2,'dimensions':5,'frozen_strata':29,'endpoints':2}
assert abs(stats['metadata']['alpha']-.05)<1e-15
DIMS=['S','E','Ec','I','F']
GROUPS=['NMPA','NHSA','NHC','GOV']
coding={}
possible={}
for row in stats['department_status_estimates']:
    coding[row['coder'],row['department'],row['dimension'],row['measure']]=row
for row in stats['department_potential_positive_estimates']:
    possible[row['coder'],row['department'],row['dimension']]=row

def sign(a,b):return 1 if a>0 else -1 if b<0 else 0
def bounds(L,U,d):
    # Positive-total domain; derive via cross-dimension monotonicity.
    assert all(0<=a<=b for a,b in zip(L,U))
    if sum(U)==0:return None
    other_max=sum(U)-U[d]
    other_min=sum(L)-L[d]
    bottom=L[d]+other_max
    top=U[d]+other_min
    return F(L[d],bottom) if bottom else F(1), F(U[d],top) if top else F(0)

expected={}
certified=[]
for coder in ['A','C']:
    for group in GROUPS:
        c=[coding[coder,group,d,'1']['ht_total'] for d in DIMS]
        q=[coding[coder,group,d,'pending']['ht_total'] for d in DIMS]
        L=[coding[coder,group,d,'1']['simultaneous_confidence_interval']['population_total_lower'] for d in DIMS]
        K=[coding[coder,group,d,'1']['simultaneous_confidence_interval']['population_total_upper'] for d in DIMS]
        U=[possible[coder,group,d]['simultaneous_confidence_interval']['population_total_upper'] for d in DIMS]
        assert sum(L)>0
        certified.append({'coder':coder,'group':group,'minimum_total':sum(L)})
        for ix,d in enumerate(DIMS):
            expected[coder,group,d]={'point':c[ix]/sum(c), 'known':bounds(L,K,ix),'completed':bounds(L,U,ix),'count':c[ix],'pending':q[ix],'total':sum(c),
                'pending_range':[c[ix]/(sum(c)+sum(q)-q[ix]),(c[ix]+q[ix])/(sum(c)+q[ix])]}
            assert expected[coder,group,d]['known'][0]<=expected[coder,group,d]['point']<=expected[coder,group,d]['known'][1]
            assert expected[coder,group,d]['completed'][0]<=expected[coder,group,d]['point']<=expected[coder,group,d]['completed'][1]

assert len(result['rows'])==40
for row in result['rows']:
    exp=expected[row['coder'],row['group'],row['dimension']]
    assert abs(exp['point']-row['attention_share'])<1e-14
    assert abs(exp['count']-row['weighted_coded_count'])<1e-10
    assert abs(exp['total']-row['weighted_five_dimension_count'])<1e-10
    for name in ['known','completed']:
        observed=row[name+'_count_simultaneous_share_region']
        assert (F(*observed['exact_lower']),F(*observed['exact_upper']))==exp[name]
        assert observed['total_strictly_positive_certified']
    assert all(abs(a-b)<1e-14 for a,b in zip(exp['pending_range'],row['pending_completion_descriptive_range']))

directions={}
assert len(result['department_comparisons'])==60
for row in result['department_comparisons']:
    coder=row['coder'];g,h=row['pair'];d=row['dimension']
    a,b=expected[coder,g,d],expected[coder,h,d]
    assert abs(row['share_difference_point']-(a['point']-b['point']))<1e-14
    for name in ['known','completed']:
        low=a[name][0]-b[name][1];high=a[name][1]-b[name][0]
        obs=row[name+'_simultaneous_difference_region']
        assert F(*obs['exact_lower'])==low and F(*obs['exact_upper'])==high
        assert obs['direction']==sign(low,high)
        directions[coder,g,h,d,name]=sign(low,high)
assert len(result['common_department_directions'])==30
for row in result['common_department_directions']:
    g,h=row['pair'];d=row['dimension']
    da=directions['A',g,h,d,'completed'];dc=directions['C',g,h,d,'completed']
    assert row['common_direction']==(da if da==dc else 0)

within_nonzero=[]
assert len(result['within_department_dimension_comparisons'])==40
for row in result['within_department_dimension_comparisons']:
    group=row['group'];d,k=row['dimension_pair'];s={};raw={}
    for coder in ['A','C']:
        Ld=coding[coder,group,d,'1']['simultaneous_confidence_interval']['population_total_lower']
        Lk=coding[coder,group,k,'1']['simultaneous_confidence_interval']['population_total_lower']
        Ud=possible[coder,group,d]['simultaneous_confidence_interval']['population_total_upper']
        Uk=possible[coder,group,k]['simultaneous_confidence_interval']['population_total_upper']
        s[coder]=sign(Ld-Uk,Ud-Lk)
        raw[coder]={'first_minus_second_count_bounds':[Ld-Uk,Ud-Lk]}
    assert row['coder_directions']==s
    common=s['A'] if s['A']==s['C'] else 0
    assert row['common_direction']==common
    if common:within_nonzero.append({**row,'raw_count_bounds_for_direction_only':raw})

for row in result['overall']:
    coder=row['coder'];d=row['dimension']
    numerator=sum(expected[coder,g,d]['count'] for g in GROUPS)
    denominator=sum(expected[coder,g,dim]['count'] for g in GROUPS for dim in DIMS)
    assert abs(row['attention_share']-numerator/denominator)<1e-14

audit={
    'read_only_review':True,'source_path':str(source),'source_sha256':result['source_sha256'],
    'reviewed_implementation':str(implementation_path),'implementation_sha256':hashlib.sha256(implementation_path.read_bytes()).hexdigest(),
    'reviewed_result':str(result_path),'result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest(),
    'share_rows_reconstructed':40,'exact_pairwise_differences_reconstructed':60,'common_pairwise_decisions_reconstructed':30,
    'within_group_comparisons_reconstructed':40,'within_single_coder_signs_reconstructed':80,'overall_rows_reconstructed':10,
    'all_group_positive_totals_certified':True,'positive_total_certificates':certified,'all_checks_passed':True,
    'nonzero_within_group_directions':within_nonzero,
    'conclusion':'公式、实际端点、精确差值符号及580计数事件的派生方法均无发现错误；跨部门方向全0是新结构区域重算所得，不是旧差值区间照搬。',
    'interpretation_limits':[
      '至少95%同时覆盖承接原580参数事件的有效性；本次派生核验没有重新审计分层随机化、原始抽样记录和每层超几何反演实现。',
      '点份额是记录为1的标签总量构成估计，待定尚未完成；补全描述范围不是抽样置信区间。',
      '组内唯一共同方向是医保经济性高于有效性，不能扩大成高于其他全部维度或完整主导排序。',
      '同组用总量差判符号是合法的，因为两个份额差共享正分母；这些总量差不能作为份额差的数值区间直接入表。',
      '当前所有组ΣL>0，不发生0/0；通用程序对全零框应把该组比较置NA或明确报错，不能让后续exact_lower索引失败或将无定义份额补0。',
      '对新的组内方向如先前方案未预定，应在论述中明确为此次增加的探索性比较；联合事件保守覆盖不等于该比较原先已预注册。',
      '不覆盖AI共同偏差、构念效度、真人验证或政策效果。'
    ]
}
(OUT/'结构比区间-独立复核.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
audit_file=OUT/'指标与变量一致性审查.json'
r=json.loads(audit_file.read_text());r['derived_implementation_readonly_review']=audit;audit_file.write_text(json.dumps(r,ensure_ascii=False,indent=2))
md=OUT/'指标与变量一致性审查.md'
with md.open('a') as f:
    f.write('\n## 已生成结构区间的只读独立复核\n\n')
    f.write('已直接读取根代理的derive_attention_bounds.py、attention_share_bounds.json及原计数统计，从原始端点独立重构40个组别维度比率、60项精确组间差值、30项共同方向、40组内维度对的80项单参照方向及10项总体比率，全部一致。8个组别×参照的计数下界总和均严格大于0，实际不存在退化分母。原580项同时事件的确定性映射有效；没有复用旧固定N差值CI。\n\n')
    f.write('新跨部门60项单参照差值均未排除0，30项共同方向也为0。组内只有医保经济性高于有效性这一对得到A/C共同方向；不能据此说经济性已显著高于所有其他维度。组内用计数差判符号合法，但计数差的数值端点不能直接当作份额差的区间。若该组内比较是本次新增，须标明其探索性地位。\n\n')
    f.write('实际输入没有发现数值或公式错误。通用程序仍应为全零组完善外层NA传播/明确报错；目前region_ratio能返回defined=False，但后续差值提取exact_lower尚依赖所有组结构可定义。此项不影响当前8组均正的结果。独立核查详见“结构比区间-独立复核.json”。\n')
print(json.dumps({k:audit[k] for k in ['share_rows_reconstructed','exact_pairwise_differences_reconstructed','common_pairwise_decisions_reconstructed','within_single_coder_signs_reconstructed','all_checks_passed','nonzero_within_group_directions']},ensure_ascii=False,indent=2))
