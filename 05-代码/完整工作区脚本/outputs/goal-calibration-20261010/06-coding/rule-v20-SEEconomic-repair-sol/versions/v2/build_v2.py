"""Reproducible isolated v2 build from sealed v1 and explicit SE patches."""
from pathlib import Path
P=Path(__file__).resolve().parent;V1=P.parents[1]
d=(V1/'dimensions.py').read_text();d=d[:d.index('# S/E/Ec candidate predicates.')]+(P/'se_predicates.inc').read_text()+'\n\n'+d[d.index('def judge(view)'):]
d=d.replace('for ctx in contexts:\n                        content = _norm(_literal(ctx))','for ctx in contexts:\n                        if ctx.get("context_id") in {q["context_id"] for q in details.get("closure_proof", {}).get("boundary_quotes", [])}:\n                            continue\n                        content = _norm(_literal(ctx))')
d=d.replace('Unit(content[left:right], a + start, a + end, [ctx], kind, details, operative)','Unit(content[left:right], a + start, a + end, contexts if details.get("SE_scope_verified") else [ctx], kind, details, operative)')
d=d.replace('        consumers = unit.details.get("affected_dimensions")\n        if consumers is None or "I" in consumers:', '        consumers = set(unit.details.get("affected_dimensions", DIMENSIONS))\n        if unit.details.get("only_IF_consumers"):\n            consumers &= {"I", "F"}\n        if "I" in consumers:').replace('        if consumers is None or "F" in consumers:','        if "F" in consumers:')
(P/'dimensions.py').write_text(d)
r=(V1/'relations.py').read_text();r=r[:r.index('    def _se_bounded_content(')]+(P/'se_relations.inc').read_text()
r=r.replace("signature = (kind, tuple((e['text'], e['source_ref'].get('sha256')) for e in evidence))", "signature = (kind, tuple((e['context_id'], e['start'], e['end'], e['text'], e['source_ref'].get('sha256')) for e in evidence), details.get('relation_subtype'), tuple(sorted(details.get('affected_dimensions', ['S','E','Ec','I','F']))), bool(details.get('only_IF_consumers')), details.get('norm_start'), details.get('norm_end'), details.get('shared_predicate'))")
r=r.replace('        self._se_bounded_content()', '        self._se_bounded_content()\n        self._se_direct_content_parents()\n        self._se_complete_lists()')
(P/'relations.py').write_text(r)
