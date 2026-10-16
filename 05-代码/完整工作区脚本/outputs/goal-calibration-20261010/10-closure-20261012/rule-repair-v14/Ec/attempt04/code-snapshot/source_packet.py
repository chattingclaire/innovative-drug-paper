"""Generic source-only semantic adapter and inventories extracted from sealed v14.
Raw bundle fields stay exact. Administrative ten-record loader is not included.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path

_SHA = re.compile(r'[a-f0-9]{64}\Z')
BUNDLE_KEYS = {'common_source_bundle_version', 'source_record', 'source_documents',
               'explicit_or_primary_source_resources', 'preserved_historical_neutral_source_supplements',
               'source_full_text_resources', 'source_asset_locations', 'source_locator_bases',
               'source_reference_index', 'source_provenance_addenda'}

class PacketInterfaceError(ValueError):
    """A source shape, finite scope or exact byte binding is unsupported."""


def _fail(path, reason):
    raise PacketInterfaceError(f'{path}: {reason}')


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()



def _derived_contexts(bundle):
    """Exact source text handles; candidate availability conveys no applicability."""
    raw = bundle['source_record']['contexts']
    contexts, origins = [], {}
    candidates, extension_candidates = [], []
    for di, doc in enumerate(bundle['explicit_or_primary_source_resources']):
        for ti, text in enumerate(doc.get('source_texts', [])):
            target = (extension_candidates if text.get('source_locator', {}).get('kind') ==
                      'structured_JSON_and_original_HTML' else candidates)
            target.append((text, doc, f'/explicit_or_primary_source_resources/{di}/source_texts/{ti}', 'source_resource_text'))
        for ti, text in enumerate(doc.get('source_visual_text_resources', [])):
            candidates.append((text, doc, f'/explicit_or_primary_source_resources/{di}/source_visual_text_resources/{ti}', 'visual_source_text'))
    for hi, text in enumerate(bundle['preserved_historical_neutral_source_supplements']):
        candidates.append((text, text, f'/preserved_historical_neutral_source_supplements/{hi}', 'historical_source_fragment'))
    for fi, doc in enumerate(bundle['source_full_text_resources']):
        if doc.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            extension_candidates.append((doc, doc, f'/source_full_text_resources/{fi}', 'source_resource_text'))
        if doc.get('kind') == 'verbatim_UTF8_snapshot_text':
            extension_candidates.append((doc, doc, f'/source_full_text_resources/{fi}', 'source_textleaf'))
        for pi, text in enumerate(doc.get('paragraphs', doc.get('source_texts', []))):
            candidates.append((text, doc, f'/source_full_text_resources/{fi}/' + ('paragraphs' if 'paragraphs' in doc else 'source_texts') + f'/{pi}', 'source_resource_text'))
    for text, doc, pointer, kind in candidates + extension_candidates:
        if not isinstance(text, dict) or not isinstance(text.get('text'), str):
            _fail(pointer, 'source text candidate has unsupported raw shape')
        sha = text.get('source_sha256', doc.get('source_sha256', doc.get('source_pdf_sha256', doc.get('snapshot_sha256'))))
        ref = copy.deepcopy(text.get('source_ref'))
        if ref is None:
            ref = {'sha256': sha, 'source_resource_id': text.get('source_document_resource_id', 'SOURCE-' + str(sha)),
                   'locator': copy.deepcopy(text.get('source_locator', text.get('locator',
                                {'physical_pages': text.get('physical_pages', [])})))}
        if not isinstance(ref.get('sha256'), str) or not _SHA.fullmatch(ref['sha256']):
            _fail(pointer, 'source text candidate has no bound document SHA')
        resource_id = text.get('source_resource_id', text.get('source_paragraph_id', text.get('supplement_id', doc.get('source_resource_id'))))
        original = [c for c in raw if c.get('text') == text['text'] and c['source_ref']['sha256'] == ref['sha256']
                    and resource_id is not None and resource_id in
                    (c.get('structure', {}).get('source_paragraph_id'), c['source_ref']['locator'].get('source_paragraph_id'))]
        origin = {'source_resource_id': resource_id, 'source_bundle_pointer': pointer,
                  'role': text.get('role'), 'representation': text.get('representation', text.get('kind')),
                  'source_sha256': ref['sha256'], 'document_resource_id': doc.get('source_resource_id')}
        if kind == 'source_textleaf':
            inventory_id, view, view_sha = resource_id, 'text', text['text_utf8_sha256']
            origin['origin_inventory_consumption_scope'] = 'complete_literal_text_view'
            origin['semantic_only_alias_origins'] = {
                'text_sha256': pointer + '/text_utf8_sha256', 'source_locator': pointer + '/locator'}
        elif kind == 'visual_source_text' or text.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            inventory_id, view, view_sha = resource_id, 'text', text['text_sha256']
            origin['origin_inventory_consumption_scope'] = 'complete_literal_text_view'
        elif kind == 'historical_source_fragment':
            inventory_id, view, view_sha = 'HISTORICALSOURCE-' + h(cj(text))[:20], 'text', h(cj(text))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_payload'
        elif pointer.startswith('/source_full_text_resources/'):
            inventory_id, view, view_sha = 'FULLSOURCE-' + h(cj(doc))[:20], 'text', h(cj(doc))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_payload'
        else:
            inventory_id, view, view_sha = doc['source_resource_id'], 'document_bundle', h(cj(doc))
            origin['origin_inventory_consumption_scope'] = 'partial_exact_text_field_of_document_bundle'
        origin.update({'origin_inventory_resource_id': inventory_id,
                       'origin_inventory_view': view, 'origin_inventory_view_sha256': view_sha})
        if original:
            for context in original:
                origins.setdefault(context['context_id'], origin)
            continue
        identity = {'source_resource_id': resource_id, 'source_ref': ref, 'text': text['text'],
                    'role': text.get('role'), 'representation': text.get('representation', text.get('kind'))}
        cid = 'CTX-DERIVED-' + h(cj(identity))[:24]
        if cid in origins: continue
        structure = {'source_resource_id': resource_id, 'source_bundle_pointer': pointer}
        keys = ('heading_path', 'source_paragraph_id', 'role', 'representation')
        if text.get('source_locator', {}).get('kind') == 'structured_JSON_and_original_HTML':
            keys += ('article', 'clause_index_one_based')
        if kind == 'source_textleaf': keys += ('source_version_id',)
        for key in keys:
            if key in text: structure[key] = copy.deepcopy(text[key])
        if text.get('role') is not None: structure['source_role'] = text['role']
        if resource_id is not None: structure.setdefault('source_paragraph_id', resource_id)
        contexts.append({'context_id': cid, 'kind': kind, 'text': text['text'],
                         'source_document': ref['source_resource_id'], 'source_ref': ref, 'structure': structure})
        origins[cid] = origin
    return contexts, origins


def semantic_unit(bundle):
    """Preserve raw current fields and expose neutral resources without record IDs."""
    if not isinstance(bundle, dict) or set(bundle) not in (BUNDLE_KEYS, BUNDLE_KEYS | {'source_bundle_extension'}):
        _fail('bundle', 'expected complete source bundle')
    row = bundle['source_record']
    unit = {key: copy.deepcopy(value) for key, value in row.items() if key != 'id'}
    unit['attachments'] = copy.deepcopy(row.get('source_attachments', []))
    semantic_bundle = copy.deepcopy(bundle)
    semantic_bundle['source_record'].pop('id', None)
    # Exact interface aliases exist only in the semantic copy. The raw complete
    # input and its sealed leaf fields/byte hashes are preserved unchanged.
    for resource in semantic_bundle['source_full_text_resources']:
        if resource.get('kind') == 'verbatim_UTF8_snapshot_text':
            resource['text_sha256'] = resource['text_utf8_sha256']
            resource['source_locator'] = copy.deepcopy(resource['locator'])
    for field in ('preserved_historical_neutral_source_supplements', 'source_reference_index'):
        for item in semantic_bundle[field]: item.pop('record_id', None)
    unit['source_bundle'] = semantic_bundle
    derived, origins = _derived_contexts(bundle)
    unit['contexts'].extend(derived)
    unit['derived_context_origins'] = origins
    return unit


def _v12_source_inventory(b):
 """Describe available views, never claim the consumer read or used them."""
 inv=[];r=b['source_record'];s=r['source_ref']['sha256']
 inv.append({'resource_id':'BODY-'+r['id'],'source_document_id':'SOURCE-'+s,'source_sha256':s,'locator':r['source_ref']['locator'],'available_views':{'text':h(r['text'])},'availability_status':'available','representation':r.get('body_source_representation',{'kind':'current_source_body'}),'consumer_read_status':'not_recorded'})
 for n in r['contexts']:
  views={'geometry':h(cj(n['structure']))};fields={k:n[k] for k in ['text','title','caption','headers','row_cells'] if k in n}
  if fields:views['text']=h(cj(fields))
  inv.append({'resource_id':n['context_id'],'source_document_id':n['source_ref']['source_resource_id'],'source_sha256':n['source_ref']['sha256'],'locator':n['source_ref']['locator'],'available_views':views,'availability_status':'available','representation':n['kind'],'consumer_read_status':'not_recorded'})
 for d in b['explicit_or_primary_source_resources']:
  ds=d.get('source_sha256',d.get('snapshot_sha256'));inv.append({'resource_id':d['source_resource_id'],'source_document_id':d['source_resource_id'],'source_sha256':ds,'locator':{'document_resource_id':d['source_resource_id']},'available_views':{'document_bundle':h(cj(d))},'availability_status':'available','representation':'source_document_resource; applicability_scope_requires_source_read','consumer_read_status':'not_recorded'})
  for z in d.get('source_visual_text_resources',[]):
   inv.append({'resource_id':z['source_resource_id'],'source_document_id':z['source_document_resource_id'],'source_sha256':z['source_sha256'],'locator':z['source_locator'],'available_views':{'text':z['text_sha256']},'availability_status':'available','representation':z['representation'],'role':z['role'],'production_read_provenance':z['source_review_provenance'],'consumer_read_status':'not_recorded'})
  for z in d.get('source_display_regions',[]):
   inv.append({'resource_id':z['region_id'],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':{'physical_page':z['physical_page'],'coordinate_system':z['coordinate_system'],'bbox_points_xyxy':z['bbox_points_xyxy']},'available_views':{'geometry':h(cj(z))},'availability_status':'available','representation':'pure_display_region_manual_padded','consumer_read_status':'not_recorded'})
 for z in b['preserved_historical_neutral_source_supplements']:
  inv.append({'resource_id':'HISTORICALSOURCE-'+h(cj(z))[:20],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':z.get('source_locator',{}),'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'previously_shared_neutral_source_fragment','consumer_read_status':'not_recorded'})
 for z in b['source_full_text_resources']:
  inv.append({'resource_id':'FULLSOURCE-'+h(cj(z))[:20],'source_document_id':z.get('source_resource_id'),'source_sha256':z.get('source_sha256'),'locator':{'representation':'source_full_text_resource_payload'},'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'source_full_text_resource; scope_requires_source_read','consumer_read_status':'not_recorded'})
 for a in b['source_asset_locations']:
  inv.append({'resource_id':a['attachment_id'],'source_document_id':'SOURCE-'+a.get('source_pdf_sha256',s),'source_sha256':a.get('source_pdf_sha256',s),'locator':{'absolute_path':a['absolute_path'],'physical_page':a.get('physical_page')},'available_views':{'image':a['sha256']},'availability_status':'available_SHA_matched','representation':a.get('kind','original_source_asset'),'consumer_read_status':'not_recorded'})
 seen={};out=[]
 for z in inv:
  if z['resource_id'] in seen:
   if cj(z)!=cj(seen[z['resource_id']]):
    old=seen[z['resource_id']]
    if old['available_views']!=z['available_views'] or old['source_sha256']!=z['source_sha256'] or old['locator'].get('physical_page')!=z['locator'].get('physical_page'):raise ValueError('conflicting resource ID')
    old['locator'].setdefault('alternate_absolute_paths',[]).append(z['locator']['absolute_path'])
  else:seen[z['resource_id']]=z;out.append(z)
 return out


def _v13_source_inventory(bundle):
    """Keep old inventories; describe literal JSON/HTML paragraphs without invented page geometry."""
    paragraphs = [z for z in bundle['source_full_text_resources']
                  if isinstance(z, dict) and isinstance(z.get('source_locator'), dict)
                  and z['source_locator'].get('kind') == 'structured_JSON_and_original_HTML']
    base_view = dict(bundle)
    base_view['source_full_text_resources'] = [z for z in bundle['source_full_text_resources']
                                              if z not in paragraphs]
    inventory = _v12_source_inventory(base_view)
    for z in paragraphs:
        inventory.append({
            'resource_id': z['source_resource_id'],
            'source_document_id': z['source_document_resource_id'],
            'source_sha256': z['source_sha256'],
            'locator': copy.deepcopy(z['source_locator']),
            'available_views': {'text': z['text_sha256']},
            'availability_status': 'available',
            'representation': z['representation'],
            'role': z['role'],
            'consumer_read_status': 'not_recorded',
            'consumer_use_status': 'not_recorded',
        })
    if len({z['resource_id'] for z in inventory}) != len(inventory):
        raise ValueError('conflicting source resource inventory ID')
    return inventory


def source_inventory(bundle):
    """Literal text SHA/coordinates only; available does not mean read or used."""
    added = [z for z in bundle['source_full_text_resources']
             if isinstance(z, dict) and z.get('kind') == 'verbatim_UTF8_snapshot_text'
             and isinstance(z.get('source_sha256'), str) and _SHA.fullmatch(z['source_sha256'])]
    base_view = dict(bundle)
    base_view['source_full_text_resources'] = [z for z in bundle['source_full_text_resources'] if z not in added]
    inventory = _v13_source_inventory(base_view)
    for z in added:
        inventory.append({'resource_id': z['source_resource_id'],
                          'source_document_id': 'SOURCE-' + z['source_sha256'],
                          'source_sha256': z['source_sha256'], 'locator': copy.deepcopy(z['locator']),
                          'available_views': {'text': z['text_utf8_sha256']},
                          'availability_status': 'available',
                          'representation': 'literal original UTF8 snapshot text; bounded complete physical lines',
                          'consumer_read_status': 'not_recorded', 'consumer_use_status': 'not_recorded'})
    if len({z['resource_id'] for z in inventory}) != len(inventory):
        raise ValueError('conflicting source resource inventory ID')
    return inventory
