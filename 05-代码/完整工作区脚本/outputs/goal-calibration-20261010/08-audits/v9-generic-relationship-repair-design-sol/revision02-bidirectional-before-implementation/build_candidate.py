from pathlib import Path
import json
R=Path(__file__).resolve().parents[3];O=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol';V=O.parent/'joint-v8-target-product-gap-sol'
entry=json.loads((Path(__file__).parent/'impact-contract-before-edit.json').read_text())['entry_regex']
for n in ['evidence','source_packet','source_receipts','relations','dimensions']:
 p=O/(n+'.py');assert not p.exists();p.write_bytes((V/(n+'.py')).read_bytes())
for name in ['relations','dimensions']:
 p=O/(name+'.py');s=p.read_text();at=s.index('\nclass SourceDependencyStop' if name=='relations' else '\nclass MaterialRequestRoutingError')
 s=s[:at]+"\nV9_REPAIR_ENTRY = "+repr(entry)+"\n\ndef _v9_repair_gate(text):\n    return bool(re.search(V9_REPAIR_ENTRY, text))\n"+s[at:]
 if name=='relations':
  target="        self.source_scope_review = {'status': 'complete', 'source_evidence_note': '原CTX文字与结构逐字段读取；完整来源对象的结构、文字及身份已解析。仅当前确指、完整组或同版具名关系使用选定原文；图片未读取，全文不自动适用。'}"
  assert s.count(target)==1;s=s.replace(target,target+'\n        if _v9_repair_gate(self.norm):\n            self._v9_bounded_relationships()')
  s+='\n'+(Path(__file__).parent/'relations-extension.txt').read_text()
 else:
  target='    decisions = acc.finish()';assert s.count(target)==1;s=s.replace(target,'    if _v9_repair_gate(view.norm):\n        _v9_IF_consume(acc, view)\n'+target)
  s+='\n'+(Path(__file__).parent/'dimensions-extension.txt').read_text()
 p.write_text(s)
