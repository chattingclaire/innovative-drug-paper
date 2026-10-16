"""Original v3 record guards through the explicit v4 scope adapter; no new selection rules."""
import necessary_read_gate as gate
if gate.BINDING is None: raise ValueError('configure gate before importing native_records')
_base = gate._load('base_native_records','_formal_inherited_v3_native_records')
_base.check_scope = gate.check_scope
_blank_v3 = _base.blank_ledger
def blank_ledger():
    ledger = _blank_v3()
    ledger['protocol_version'] = 'native-necessary-read-prospective-4'
    ledger['receipt_scope_schema_version'] = 'native-necessary-read-v3'
    ledger['gate_binding_sha256'] = gate._pb.file_sha(gate.BINDING_PATH)
    ledger['inherited_development77_inputs_unchanged'] = True
    return ledger
for _name in ['TELEMETRY_KEYS','check_telemetry','check_saved_scopes','select_technical_receipts','all_batches_sealed_gate']:
    globals()[_name] = getattr(_base,_name)
