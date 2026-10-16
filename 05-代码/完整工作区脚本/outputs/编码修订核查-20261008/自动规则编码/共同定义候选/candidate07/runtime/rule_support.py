"""Shared traceable utilities for the five-dimension rule review.

Matching operates on a normalized, title-masked view; evidence always points
back to the supplied original. These helpers do not decide any dimension.
"""
import hashlib
import re
# All runtime dependencies are frozen beside this module in rules-v31.
import baseline_candidate17 as baseline
import policy_coding_v25 as v25

DIMENSIONS = ('S','E','Ec','I','F')

class RuleView:
    def __init__(self, record, result):
        self.record=record
        self.result=result
        self.original=record['unit_text']
        normalized,self.offsets=baseline.matching_view(self.original)
        self.text=v25._without_titles(normalized)
        self.normalized=normalized
        self.drug_scope=bool(v25.DRUG.search(self.text) or result.get('drug_object_evidence'))

    def sentences(self):
        return re.finditer(r'[^。；;]+',self.text)

    def clauses(self):
        return re.finditer(r'[^。；;，,]+',self.text)

    def raw_span(self,start,end):
        assert 0<=start<end<=len(self.text)
        return self.offsets[start][0],self.offsets[end-1][1]

    def add(self,rule,dimension,start,end,subtype=None,basis='',dependency=None,safety_basis=None):
        assert dimension in DIMENSIONS and basis
        a,b=self.raw_span(start,end)
        e={'rule':rule,'dimension':dimension,'start':a,'end':b,'text':self.original[a:b],
           'matching_text':self.text[start:end],'subtype':subtype,
           'protocol_basis':basis,'rule_release':'v27-five-dimension-review'}
        if dependency:e['context_dependency']=dependency
        if safety_basis:e['safety_basis']=safety_basis
        if not any(x.get('rule')==rule and x.get('dimension')==dimension and x.get('start')==a and x.get('end')==b for x in self.result['evidence']):
            self.result['evidence'].append(e)
        return e

    def drop(self,predicate,rule,reason):
        removed=[e for e in self.result['evidence'] if predicate(e)]
        self.result['evidence']=[e for e in self.result['evidence'] if not predicate(e)]
        for e in removed:
            self.result.setdefault('suppressions',[]).append({
                'rule':rule,'dimensions':[e['dimension']],'start':e['start'],'end':e['end'],
                'text':e['text'],'suppressed_rule':e['rule'],'reason':reason})
        return removed

    def drop_within(self,dimension,start,end,rule,reason):
        a,b=self.raw_span(start,end)
        return self.drop(lambda e:e['dimension']==dimension and a<=e['start'] and e['end']<=b,rule,reason)

    def paragraph_prefixes(self):
        for p in self.record.get('paragraph_context',[]):
            full=baseline.matching_view(p['text'])[0]
            if full.count(self.normalized)==1:
                yield p,full.split(self.normalized,1)[0]

    def dependency(self,p,kind,antecedent):
        return {'kind':kind,'paragraph_id':p.get('paragraph_id'),
                'source_sha256':self.record.get('unit_source_sha256') or self.record.get('source_sha256'),
                'paragraph_sha256':hashlib.sha256(p['text'].encode()).hexdigest(),
                'antecedent_text':antecedent,'pages':p.get('pages',[])}

def rebuild(result):
    if result.get('judgement_status')=='undetermined':return result
    result['labels']={d:int(any(e['dimension']==d for e in result['evidence'])) for d in DIMENSIONS}
    for dim,key in [('F','fairness_subtypes'),('I','innovation_subtypes')]:
        result[key]=sorted({e['subtype'] for e in result['evidence'] if e['dimension']==dim and e.get('subtype')})
    result['innovation_unclassified_evidence']=[e for e in result['evidence'] if e['dimension']=='I' and not e.get('subtype')]
    result['innovation_subtype_status']=('needs_review' if result['innovation_unclassified_evidence'] else 'complete' if result['labels']['I'] else 'not_applicable')
    result['safety_subtypes']=sorted({e.get('safety_basis','quality_safety' if e['rule']=='S07' else 'other_safety') for e in result['evidence'] if e['dimension']=='S'})
    q=result['safety_subtypes']
    result['safety_quality_basis']='quality_only' if q==['quality_safety'] else 'quality_and_other' if 'quality_safety' in q else 'no_quality_basis'
    return result
