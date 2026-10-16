"""CAL-5D v1.3 automatic rules: five-dimension implementation review.

Frozen earlier results remain intact. The inherited v25 module changes only
its completeness gate; each dimension module reviews evidence, then labels
are rebuilt exclusively from current-unit evidence.
"""
import copy
import common_definition_stage
import common_definition_delta06
import common_scope09
import common_coverage_relations11
import common_cited_list_conditions12
import common_innovation_relations14
import common_medicine_access14
from proposition_negation import normalize_evidence_expressions
from current_unit_role import classify as classify_current_unit
from rule_support import rebuild, DIMENSIONS
import inherited_rules_v25
import rules_se
import rules_ec
import rules_if
import rules_recall_v31
import rules_boundary_v32
import table_material_adapter_v321
import source_context_adapter_v34
import material_completeness_v34
import referenced_relations_v34
import rules_substantive_v33
import rules_semantic_v35
import rules_semantic_v36
import rules_bounded_v36_2
import rules_repair_v37
import rules_supply_membership_v38
import rules_current_relations_v39
from context_validation import validate_added_parents

VERSION = 'substantive-evaluation-support-repair-03'
CURRENT_MANUAL_SHA256 = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
CURRENT_PROTOCOL = 'UNIFIED-5D-MEASUREMENT-SEMANTIC-20261009'


def code_unit(record, *, source_adapter=True, substantive_rules=True):
    record = source_context_adapter_v34.prepare(record) if source_adapter else record
    record = material_completeness_v34.prepare(record)
    record = rules_current_relations_v39.prepare(record)
    validate_added_parents(record)
    table_material_adapter_v321.verified_rows(record)
    result = copy.deepcopy(inherited_rules_v25.code_unit(record))
    result['version'] = VERSION
    result['semantic_protocol'] = CURRENT_PROTOCOL
    result['current_manual_sha256'] = CURRENT_MANUAL_SHA256
    result['implementation_identity'] = VERSION
    role = classify_current_unit(record['unit_text'])
    result['current_unit_role'] = role
    result['status'] = 'common_definition_development_candidate_not_adopted'
    if result.get('judgement_status') == 'undetermined':
        result['typed_contexts_v34'] = record.get('typed_contexts_v34', [])
        result['source_field_consumption_v34'] = record.get('source_field_consumption_v34', [])
        result['completeness_gate_v34'] = record.get('completeness_gate_v34')
        result['current_reference_gate_v39'] = record.get('current_reference_gate_v39')
        return result
    if role['role'] == 'structural_reference_only':
        # Whole-unit structural role is resolved before every dimension/list
        # entry. The inherited missing-material gate above remains authoritative.
        if source_adapter:
            source_context_adapter_v34.authenticate_target(record)
        result['evidence'] = []
        result['current_unit_role']['semantic_action'] = 'retain_source_record_without_member_dimension_aggregation'
        result['typed_contexts_v34'] = record.get('typed_contexts_v34', [])
        result['source_field_consumption_v34'] = record.get('source_field_consumption_v34', [])
        result['completeness_gate_v34'] = record.get('completeness_gate_v34')
        return rebuild(result)
    for module in (rules_se, rules_ec, rules_if, rules_recall_v31, rules_boundary_v32, table_material_adapter_v321):
        result = module.revise(record, result)
    if substantive_rules:
        result = rules_substantive_v33.revise(record, result)
    result = referenced_relations_v34.revise(record,result)
    result = rules_semantic_v35.revise(record,result)
    result = rules_semantic_v36.revise(record,result)
    result = rules_bounded_v36_2.revise(record,result)
    result = rules_repair_v37.revise(record,result)
    result = rules_supply_membership_v38.revise(record,result)
    result = rules_current_relations_v39.revise(record,result)
    result = common_definition_stage.revise(record, result)
    result = common_definition_delta06.revise(record, result)
    result = common_coverage_relations11.revise(record, result)
    result = common_scope09.revise(record, result)
    result = common_cited_list_conditions12.revise(record, result)
    result = common_innovation_relations14.revise(record, result)
    result = common_medicine_access14.revise(record, result)
    result = common_scope09.revise(record, result)
    result = normalize_evidence_expressions(record, result)
    result['implementation_scope_note'] = (
        '按统一操作判据替换局部关系候选、确指入口及相关家族责任；'
        '按药物对象、当前障碍/指导谓词及明确关系补有界实现；一般提速不赋公平。必要对象绑定实际来源，当前动作独立留痕。仅开发候选，未作独立效度验证。')
    result = rebuild(result)
    pending = {}
    for field in ('common11_pending_dimensions', 'common14_pending_dimensions'):
        for dimension, reasons in (result.get(field) or {}).items():
            pending.setdefault(dimension, []).extend(copy.deepcopy(reasons))
    if pending:
        result['partial_rule_labels_before_scope_resolution'] = dict(result['labels'])
        result['labels'] = {d: None if d in pending else value for d,value in result['labels'].items()}
        result['judgement_status'] = 'undetermined'
        result['input_assessment_status'] = 'necessary_current_source_relation_unresolved'
    result['source_list_repaired'] = bool(record.get('verified_following_list_v27') or record.get('verified_complete_following_list_v34') or record.get('complete_following_list_v11'))
    result['typed_contexts_v34'] = record.get('typed_contexts_v34', [])
    result['source_field_consumption_v34'] = record.get('source_field_consumption_v34', [])
    result['implementation_components_v33'] = {'source_adapter': source_adapter, 'substantive_rules': substantive_rules}
    result['source_context_adaptation_log_v33'] = record.get('source_context_adaptation_log_v33', [])
    original = record['unit_text']
    for evidence in result['evidence']:
        assert original[evidence['start']:evidence['end']] == evidence['text']
        assert evidence['dimension'] in DIMENSIONS
    assert all((type(v) is int and v in (0,1)) or (d in pending and v is None)
               for d,v in result['labels'].items())
    return result
