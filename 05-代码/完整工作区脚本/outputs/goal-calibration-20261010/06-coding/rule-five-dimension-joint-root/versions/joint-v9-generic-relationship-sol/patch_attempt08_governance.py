from pathlib import Path
P=Path(__file__).resolve().parent;q=P/'relations.py';s=q.read_text();cut=s.index('    def _v9_emit(');prefix,body=s[:cut],s[cut:]
body=body.replace('self._current_source()', 'self._v9_current_context()')
body=body.replace("        if not pok or not cok or not pid or not cid or current['source_ref']['sha256']!=primary:return None", "        if not pok or not cok or not pid or not cid or current['source_ref']['sha256']!=primary or not self._se_same_geometry(parent,current):return None")
body=body.replace("matches=[c for c,(p,_) in zip(members[1:],mp[1:]) if p==cid and self.norm in norm(c['text'])]", "matches=[c for c,(p,_) in zip(members[1:],mp[1:]) if p==cid and norm(c['text'])==norm(current.get('text','')) and norm(c['text']).count(self.norm)==1]")
body=body.replace("            if len(matches)!=1:continue\n            lines=", "            if len(matches)!=1:continue\n            declared_current_lines,current_lines_ok=self._se_geometry_value(current,'source_lines')\n            declared_member_lines,member_lines_ok=self._se_geometry_value(matches[0],'source_lines')\n            if not current_lines_ok or not member_lines_ok or (declared_current_lines is not None and declared_member_lines is not None and declared_current_lines!=declared_member_lines):continue\n            lines=")
body=body.replace("                st=boundary.get('structure',{})\n                if st.get('parent_context_id')!=group['context_id'] or st.get('first_paragraph')!=pid or st.get('last_paragraph')!=mp[-1][0]:continue", "                st=boundary.get('structure',{})\n                if self._se_geometry_value(boundary,'parent_context_id')!=(group['context_id'],True) or self._se_geometry_value(boundary,'first_paragraph')!=(pid,True) or self._se_geometry_value(boundary,'last_paragraph')!=(mp[-1][0],True):continue\n                child_groups,child_groups_ok=self._se_geometry_value(boundary,'child_groups')\n                if not child_groups_ok or not isinstance(child_groups,list):continue")
body=body.replace("next_ids=[i for g in st.get('child_groups',[])", "next_ids=[i for g in child_groups")
body+='''
    def _v9_current_context(self):
        # Geometry and complete original paragraph identity must be unique;
        # duplicate representations of exactly one paragraph are collapsed.
        rows={}
        for c in self._se_current_geometry_contexts():
            text=norm(c.get('text',''))
            if not self.norm or text.count(self.norm)!=1:continue
            pid,ok=self._se_geometry_value(c,'paragraph_id');component,ok2=self._se_geometry_value(c,'component_id')
            if not ok or not ok2:continue
            key=(c['source_ref']['sha256'],pid,component,text)
            rows.setdefault(key,c)
        return next(iter(rows.values())) if len(rows)==1 else None
'''
q.write_text(prefix+body)
