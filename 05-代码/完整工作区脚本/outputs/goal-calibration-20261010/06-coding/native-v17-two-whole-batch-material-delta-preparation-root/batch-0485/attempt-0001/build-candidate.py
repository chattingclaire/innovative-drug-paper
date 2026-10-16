import json
from pathlib import Path

slot = Path(__file__).resolve().parent
assignment_path = slot.parent / 'assignment.json'
a = json.loads(assignment_path.read_text())
packets = [json.loads(Path(binding['path']).read_text()) for binding in a['packets']]
current_pointer = '/source_bundle/source_record/text'

def evidence(i, context=None):
    record = packets[i]['source_bundle']['source_record']
    if context is None:
        return {'pointer': current_pointer, 'quote': record['text'], 'role': 'current'}
    return {'pointer': f'/source_bundle/source_record/contexts/{context}/text',
            'quote': record['contexts'][context]['text'], 'role': 'context'}

standard = (
    '第六十三条\n'
    '药物临床试验期间，符合以下情形的药品，可以申请附条件批准：\n'
    '（一）治疗严重危及生命且尚无有效治疗手段的疾病的药品，药物临床试验已有数据证实疗效并能预测其临床价值的；\n'
    '（二）公共卫生方面急需的药品，药物临床试验已有数据显示疗效并能预测其临床价值的；\n'
    '（三）应对重大突发公共卫生事件急需的疫苗或者国家卫生健康委员会认定急需的其他疫苗，经评估获益大于风险的。'
)
asset = a['source_asset_bindings'][0]
asset_standard = {'asset_path': asset['path'], 'asset_sha256': asset['sha256'],
                  'page': 'TXT L208-L217; Unicode code points [10374,10720)',
                  'quote': standard, 'role': 'context'}
inline_standard = {'pointer': '/source_bundle/source_full_text_resources/0/text',
                   'quote': standard, 'role': 'context'}

decisions = [
    {
        'S': (0, '当前严重危及生命描述的是疾病本身；疗效数据条件没有评价药物损害或规定用药风险控制，故不记安全性。', []),
        'E': (1, '当前以申请附条件批准的药品为对象，要求临床试验数据证实疗效并能预测临床价值，且明确尚无有效治疗手段，实质涉及效果证据及有效选项缺失。', [evidence(0, 2)]),
        'Ec': (0, '本成员规定疾病及疗效证据条件，未涉及药品价格、治疗费用、支付责任或资源经济影响。', []),
        'I': (0, '本成员的疾病及疗效条件没有要求技术创新或实质改良资格；附条件批准的申请机会未在本成员连接明确创新或改良研发对象，不能由程序推定创新性。', [evidence(0, 2)]),
        'F': (1, '患者所需治疗对应严重危及生命且尚无有效治疗手段的疾病；该明确的有效治疗选项缺口与父条款允许申请附条件批准的机会直接相连，构成按需机会配置。此判断不证明已有药品获批或缺口已消除。', [evidence(0, 2)])
    },
    {
        'S': (0, '当前规定公共卫生急需及疗效数据条件，没有药物损害、风险评价或安全控制内容；不继承同清单疫苗成员的风险条件。', []),
        'E': (1, '当前明确要求药物临床试验已有数据显示疗效并能预测临床价值，是附条件批准申请资格中的效果证据要求。', [evidence(1, 3)]),
        'Ec': (0, '当前急需药品的申请及效果证据条件未规定治疗费用、价格或支付安排。', []),
        'I': (0, '公共卫生急需和疗效证据是本成员的资格内容，没有技术创新、实质改良或以其为对象的研发支持关系，申请附条件批准本身不足以赋I。', [evidence(1, 3)]),
        'F': (0, '公共卫生方面急需与申请机会虽有联系，但本成员未明示无有效治疗选项、境内无获批选项、供药短缺或其他可指认获取障碍；不能继承兄弟成员的无有效治疗手段条件。', [evidence(1, 3)])
    },
    {
        'S': (1, '当前要求申请附条件批准的急需疫苗经评估获益大于风险，直接评价疫苗使用风险与获益的关系，属于安全评价内容。', [evidence(2, 3)]),
        'E': (1, '当前对疫苗作获益大于风险的实质评估要求，其中疫苗防治健康获益是批准资格的组成部分；不将该要求写成某疫苗已证实有效。', [evidence(2, 3)]),
        'Ec': (0, '当前疫苗急需及获益风险条件没有费用、价格、支付或成本与产出的经济关系。', []),
        'I': (0, '当前疫苗的公共卫生用途、急需认定和获益风险条件没有技术新颖性或实质改良资格，也未将创新研发对象与支持安排相连。', [evidence(2, 3)]),
        'F': (0, '突发公共卫生事件急需或卫生部门认定急需不独立说明可指认的治疗保障缺口、获取差异或患者负担关系；本成员不能继承另一成员的无有效治疗选项。', [evidence(2, 3)])
    },
    {
        'S': (1, '当前要求就附条件批准上市的条件进行实质沟通并确认，确认后方提出上市许可申请；已读同版第63条完整条件中，疫苗分支要求经评估获益大于风险，故该操作性条件确认涉及安全评价。只记录该分支，不称全部申请药品都适用疫苗条件。', [inline_standard]),
        'E': (1, '当前沟通并确认的是附条件批准上市的实质条件，而非交流形式；同版第63条条件明确要求疗效数据、临床价值预测或疫苗获益风险评估，故条件确认实质涉及药物效果证据。', [inline_standard]),
        'Ec': (0, '本条要求确认上市条件及继续研究工作后申报，同版完整条件也没有药品价格、治疗费用或支付内容。', [inline_standard]),
        'I': (0, '本条设置的条件沟通及申请前确认没有与技术创新或实质改良研发对象相连；同版第63条条件是疾病、急需、疗效与获益风险内容，不能把一般条件沟通改称创新研发支持。', [inline_standard]),
        'F': (1, '当前以附条件批准上市条件的沟通确认为提出上市许可申请的前置要求；同版第63条第一分支把严重危及生命且无有效治疗手段的明确治疗缺口与该申请机会相连，当前确认适用该按需机会条件。该关系只适用于这一缺口分支，不推广至所有急需药品或疫苗。', [inline_standard])
    },
    {
        'S': (0, '当前以经审评符合要求的药品为对象规定证书记载事项，未在本记录核验药物风险条件或设定安全信息内容；不能从已符合程序要求的对象状态展开安全标签。', []),
        'E': (0, '本条载明的是证书有效期、继续研究工作及完成时限；行政有效期和未指定效果内容的研究记载不构成药物有效性证据要求，亦不从已符合要求的对象状态继承疗效条件。', []),
        'Ec': (0, '当前证书有效期和研究期限的记载未涉及治疗成本、药价、支付责任或标准。', []),
        'I': (0, '当前证书记载事项没有创新或改良资格的制度使用，也没有向明确创新研发对象提供支持；研究工作及期限未表达创新内容。', []),
        'F': (0, '当前规范经审评符合要求药品的证书记载事项，没有本记录的治疗缺口核验、按需机会配置或患者可负担关系；不由附条件批准对象身份复制其全部申请条件。', [])
    },
    {
        'S': (1, '当前以不能满足附条件批准条件为终止该程序的标准，属于操作性标准—待遇撤回关系；同版第63条完整标准中疫苗获益大于风险分支涉及药物风险评价，故记S。此规范不证明某具体药品不安全或全部条件失败。', [asset_standard]),
        'E': (1, '本条把是否满足附条件批准条件用于决定终止程序；有限补读的同版第63条包含临床试验疗效数据、临床价值预测及疫苗获益要求，因此实质使用效果证据标准。不能满足整体条件不等于已证明药物无效。', [asset_standard]),
        'Ec': (0, '当前程序终止及转正常研究申报的后果不涉及药价、药品治疗费用或支付责任，同版条件亦无此经济内容。', [asset_standard]),
        'I': (0, '本条终止的是附条件批准机会，同版条件没有技术创新或实质改良资格；转正常研究申报也未设置创新研发支持，不能因加快程序撤回便自动赋I。', [asset_standard]),
        'F': (1, '当前以是否满足同版条件决定维持或终止附条件批准机会；第63条第一分支将无有效治疗手段的严重疾病缺口与该机会直接相连，故终止规范涉及按需机会的条件限制。这里不推断所有治疗均被撤回，也不宣称已造成不公平。', [asset_standard])
    },
    {
        'S': (1, '当前明确要求附条件批准药品上市后采取相应风险管理措施，直接规定药物风险控制，属于安全性制度安排。', []),
        'E': (0, '当前要求完成药物临床试验等相关研究但没有指定疗效、健康收益或效果终点内容；一般研究要求不能从附条件批准背景继承有效性。', []),
        'Ec': (0, '当前规定上市后风险管理、研究期限和补充申请，没有治疗费用、价格或支付安排。', []),
        'I': (0, '这是持有人上市后的风险管理和完成研究义务，没有明确创新或改良研发支持对象及可用安排，不能从研究或程序身份推成I3。', []),
        'F': (0, '当前药品上市后的管理、研究和申报义务未与治疗保障缺口、获取差异或患者负担能力相连；附条件批准身份本身不足。', [])
    },
    {
        'S': (0, '当前只要求疫苗持有人在期限内完成批准时提出的进一步研究，没有表达药物损害或风险证据内容，也未承接前段风险管理义务。', []),
        'E': (0, '本条进一步研究的完成期限未指定疗效、健康收益或效果证据，不能仅由疫苗用途和研究名称推定E。', []),
        'Ec': (0, '当前研究完成期限与持有人义务没有药品治疗费用、价格或支付内容。', []),
        'I': (0, '当前是批准后完成研究的常规义务，没有创新或实质改良内容，亦未设置向该类研发提供资源、技术反馈或支持机会的关系。', []),
        'F': (0, '当前疫苗持有人的研究期限未连接患者药品获取、持续治疗负担或按需保障缺口；疫苗对象及附条件批准章节名称不足以赋F。', [])
    },
    {
        'S': (1, '当前规定不能证明药品获益大于风险时依法处理直至注销注册证书，风险证据是本记录实质监管后果的一个条件分支，故记S。不能证明不等于已经证实风险更大。', []),
        'E': (1, '本条在不能证明获益大于风险的分支实质要求药物健康获益证据，并以其证明状况连接注册后果，故记E；逾期未完成研究的另一分支不因此都包含效果内容。', []),
        'Ec': (0, '研究逾期或获益风险证明不足与证书注销的关系没有药品治疗资源、费用或支付内容。', []),
        'I': (0, '当前为持有人研究与获益风险证明义务及注册后果，没有创新、实质改良资格或明确创新研发支持关系；注销本身不使I成立。', []),
        'F': (0, '当前处罚条件是研究逾期或获益风险证据不足，没有核验按需申请标准或表达患者获取差异、治疗保障缺口与该后果的关系；不能从已附条件批准身份展开全部原申请条件。', [])
    },
    {
        'S': (1, '当前并非纯清单引导，而是规定所列条件药品可申请优先审评；其中第(五)成员将符合附条件批准作为申请机会条件，同版第63条疫苗获益风险标准据此被操作性使用，故记S。其他成员不继承该标准。', [evidence(9, 9), asset_standard]),
        'E': (1, '当前可申请优先审评的第(五)分支要求符合附条件批准，同版完整标准包含疗效数据、临床价值预测和疫苗获益要求，故这一路径涉及效果证据条件。笼统明显临床价值及治疗用途本身不另作为E依据。', [evidence(9, 9), asset_standard]),
        'Ec': (0, '当前授予所列药品优先审评申请机会，完整成员及有限补核的附条件批准标准没有药价、药费、支付责任或成本产出关系。', []),
        'I': (1, '当前将重大传染病、罕见病等疾病的创新药和改良型新药以及创新疫苗设为可申请优先审评的对象，创新或改良资格与差异化申请机会直接相连，按I4记录其制度使用。不能将儿童剂型、短缺或其他程序身份都解释为技术创新。', [evidence(9, 5), evidence(9, 7)]),
        'F': (1, '当前第(一)分支明确临床急需短缺药品，并以该实际药品保障缺口连接优先审评申请机会，构成按需审评资源配置。该短缺关系不移给全部创新药、儿童药或其他成员，也不证明最终供应改善。', [evidence(9, 5)])
    },
    {
        'S': (0, '当前成员是短缺药品及重大传染病、罕见病创新药和改良型新药的适用条件，没有药物风险内容；疾病属性及短缺不等于药物损害。', []),
        'E': (0, '本成员仅说明防治用途、疾病类型及创新或改良类别，未表达药物疗效或健康获益证据；父条款明显临床价值不能默认等于有效性。', [evidence(10, 2)]),
        'Ec': (0, '当前短缺及创新、改良药的优先审评资格没有治疗费用、价格、支付或经济影响内容。', []),
        'I': (1, '本成员把防治重大传染病、罕见病等疾病的创新药和改良型新药与父条款优先审评申请机会直接相连，是创新或改良资格决定差异化准入待遇的制度使用，按I4纳入。短缺药品分支不因此全部具备创新资格。', [evidence(10, 2)]),
        'F': (1, '本成员明确患者临床急需药品存在短缺，并与父条款允许申请优先审评的针对性机会相连，构成保障缺口—按需资源配置关系。罕见病名称及创新身份本身不作为F充分依据。', [evidence(10, 2)])
    },
    {
        'S': (0, '当前要求儿童药品的新品种、剂型和规格符合儿童生理特征，未表达药物损害、给药差错或风险控制关系；生理适合性不足以推定安全性。', []),
        'E': (0, '当前是儿童适用性和品种、剂型、规格条件，没有防治效果、健康收益或相应证据；父条款明显临床价值不能直接代替E。', [evidence(11, 3)]),
        'Ec': (0, '当前儿童药品适用条件和优先审评申请机会没有治疗费用、价格或支付内容。', []),
        'I': (0, '新品种、剂型和规格以及符合儿童生理特征没有明示技术新颖性、实质改良资格或具体既有使用局限—改进关系；父条款的优先机会也未将本成员对象限定为创新或实质改良研发，故不推定I。', [evidence(11, 3)]),
        'F': (0, '儿童对象及生理适合性没有说明所需药品短缺、无有效选项、获取差异或患者负担联系；优先审评机会不能继承兄弟成员的临床急需短缺条件。', [evidence(11, 3)])
    }
]

records = []
for i, decision in enumerate(decisions):
    dimensions = {}
    for key in ['S', 'E', 'Ec', 'I', 'F']:
        value, reason, context_evidence = decision[key]
        dimensions[key] = {'value': value, 'reason': reason,
                           'evidence': [evidence(i)] + context_evidence}
    binding = a['packets'][i]
    records.append({'source_id': binding['source_id'], 'output_id': binding['output_id'],
                    'packet_sha256': binding['sha256'], 'dimensions': dimensions})

events = []
for start, end in [(0, 6500), (6500, 13000), (13000, 14190)]:
    events.append({'path': str(assignment_path), 'bytes': 14890,
        'sha256': 'a432ee49541aa34715264986501c3e1947394ac54440453b20efe3687985991f',
        'start': start, 'end': end, 'range_kind': 'unicode_code_points',
        'presentation_event': f'present:a432ee49541aa34715264986501c3e1947394ac54440453b20efe3687985991f:{start}:{end}'})
events += [json.loads(line) for line in (slot / 'presentation-events.jsonl').read_text().splitlines()]
files = {}
packet_sources = {binding['path']: [binding['source_id']] for binding in a['packets']}
asset_sources = ['RECODE25-04598', 'RECODE25-04599', 'RECODE25-04600', 'RECODE25-04604']
for event in events:
    path = event['path']
    if path not in files:
        ids = packet_sources.get(path, asset_sources if path == asset['path'] else a['source_ids'])
        files[path] = {key: event[key] for key in ['path', 'bytes', 'sha256']}
        files[path].update({'actual_presented_ranges': [],
            'read_method': 'emit-presentation.py --assignment bound assignment --path bound file --start/--end; literal stdout observed',
            'source_ids': ids, 'not_truncated': True,
            'full_file_read': path != asset['path']})
    files[path]['actual_presented_ranges'].append({
        'range_kind': event['range_kind'],
        'range_basis': 'zero-based Unicode code points; half-open [start,end); actual PRESENTATION stdout without truncation',
        'start': event['start'], 'end': event['end'],
        'presentation_event': event['presentation_event']})

candidate = {
    'artifact_type': 'native_coder_first_structured_whole_batch_submission',
    'run_id': a['run_id'], 'batch_id': a['batch_id'],
    'requested_model': a['requested_model'],
    'requested_reasoning_effort': a['requested_reasoning_effort'],
    'manual_binding': a['manual'], 'execution_prompt_binding': a['execution_prompt'],
    'context_unit': 'batch', 'scope': a['scope'], 'template_only': False,
    'read_manifest': {'artifact_type': 'actual_literal_read_manifest',
        'run_id': a['run_id'], 'batch_id': a['batch_id'], 'context_unit': 'batch',
        'template_only': False, 'actual_read_or_use_claimed': True,
        'files': list(files.values()),
        'limited_asset_use': {
            'path': asset['path'], 'unicode_code_points': [10374, 10720],
            'source_ids': asset_sources,
            'use': '同版第63条完整条件及第64条；04598以packet内同版叶片为证据，04600及04604有限补全操作性标准；04599仅核明后仍按本条证书记载命题判断，不展开已符合要求的对象身份。'
        }},
    'records': records,
    'execution_identity_note': 'Model and reasoning effort are assignment requests; no independent serving-model verification or provider wire-body capture is claimed.'
}
candidate_bytes = (json.dumps(candidate, ensure_ascii=False, indent=2) + '\n').encode('utf8')
with (slot / 'first.candidate.json').open('xb') as stream:
    stream.write(candidate_bytes)
print('Saved first complete whole-batch candidate in own slot; no validator executed.')
