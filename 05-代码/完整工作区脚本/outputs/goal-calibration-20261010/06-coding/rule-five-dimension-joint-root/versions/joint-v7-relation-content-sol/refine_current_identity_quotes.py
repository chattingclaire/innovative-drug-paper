from pathlib import Path
P=Path(__file__).resolve().parent;p=P/'relations.py';s=p.read_text()
start=s.index("        receipt = completion.get('neutral_scope_receipt')",s.index('    def _operative_value_definition'))
needle="            self._add('cited_standard', receipt['content_evidence'] + proof_only, '当前申请的实质临床优势条件"
index=s.index(needle,start)
new="""            content = [q for q in receipt['content_evidence'] if not any(q.get('context_id') == only.get('context_id') and q['start'] < only['end'] and only['start'] < q['end'] for only in proof_only)]
            # The current criterion is already classified as current text; its
            # duplicate source quote proves identity and is never donor content.
            proof = dict(proof, current_identity_overlap_excluded_from_donor_content=True, consumed_content_quotes=content)
"""
s=s[:index]+new+s[index:];s=s.replace(needle,"            self._add('cited_standard', content + proof_only, '当前申请的实质临床优势条件",1);p.write_text(s)
