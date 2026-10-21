"""Mechanical reserved267 full-text redaction; never print/serialize protected index.

Use this only to build safe manual-review projections. Model execution inputs and
all original/frozen files must remain unchanged. A protected current-unit ID
must also be excluded before projection, regardless of text matching.
"""
from pathlib import Path
import hashlib, json, unicodedata

ROOT=Path('/PROJECT_ROOT')
EXCLUSION_REL='outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
INPUT_REL='outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl'
EXCLUSION_SHA='a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
INPUT_SHA='6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
MARKER='[预留单元原文已机械遮蔽]'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized_with_offsets(text):
    chars=[];offsets=[]
    for i,ch in enumerate(text):
        for c in unicodedata.normalize('NFKC',ch).casefold():
            if c.isalnum():chars.append(c);offsets.append(i)
    return ''.join(chars),offsets
def normalized(text):return normalized_with_offsets(text)[0]

class ReservedContextRedactor:
    def __init__(self,root=ROOT):
        root=Path(root);self.exclusion_path=root/EXCLUSION_REL;self.input_path=root/INPUT_REL
        assert sha(self.exclusion_path)==EXCLUSION_SHA
        assert sha(self.input_path)==INPUT_SHA
        exclusion=json.loads(self.exclusion_path.read_text())
        self.reserved_ids=set(exclusion['all_registered_members_of_reserved_families_unit_ids'])
        assert len(self.reserved_ids)==267
        self._index=[];seen=set()
        with self.input_path.open() as stream:
            for line in stream:
                row=json.loads(line)
                if row['id'] not in self.reserved_ids:continue
                norm=normalized(row['text']);assert norm
                self._index.append((row['id'],norm));seen.add(row['id'])
        assert seen==self.reserved_ids
    def is_reserved(self,unit_id):return unit_id in self.reserved_ids
    def manifest(self):
        return {'reserved_member_n':267,'normalization':'per-characterNFKC+casefold+alphanumeric; original character offsets retained','index_material':'In-memory only; do not print or serialize _index.','exclusion_path':str(self.exclusion_path),'exclusion_sha256':EXCLUSION_SHA,'input_path':str(self.input_path),'input_sha256':INPUT_SHA,'only_full_normalized_unit_matches':True,'does_not_detect_arbitrary_partial_paraphrase':True}
    def redact_text(self,text,locator=''):
        norm,offsets=normalized_with_offsets(text);spans=[];hits=[]
        for unit_id,protected in self._index:
            start=0
            while True:
                at=norm.find(protected,start)
                if at<0:break
                end=at+len(protected);begin_orig=offsets[at];end_orig=offsets[end-1]+1
                spans.append((begin_orig,end_orig))
                hits.append({'locator':locator,'reserved_unit_id':unit_id,'context_sha256':hashlib.sha256(text.encode()).hexdigest(),'matched_original_span_sha256':hashlib.sha256(text[begin_orig:end_orig].encode()).hexdigest(),'normalized_match_length':len(protected)})
                start=at+1
        merged=[]
        for begin,end in sorted(spans):
            if merged and begin<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],end)
            else:merged.append([begin,end])
        for begin,end in reversed(merged):text=text[:begin]+MARKER+text[end:]
        return text,hits
    def redact_object(self,obj,locator='root'):
        hits=[]
        if isinstance(obj,str):return self.redact_text(obj,locator)
        if isinstance(obj,list):
            result=[]
            for i,v in enumerate(obj):
                vv,hh=self.redact_object(v,f'{locator}[{i}]');result.append(vv);hits+=hh
            return result,hits
        if isinstance(obj,dict):
            result={}
            for k,v in obj.items():
                vv,hh=self.redact_object(v,f'{locator}.{k}');result[k]=vv;hits+=hh
            return result,hits
        return obj,hits
    def audit_object_no_full_match(self,obj):
        _,hits=self.redact_object(obj)
        return {'no_remaining_full_normalized_reserved_unit_match':not hits,'hit_metadata':hits}

def selftest_without_models():
    # Synthetic patterns only; never expose a real reserved string.
    obj=ReservedContextRedactor.__new__(ReservedContextRedactor)
    obj.reserved_ids={'TEST-1','TEST-2'};obj._index=[('TEST-1',normalized('甲Ａ乙丙')),('TEST-2',normalized('乙丙丁'))]
    out,hits=obj.redact_text('前：甲 A\n乙，丙丁。后')
    assert out=='前：'+MARKER+'。后' and {h['reserved_unit_id'] for h in hits}=={'TEST-1','TEST-2'}
    source={'a':'独立文本','b':['甲Ａ乙丙',{'c':'乙丙丁'}]};red,hits=obj.redact_object(source)
    assert source['b'][0]=='甲Ａ乙丙' and red['b'][0]==MARKER and red['b'][1]['c']==MARKER
    assert obj.audit_object_no_full_match(red)['no_remaining_full_normalized_reserved_unit_match']
    return {'synthetic_overlap_andNFKC_and_space_punctuation_and_immutable_nested_object':'PASS','model_calls':0}
