"""Finite necessary-view receipt checks. No lookup, coding, or reading inference."""
import importlib.util
from pathlib import Path
from packet_builder import BUNDLE_KEYS, InputFailure, canonical, file_sha, parse, require, sha, valid_sha, seal_members

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ('S', 'E', 'Ec', 'I', 'F')
READ_STATUSES = ('complete', 'partial', 'truncated', 'failed', 'not_delivered')


def uniform_protocol_sha():
    binding = parse((ROOT / 'parent-binding.json').read_bytes())['uniform_protocol']
    require(file_sha(binding['path']) == binding['sha256'] and
            file_sha(ROOT / 'source-reading-protocol-v12.json') == binding['sha256'], 'sealed uniform reading protocol changed')
    return binding['sha256']


def pointer_value(bundle, pointer):
    require(isinstance(pointer, str) and pointer.startswith('/'), 'original bundle pointer required')
    value = bundle
    for part in pointer[1:].split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            require(part.isdigit() and (part == '0' or not part.startswith('0')) and int(part) < len(value), 'pointer array index invalid')
            value = value[int(part)]
        elif isinstance(value, dict):
            require(part in value, 'pointer field missing')
            value = value[part]
        else:
            raise InputFailure('pointer descends through scalar')
    return value


def source_basis(bundle, basis):
    require(set(basis) == {'note', 'bundle_pointers'}, 'source basis fields missing/extra')
    require(isinstance(basis['note'], str) and basis['note'].strip(), 'source structure note missing')
    require(isinstance(basis['bundle_pointers'], list) and basis['bundle_pointers'], 'source evidence anchors missing')
    for pointer in basis['bundle_pointers']:
        pointer_value(bundle, pointer)


def owner_inventory(bundle):
    """Import only the sealed pure inventory helper, never owner.lookup."""
    binding = parse((ROOT / 'parent-binding.json').read_bytes())
    owner = binding['owner_seal']
    require(file_sha(owner['path']) == owner['sha256'], 'owner seal changed')
    members = seal_members(parse(Path(owner['path']).read_bytes()))
    entry = binding['owner_inventory_module']
    path = str(Path(entry['path']).resolve())
    require(members.get(path) == entry['sha256'] and file_sha(path) == entry['sha256'], 'owner inventory not sealed')
    spec = importlib.util.spec_from_file_location('v2_sealed_inventory_only', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.source_inventory(bundle)


def packet_identity(packet):
    require(set(BUNDLE_KEYS) <= set(packet['source_bundle']) and set(packet['source_bundle']) <= set(BUNDLE_KEYS) | {'source_bundle_extension'}, 'complete ten-key source bundle required')
    require(sha(canonical(packet['source_bundle'])) == packet['source_bundle_sha256'], 'full source bundle SHA mismatch')
    require(packet['source_bundle']['source_record']['id'] == packet['source_id'], 'original source ID mismatch')
    require(packet['output_id'] == 'B-' + packet['source_id'].split('-')[1], 'output ID mismatch')


def view_key(obj):
    return (obj['resource_id'], obj['view'], obj.get('scope_pointer'))


def inventory_views(inventory):
    result = {}
    for entry in inventory:
        require(valid_sha(entry['source_sha256']), 'inventory source SHA missing')
        for view, digest in entry['available_views'].items():
            require(valid_sha(digest), 'inventory view SHA missing')
            item = {'resource_id': entry['resource_id'], 'source_sha256': entry['source_sha256'],
                    'view': view, 'view_sha256': digest, 'scope_pointer': None, 'locator': entry['locator']}
            key = view_key(item)
            require(key not in result or result[key] == item, 'conflicting inventory view identity')
            result[key] = item
    return result


def validate_added_view(bundle, view):
    require(set(view) == {'resource_id', 'source_sha256', 'view', 'view_sha256', 'scope_pointer', 'locator', 'encoding'}, 'additional original subview fields missing/extra')
    require(view['view'] in ['text', 'geometry', 'document_bundle', 'image'], 'unsupported original subview')
    pointer = view['scope_pointer']; value = pointer_value(bundle, pointer)
    ancestors = []
    while pointer:
        v = pointer_value(bundle, pointer)
        if isinstance(v, dict):
            ancestors.append(v)
        pointer = pointer.rsplit('/', 1)[0]
    ids = {v[k] for v in ancestors for k in ['source_resource_id', 'context_id', 'region_id', 'attachment_id'] if isinstance(v.get(k), str)}
    require(view['resource_id'] in ids, 'subview is not bound to its original resource ID')
    identity = next(v for v in ancestors if view['resource_id'] in [v.get(k) for k in ['source_resource_id', 'context_id', 'region_id', 'attachment_id']])
    source_hashes = {identity[k] for k in ['source_sha256', 'snapshot_sha256', 'source_pdf_sha256'] if valid_sha(identity.get(k))}
    if isinstance(identity.get('source_ref'), dict) and valid_sha(identity['source_ref'].get('sha256')):
        source_hashes.add(identity['source_ref']['sha256'])
    require(view['source_sha256'] in source_hashes, 'subview source SHA has no explicit original binding')
    if view['encoding'] == 'utf8_text':
        require(isinstance(value, str) and view['view'] == 'text', 'text subview must be an original text leaf')
        digest = sha(value.encode('utf-8'))
    elif view['encoding'] == 'canonical_json':
        require(view['view'] != 'image', 'JSON/text/geometry cannot attest image pixels')
        digest = sha(canonical(value))
    else:
        require(view['encoding'] == 'file_bytes' and view['view'] == 'image' and isinstance(value, dict), 'unsupported subview encoding')
        image_hashes = {value[k] for k in ['sha256', 'image_sha256', 'source_image_sha256', 'original_page_asset_sha256', 'new_300dpi_asset_sha256'] if valid_sha(value.get(k))}
        require(view['view_sha256'] in image_hashes, 'image subview file SHA has no original locator binding')
        digest = view['view_sha256']
    require(digest == view['view_sha256'], 'subview SHA mismatch')
    # Locator is the immutable original pointer, not an inferred broader page.
    require(view['locator'] == {'source_bundle_pointer': view['scope_pointer']}, 'subview locator must be the exact original pointer')


def base_requirements(packet, inventory):
    row = packet['source_bundle']['source_record']
    inv = {v['resource_id']: v for v in inventory}
    pairs = [('BODY-' + row['id'], 'text', 'current_body', '/source_record')]
    for i, context in enumerate(row['contexts']):
        pairs.extend((context['context_id'], view, 'preserved_current_source_context', '/source_record/contexts/' + str(i))
                     for view in inv[context['context_id']]['available_views'])
        if context['kind'] == 'same_snapshot_source_display_geometry':
            structure = context['structure']; pointer = '/source_record/contexts/' + str(i)
            pairs.append((structure['bound_body_instruction_resource_id'], 'text', 'necessary_role_or_scope_boundary', pointer))
            pairs.append((structure['bound_body_instruction_region_id'], 'geometry', 'necessary_geometry', pointer))
            for d_i, document in enumerate(packet['source_bundle']['explicit_or_primary_source_resources']):
                for region in document.get('source_display_regions', []):
                    if region['region_id'] != structure['bound_body_instruction_region_id']:
                        continue
                    pairs.extend((child, 'text', 'necessary_role_or_scope_boundary', pointer) for child in region['children_resource_ids'])
                    pairs.extend((text['source_resource_id'], 'text', 'necessary_role_or_scope_boundary', '/explicit_or_primary_source_resources/' + str(d_i))
                                 for text in document.get('source_visual_text_resources', []) if text['role'] == 'illustration_scope_notice')
    result = []
    for resource, view, relation, pointer in pairs:
        if any(r['resource_id'] == resource and r['view'] == view for r in result):
            continue
        require(resource in inv and view in inv[resource]['available_views'], 'current same-frame source closure missing')
        result.append({'requirement_id': 'REQ-' + sha((resource + ':' + view).encode())[:20],
                       'resource_id': resource, 'view': view, 'scope_pointer': None,
                       'source_relation_kind': relation, 'source_evidence_locator': inv[resource]['locator'],
                       'source_basis': {'note': 'Current body or preserved current CTX source structure; review finite applicability without inheriting other whole-document content.', 'bundle_pointers': [pointer]},
                       'dependency_dimensions': list(DIMENSIONS)})
    return result


def prepare_scope(packet, run_id, reader):
    packet_identity(packet)
    require(run_id and reader, 'run and reader required')
    inventory = owner_inventory(packet['source_bundle'])
    return {'scope_version': 'native-necessary-read-v3',
            'uniform_protocol_sha256': uniform_protocol_sha(),
            'run_id': run_id, 'reader': reader, 'source_id': packet['source_id'],
            'source_bundle_sha256': packet['source_bundle_sha256'], 'source_inventory': inventory,
            'additional_views': [], 'requirements': base_requirements(packet, inventory),
            'necessary_source_scope_review_status': 'pending', 'scope_source_basis': None,
            'reference_resolution': [], 'read_receipts': [], 'use_receipts': [], 'source_requests': [],
            'required_read_complete_claim': False, 'read_or_use_inferred_from_availability': False}


def dependency_output_projection(item):
    """Only null/request presence; never judge whether a dimension should be null."""
    return {'null_dimensions': [d for d in DIMENSIONS if d in item['labels'] and item['labels'][d] is None],
            'material_request_dimensions': sorted({r['dimension'] for r in item['material_requests']
                                                   if r.get('kind') == 'material_missing' and isinstance(r.get('detail'), str) and r['detail'].strip()})}


def check_scope(packet, log, output_projection=None):
    packet_identity(packet)
    schema = parse((ROOT / 'necessary-source-scope.schema.json').read_bytes())
    from packet_builder import schema_check
    schema_check(log, schema)
    require(log['source_id'] == packet['source_id'] and log['source_bundle_sha256'] == packet['source_bundle_sha256'], 'scope source/full-bundle binding mismatch')
    require(log['uniform_protocol_sha256'] == uniform_protocol_sha(), 'uniform reading protocol SHA mismatch')
    require(log['read_or_use_inferred_from_availability'] is False, 'availability cannot imply read/use')
    bundle = packet['source_bundle']; inventory = owner_inventory(bundle)
    require(canonical(log['source_inventory']) == canonical(inventory), 'complete available inventory changed')
    require(log['necessary_source_scope_review_status'] == 'complete', 'necessary scope review pending')
    source_basis(bundle, log['scope_source_basis'])
    views = inventory_views(inventory)
    for v in log['additional_views']:
        validate_added_view(bundle, v)
        key = view_key(v); require(key not in views, 'duplicate/overridden source subview')
        views[key] = v
    requirements = {r['requirement_id']: r for r in log['requirements']}
    require(len(requirements) == len(log['requirements']), 'duplicate necessary requirement')
    for r in base_requirements(packet, inventory):
        actual = requirements.get(r['requirement_id'])
        fields = ['resource_id', 'view', 'scope_pointer', 'source_relation_kind', 'source_evidence_locator']
        require(actual is not None and all(actual[k] == r[k] for k in fields), 'current/body/CTX requirement removed or changed')
    for r in requirements.values():
        source_basis(bundle, r['source_basis'])
        bound_view = views.get(view_key(r))
        if bound_view:
            require(r['source_evidence_locator'] == bound_view['locator'], 'necessary view locator differs from original binding')
        if r['source_relation_kind'] == 'current_body':
            require(set(r['dependency_dimensions']) == set(DIMENSIONS), 'unread current body must stop all dimensions')
    good = {}; reads = {}; technical = []
    for r in log['read_receipts']:
        require(r['receipt_id'] not in reads, 'duplicate read receipt')
        reads[r['receipt_id']] = r
        require(r['run_id'] == log['run_id'] and r['reader'] == log['reader'] and r['source_id'] == log['source_id'], 'read run/reader/source mismatch')
        view = views.get(view_key(r))
        require(view is not None and all(r[k] == view[k] for k in ['source_sha256', 'view_sha256']), 'read source/view/SHA mismatch')
        require(r['locator_read'] == view['locator'], 'read locator differs from the bound full view')
        require(r['event_id'] or r['local_event_id'], 'actual or local read event ID missing')
        if r['delivery_status'] == 'complete' and r['read_attestation'] == 'recorded':
            good[r['receipt_id']] = r
        if r['delivery_status'] in ['truncated', 'failed', 'not_delivered']:
            technical.append({'receipt_id': r['receipt_id'], 'status': r['delivery_status']})
    good_keys = {view_key(r) for r in good.values()}
    issues = []
    for r in requirements.values():
        key = view_key(r)
        if key not in views or key not in good_keys:
            issues.append({'issue_id': r['requirement_id'], 'reason': 'missing_required_source_view' if key not in views else 'required_view_not_read',
                           'dependency_dimensions': r['dependency_dimensions']})
    ref_ids = set()
    for ref in log['reference_resolution']:
        require(ref['reference_id'] not in ref_ids, 'duplicate source reference')
        ref_ids.add(ref['reference_id']); source_basis(bundle, ref['source_basis'])
        if ref['resolution_status'] in ['exact_snapshot', 'same_edition_confirmed']:
            if ref['necessary_dependency']:
                require(ref['target_requirement_id'] in requirements, 'resolved necessary reference needs declared target view requirement')
                target = views.get(view_key(requirements[ref['target_requirement_id']]))
                require(target and target['source_sha256'] == ref['target_source_sha256'], 'resolved reference target SHA/view binding mismatch')
            else:
                require(any(v['source_sha256'] == ref['target_source_sha256'] for v in views.values()), 'optional reference source SHA unavailable')
            require(ref['identity_basis_pointers'], 'reference source identity evidence missing')
            for pointer in ref['identity_basis_pointers']:
                pointer_value(bundle, pointer)
        elif ref['necessary_dependency']:
            issues.append({'issue_id': ref['reference_id'], 'reason': 'required_reference_unresolved', 'dependency_dimensions': ref['dependency_dimensions']})
    for use in log['use_receipts']:
        if use['use_status'] != 'used':
            continue
        read = good.get(use['read_receipt_id'])
        require(read and view_key(read) == view_key(use) and read['source_sha256'] == use['source_sha256'] and read['view_sha256'] == use['view_sha256'], 'used requires same-resource same-view complete recorded actual read')
        require(use['use_scope'].strip(), 'actual use scope missing')
    full = not issues
    require(log['required_read_complete_claim'] is full, 'required-read-complete claim differs from actual necessary receipts/reference closure')
    requests = {r['issue_id']: r for r in log['source_requests']}
    require(len(requests) == len(log['source_requests']), 'duplicate source request issue')
    require(all(r['status'] == 'resolved' or r['issue_id'] in {i['issue_id'] for i in issues} for r in requests.values()), 'unresolved source request has no declared dependency issue')
    handled = True
    stop_dimensions = set()
    for issue in issues:
        request = requests.get(issue['issue_id'])
        ok = (request is not None and request['conclusions_stopped'] is True and request['status'] == 'unresolved'
              and set(request['dependency_dimensions']) == set(issue['dependency_dimensions']))
        handled = handled and ok
        stop_dimensions.update(issue['dependency_dimensions'])
    if issues:
        handled = (handled and output_projection is not None
                   and stop_dimensions <= set(output_projection['null_dimensions'])
                   and stop_dimensions <= set(output_projection['material_request_dimensions']))
    return {'source_id': packet['source_id'], 'source_bundle_sha256': packet['source_bundle_sha256'],
            'required_read_complete': full, 'dependency_handling_complete': bool(handled),
            'scope_record_valid': bool(handled) and not technical,
            'dependency_stops': issues, 'stopped_dimensions': sorted(stop_dimensions),
            'observed_technical_read_failures': technical,
            'available_view_count': len(views), 'complete_recorded_read_count': len(good_keys),
            'unread_available_view_count': len(set(views) - good_keys),
            'actual_reading_independently_proven': False, 'semantic_necessity_or_correctness_certified': False}
