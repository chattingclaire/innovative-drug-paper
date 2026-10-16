"""Actual current resource/feedback/convenience relationships for I3.

A technical task or advice verb is insufficient. This helper identifies only
an independent support arrangement; callers authenticate its innovative R&D
recipient. It records mentions, including withdrawal, without claiming that
support currently exists.
"""
import re

_TITLE = re.compile(r'《[^》\n]*》')
_CARRIER = re.compile(r'文件名|栏目名称|字样|字符串|排版|上传格式|填写格式|模板')
_DUTY = re.compile(r'(?:提交|上报|报告|报送|更新)[^。；;]{0,25}(?:安全性报告|不良反应|药物警戒)|设施|场地|设备租赁|检测服务|诊疗服务')
_ARRANGE = re.compile(r'(?:不再|不予|停止|取消)?(?:提供|给予|安排|配置|设立|建立|开展|取消|停止)')
_SUPPORT = re.compile(r'(?:专门|专项|专属|个性化)?(?:科学|技术|研发)(?:指导|服务|建议|支持)|研究方案建议|方案反馈|研发资源|研发平台|研发资金|资金支持')
_PROVIDER = re.compile(r'药审中心|药品审评中心|药品(?:技术)?审评机构|监管部门|审评人员|审评团队')
_FEEDBACK = re.compile(r'(?:提出|反馈|给出)(?:具体)?(?:科学|技术|研发|研究方案)(?:建议|意见)|(?:研究|试验)方案[^。；;]{0,15}(?:反馈|技术建议)')
_CONVENIENCE = re.compile(r'(?:允许|可以|可|准予)[^。；;]{0,12}(?:免于|豁免|减免|简化)[^。；;]{0,25}(?:研发|研究|试验|审评)(?:要求|程序|资料|步骤)?')


def current_support_relations(text):
    masked = _TITLE.sub(lambda m:' '*len(m.group()),text)
    out=[]
    for part in re.finditer(r'[^。；;\n]+',masked):
        value=part.group()
        if _CARRIER.search(value) or _DUTY.search(value): continue
        def anchor(m,role):
            a,b=part.start()+m.start(),part.start()+m.end()
            return dict(start=a,end=b,text=text[a:b],role=role)
        for action in _ARRANGE.finditer(value):
            # The resource is governed by this arrangement, not another
            # following proposition or a preceding ordinary requirement.
            support=_SUPPORT.search(value,action.end())
            if support and support.start()-action.end()<=30 and not re.search(r'[，,]|(?:提交|报告|上报)',value[action.end():support.start()]) and not re.match(r'(?:材料|资料|文件|记录)',value[support.end():]):
                out.append([anchor(action,'current_support_arrangement_mentioned'),
                    anchor(support,'specific_research_support_resource')])
        provider=_PROVIDER.search(value)
        feedback=_FEEDBACK.search(value)
        if provider and feedback and provider.start()<feedback.start():
            out.append([anchor(provider,'actual_technical_support_provider'),
                anchor(feedback,'specific_protocol_feedback_arrangement')])
        for convenience in _CONVENIENCE.finditer(value):
            out.append([anchor(convenience,'specific_research_convenience_arrangement')])
    return out
