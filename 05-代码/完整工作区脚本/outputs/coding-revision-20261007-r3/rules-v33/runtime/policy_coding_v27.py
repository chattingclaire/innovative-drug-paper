"""CAL-5D v1.3 automatic rules: five-dimension implementation review.

Frozen earlier results remain intact. The inherited v25 module changes only
its completeness gate; each dimension module reviews evidence, then labels
are rebuilt exclusively from current-unit evidence.
"""
import copy
from rule_support import rebuild, DIMENSIONS
import inherited_rules_v25
import rules_se
import rules_ec
import rules_if
import rules_recall_v31
import rules_boundary_v32
import table_material_adapter_v321
import source_context_adapter_v33
import rules_substantive_v33
from context_validation import validate_added_parents

VERSION = 'v33-source-and-substantive-relations-20261007-candidate01'


def code_unit(record, *, source_adapter=True, substantive_rules=True):
    record = source_context_adapter_v33.prepare(record) if source_adapter else record
    validate_added_parents(record)
    table_material_adapter_v321.verified_rows(record)
    result = copy.deepcopy(inherited_rules_v25.code_unit(record))
    result['version'] = VERSION
    result['semantic_protocol'] = 'CAL-5D-20260926-v1.3+operation-v1.4'
    result['status'] = 'development_revision_not_independently_validated'
    if result.get('judgement_status') == 'undetermined':
        return result
    for module in (rules_se, rules_ec, rules_if, rules_recall_v31, rules_boundary_v32, table_material_adapter_v321):
        result = module.revise(record, result)
    if substantive_rules:
        result = rules_substantive_v33.revise(record, result)
    result = rebuild(result)
    result['source_list_repaired'] = bool(record.get('verified_following_list_v27'))
    result['implementation_components_v33'] = {'source_adapter': source_adapter, 'substantive_rules': substantive_rules}
    result['source_context_adaptation_log_v33'] = record.get('source_context_adaptation_log_v33', [])
    original = record['unit_text']
    for evidence in result['evidence']:
        assert original[evidence['start']:evidence['end']] == evidence['text']
        assert evidence['dimension'] in DIMENSIONS
    assert all(type(v) is int and v in (0,1) for v in result['labels'].values())
    return result
