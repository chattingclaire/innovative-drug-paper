"""Three authorized semantic relations; no fixture names or source identities."""
from pathlib import Path
P=Path(__file__).resolve().parent
r=P/'relations.py';text=r.read_text()
old="            names=[name for name in names if name in self.norm]\n            if len(set(names))!=1:"
new="""            explicit_names=[name for name in names if name in self.norm]
            if explicit_names:
                names=explicit_names
            elif not re.search('(?:本|该)(?:计划|程序|通道)',self.norm):
                names=[]
            # A local anaphor can bind only the one fully closed programme in
            # this actual current component, never a title elsewhere.
            if len(set(names))!=1:"""
assert old in text;text=text.replace(old,new)
old="(?:本|该)(?:计划|程序|通道)(?:仅)?(?:面向|适用于)|适用(?:对象|范围)[^。；;]{0,20}(?:为|是|包括)"
new="(?:本|该)(?:计划|程序|通道)(?:仅)?(?:面向|适用于)|(?:本|该)(?:计划|程序|通道)(?:的)?(?:支持)?(?:对象|适用对象|支持目标|适用范围)(?:为|是|包括)|适用(?:对象|范围)[^。；;]{0,20}(?:为|是|包括)"
assert old in text;text=text.replace(old,new)
old="'开放|提供|实施|可(?:以)?获得|允许[^。；;]{0,10}使用|不再提供|撤回|终止', self.norm)"
new="'开放|提供|实施|可(?:以)?(?:获得|预约)|允许[^。；;]{0,10}使用|不再提供|撤回|终止', self.norm)"
assert old in text;text=text.replace(old,new)
r.write_text(text)

d=P/'dimensions.py';text=d.read_text()
pos=text.index('def _innovation(acc: Accumulator, unit: Unit, obj: dict):')
text=text[:pos]+'''def _same_current_RND_comparative_support(view, unit: Unit):
    """One immediate current antecedent + explicit anaphor and comparison.

    Only the semicolon-separated continuation of the same proposition can
    bind; different objects, ordinary common deadlines and source siblings
    cannot donate an innovation support beneficiary.
    """
    if unit.kind!='current' or not re.match('(?:本条(?:将)?)?(?:其|该(?:项目|药品|通道)|上述(?:项目|通道))',unit.text):
        return None
    prefix=view.norm[:unit.a]
    previous=re.search('[^。；;]+(?=[；;]$)',prefix)
    if previous is None:
        return None
    antecedent=previous.group()
    objects=list(re.finditer('(?:'+INNOVATION_OBJECT+')[^。；;，,]{0,15}?(?:研发|研制)(?:项目|工作|活动)?',antecedent))
    if len(objects)!=1 or re.search('其他(?:药品|药物|项目)|另一(?:个|种)?(?:药品|药物|项目)',antecedent+unit.text):
        return None
    available=re.search('(?:可(?:以)?申请|开放|设置|提供)[^。；;]{0,20}专(?:门|用)[^。；;]{0,12}(?:通道|程序|审评)',antecedent)
    convenience=re.search('(?:审评|审批)(?:时限|期限)[^。；;]{0,45}(?:缩短|减少)|(?:缩短|减少)[^。；;]{0,15}(?:审评|审批)(?:时限|期限)',unit.text)
    baseline=re.search('(?:相较|相比|相对|比较|较)[^。；;]{0,30}(?:普通|常规|一般)(?:程序|审评|审批)',unit.text)
    if not available or not convenience or not baseline:
        return None
    obj=objects[0]
    return {'object':obj.group(),'arrangement':convenience.group(),'operation':'同一当前命题的明确相对审评时限安排',
            'connection':'one immediate same-current innovation RND beneficiary, actual special-channel opportunity, explicit anaphor and ordinary baseline',
            'numeric_deadline_alone_not_sufficient':True,'object_current_anchor':view.current_anchor(previous.start()+obj.start(),previous.start()+obj.end()),
            'available_current_anchor':view.current_anchor(previous.start()+available.start(),previous.start()+available.end()),'not_claiming_shortening_already_achieved':True}

''' +text[pos:]
old="    direct_support = _current_RND_support(unit)\n    if direct_support:"
new="    direct_support = _current_RND_support(unit) or _same_current_RND_comparative_support(acc.view,unit)\n    if direct_support:"
assert old in text;text=text.replace(old,new)
old="'numeric_deadline_alone_not_sufficient': True})\n    if unit.kind != 'named_mechanism':"
new="'numeric_deadline_alone_not_sufficient': True, **({'same_current_support_roles':direct_support} if direct_support.get('object_current_anchor') else {})})\n    if unit.kind != 'named_mechanism':"
assert old in text;text=text.replace(old,new)
# Preserve the existing patient -> concrete inability -> required treatment
# relation, adding equivalent actual-getting verbs rather than any keyword label.
old="(?:无法|不能|难以|未能)(?:持续|及时)?(?:获得|取得|获取)[^。；;]{0,12}(?:所需|必要)(?:药品|药物|治疗)"
new="(?:无法|不能|难以|未能)(?:持续|及时)?(?:获得|取得|获取|得到|接受)[^。；;]{0,12}(?:所需|必要)(?:药品|药物|治疗)"
assert old in text;text=text.replace(old,new)
d.write_text(text)
print('Three generic semantic gaps patched in own candidate; fixed controls unchanged.')
