import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

if (process.argv.includes('--discover')) {
  const workbook = Workbook.create();
  console.log(workbook.help('fx.HYPERLINK', {include:'index,examples,notes', maxChars:4000}).ndjson);
  process.exit(0);
}

const OUT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const ROOT = path.dirname(path.dirname(OUT));
const SOURCE = path.join(ROOT, '05-validation/full800-common-v15-prerelease-sol');
const DIMENSIONS = ['S', 'E', 'Ec', 'I', 'F'];
const VERSION = 'formal800-human-workbooks-v15-prerelease-1';
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const canonical = value => {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
};
const cj = value => Buffer.from(canonical(value), 'utf8');
const parse = async p => JSON.parse(await fs.readFile(p, 'utf8'));
const binding = async p => {
  const raw = await fs.readFile(p);
  return {absolute_path:path.resolve(p), bytes:raw.length, sha256:sha(raw)};
};
const put = async (p, raw) => {
  await fs.mkdir(path.dirname(p), {recursive:true, mode:0o700});
  await fs.writeFile(p, raw, {flag:'wx', mode:0o600});
};
const savejson = async (p, value) => put(p, JSON.stringify(value, null, 2) + '\n');
const exists = async p => fs.access(p).then(()=>true,()=>false);
assert(!(await exists(path.join(OUT, 'seal.json'))), 'Do not modify sealed output');
assert(!(await exists(path.join(OUT, 'coder-A'))) && !(await exists(path.join(OUT, 'shared-source'))), 'Do not rerun over output');

const sourceSeal = await parse(path.join(SOURCE, 'seal.json'));
const sourceSealBinding = await binding(path.join(SOURCE, 'seal.json'));
const sourceMembersBefore = [];
for (const entry of sourceSeal.members) {
  const current = await binding(entry.absolute_path);
  assert.equal(current.sha256, entry.sha256); assert.equal(current.bytes, entry.bytes);
  sourceMembersBefore.push(current);
}
assert.equal(sha(cj(sourceSeal.members)), sourceSeal.member_table_sha256);
const indexInput = path.join(SOURCE, 'shared-source/source-resource-index.json');
const sourceIndex = await parse(indexInput);
const sourcePer = new Map(sourceIndex.per_record.map(r => [r.source_id, r]));
const commonSourcePath=path.join(SOURCE,'shared-source/common-source-bundles.jsonl');
const sourceRaw=new Map((await fs.readFile(commonSourcePath,'utf8')).trimEnd().split('\n').map(raw=>[JSON.parse(raw).source_record.id,Buffer.from(raw,'utf8')]));
assert.equal(sourceRaw.size,800);
const inputBindings = [sourceSealBinding, await binding(indexInput),await binding(commonSourcePath)];
const deliveryFiles = [];
await fs.mkdir(path.join(OUT, 'shared-source/source-files'), {recursive:true, mode:0o700});
for (const entry of sourceIndex.deduplicated_files) {
  const original = await binding(entry.prepared_absolute_path);
  assert.equal(original.sha256, entry.sha256); assert.equal(original.bytes, entry.bytes);
  inputBindings.push(original);
  const dest = path.join(OUT, 'shared-source/source-files', path.basename(entry.prepared_absolute_path));
  await put(dest, await fs.readFile(entry.prepared_absolute_path));
  const prepared = {...entry, input_prepared_absolute_path:entry.prepared_absolute_path,
    prepared_absolute_path:dest, prepared_relative_path:path.relative(OUT, dest)};
  deliveryFiles.push(prepared);
}
const deliveryIndex = {version:VERSION, files:deliveryFiles,
  relative_path_base:'delivery package root', availability_not_reading_or_use:true};
await savejson(path.join(OUT, 'shared-source/delivery-source-assets-index.json'), deliveryIndex);
const assets = new Map(deliveryFiles.map(r => [r.sha256, r]));

const escape = text => String(text).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
const pointerPart = text => text.replaceAll('~','~0').replaceAll('/','~1');
function structural(value, pointer='') {
  if (typeof value === 'string') return `<pre class="literal" data-json-pointer="${escape(pointer)}"><span>${escape(value)}</span></pre>`;
  if (Array.isArray(value)) return value.length ? `<ol>${value.map((v,i)=>`<li>${structural(v,pointer+'/'+i)}</li>`).join('')}</ol>` : '<pre>[]</pre>';
  if (value !== null && typeof value === 'object') return `<dl>${Object.entries(value).map(([k,v])=>`<dt>${escape(k)}</dt><dd>${structural(v,pointer+'/'+pointerPart(k))}</dd>`).join('')}</dl>`;
  return `<pre>${escape(JSON.stringify(value))}</pre>`;
}
const materialPages = []; const workbookRecords = []; const artifactChecks = [];
const sheetName = '初判-pre-release';
for (const side of ['A','B']) {
  const coder = path.join(OUT, 'coder-'+side);
  const packetPath = path.join(SOURCE, 'coder-'+side, 'packet.jsonl');
  const packetIndexPath = path.join(SOURCE, 'coder-'+side, 'packet-index.json');
  const manualPath = path.join(SOURCE, 'coder-'+side, 'manual.txt');
  inputBindings.push(await binding(packetPath), await binding(packetIndexPath), await binding(manualPath));
  const packets = (await fs.readFile(packetPath, 'utf8')).trimEnd().split('\n').map(line=>JSON.parse(line));
  const packetIndex = await parse(packetIndexPath);
  assert.equal(packets.length,800); assert.equal(new Set(packets.map(p=>p.blind_id)).size,800);
  await fs.mkdir(path.join(coder,'materials'), {recursive:true,mode:0o700});
  await put(path.join(coder,'manual.txt'), await fs.readFile(manualPath));
  await savejson(path.join(coder,'source-assets-index.json'), deliveryIndex);
  const matrix = []; const rowHeights = [];
  for (const [n, packet] of packets.entries()) {
    const blind = packet.blind_id; const bundle = packet.source_bundle; const raw = sourceRaw.get(bundle.source_record.id);
    assert(raw, 'Exact original source bytes must exist');
    assert.equal(blind, packetIndex.entries[n].blind_id);
    assert.equal(sha(raw), packet.source_bundle_canonical_sha256); assert.equal(raw.length,packet.source_bundle_canonical_UTF8_bytes);
    const body = bundle.source_record.text;
    assert(body.length<=32767,'Current body must never be cut to Excel limit');
    const jsonPath = path.join(coder,'materials',blind+'.json');
    const htmlPath = path.join(coder,'materials',blind+'.html');
    await put(jsonPath,raw);
    const per = sourcePer.get(bundle.source_record.id); assert(per);
    const fileEntries = per.source_file_SHAs.map(h=>{assert(assets.has(h));return assets.get(h);});
    const fileLinks = fileEntries.map(entry=>{
      const href='../../'+entry.prepared_relative_path.split(path.sep).join('/');
      const preview = entry.image_pixels ? `<img loading="lazy" src="${escape(href)}" alt="来源图片 SHA256 ${entry.sha256}">` : '';
      return `<li><a href="${escape(href)}">${escape(entry.resource_kinds.join(', '))} ${entry.sha256}</a><div>${entry.bytes} bytes</div>${preview}</li>`;
    }).join('');
    const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${blind} 完整v15材料（pre-release）</title><style>body{font:16px/1.6 Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 20px;color:#222}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.65 Arial,sans-serif;margin:8px 0;padding:8px;background:#f7f7f7}dt{font-weight:bold;margin-top:12px}dd{margin-left:20px}img{display:block;max-width:100%;height:auto;margin:12px 0}li{margin-bottom:8px}a{color:#0563c1}</style></head><body><h1>${blind} 完整v15材料</h1><p>pre-release。ROOT开发结果和联合freeze完成前，不分发正式判读。</p><p><a href="../manual.txt">候选手册原文</a> · <a href="${blind}.json">完整原始源束JSON（SHA256 ${sha(raw)}）</a></p><h2>当前条款正文</h2><pre id="current-body">${escape(body)}</pre><h2>完整原始材料与语境</h2>${structural(bundle)}<h2>实际同SHA来源文件、图片和PDF</h2><ul>${fileLinks}</ul><h2>源束原始JSON</h2><pre id="bundle-original">${escape(raw.toString('utf8'))}</pre></body></html>`;
    await put(htmlPath,html);
    materialPages.push({side, blind_id:blind, source_bundle_sha256:sha(raw), source_bundle_bytes:raw.length,
      html_relative_path:path.relative(OUT,htmlPath), json_relative_path:path.relative(OUT,jsonPath),
      source_file_SHAs:per.source_file_SHAs});
    const widthUnits = line => [...line].reduce((a,c)=>a+(c.charCodeAt(0)>255?2:1),0);
    const lines = body.split('\n').reduce((a,l)=>a+Math.max(1,Math.ceil(widthUnits(l)/86)),0);
    const height = Math.max(36,Math.min(409,lines*15+10));
    for (const dim of DIMENSIONS) {
      matrix.push([blind,body,dim,null,null]);
      rowHeights.push(height);
    }
  }
  const wb = Workbook.create(); const sheet = wb.worksheets.add(sheetName);
  sheet.getRange('A1:E1').values = [['盲号（打开完整材料）','条款正文','维度','值（0/1）','理由（待定原因/补材）']];
  sheet.getRange('A2:E4001').values = matrix;
  const all = sheet.getRange('A1:E4001');
  all.format.font = {name:'Arial',size:11,color:'#222222'};
  all.format.verticalAlignment='top';
  sheet.getRange('A1:E1').format = {fill:'#E8EDF2',font:{name:'Arial',size:11,bold:true,color:'#222222'},rowHeight:30,verticalAlignment:'center'};
  sheet.getRange('A:A').format.columnWidth=24;
  sheet.getRange('B:B').format.columnWidth=92;
  sheet.getRange('C:C').format.columnWidth=8;
  sheet.getRange('D:D').format.columnWidth=12;
  sheet.getRange('E:E').format.columnWidth=44;
  sheet.getRange('B2:B4001').format.wrapText=true;
  sheet.getRange('E2:E4001').format.wrapText=true;
  sheet.getRange('A2:A4001').format.font={name:'Arial',size:11,color:'#0563C1'};
  sheet.getRange('D2:E4001').format.fill='#FFFBE6';
  sheet.getRange('D2:D4001').setNumberFormat('0');
  sheet.getRange('D2:D4001').dataValidation={rule:{type:'list',values:['0','1']}};
  for(let i=0;i<rowHeights.length;i+=5) sheet.getRange(`A${i+2}:E${i+6}`).format.rowHeight=rowHeights[i];
  sheet.freezePanes.freezeRows(1); sheet.freezePanes.freezeColumns(1); sheet.showGridLines=false;
  wb.recalculate();
  const values=sheet.getRange('A2:E4001').values;
  assert.equal(values.length,4000);
  for(let n=0;n<800;n++) for(let d=0;d<5;d++) {
    const row=values[n*5+d]; assert.equal(row[0],packets[n].blind_id);
    assert.equal(row[1],packets[n].source_bundle.source_record.text); assert.equal(row[2],DIMENSIONS[d]);
    assert.equal(row[3],null); assert.equal(row[4],null);
  }
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1200});
  const fields=await wb.inspect({kind:'table',range:`'${sheetName}'!C1:E6`,include:'values,formulas',tableMaxRows:6,tableMaxCols:3,maxChars:1800});
  artifactChecks.push({side, error_scan:errors.ndjson, input_region_inspect:fields.ndjson,
    direct_values_readback_4000_rows:true, D_E_all_null:true,
    native_hyperlinks_post_export_required:true,artifact_HYPERLINK_calculation_unimplemented:true});
  const top=await wb.render({sheetName,range:'A1:E6',scale:1,format:'png'});
  await put(path.join(OUT,'_build/previews',side+'-top.png'),new Uint8Array(await top.arrayBuffer()));
  const maxBodyIndex=packets.reduce((m,p,i)=>p.source_bundle.source_record.text.length>packets[m].source_bundle.source_record.text.length?i:m,0);
  const row=2+maxBodyIndex*5;
  const longest=await wb.render({sheetName,range:`A${row}:E${row}`,scale:1,format:'png'});
  await put(path.join(OUT,'_build/previews',side+'-longest-body.png'),new Uint8Array(await longest.arrayBuffer()));
  const output=await SpreadsheetFile.exportXlsx(wb);
  const outputPath=path.join(coder,`formal800-${side}-pre-release.xlsx`);
  assert(!(await exists(outputPath))); await output.save(outputPath);
  const guide='本表为pre-release，ROOT开发结果和联合freeze完成前不分发正式判读。\nA列每个盲号可打开同目录materials中的完整v15材料页；B列是逐字原条款正文，C列是S/E/Ec/I/F维度，D列空白待独立填0/1，E列空白待填写理由。证据不足时D留空、E记录待定原因与具体补材；不能把缺材填0。\n请将本方coder目录与shared-source放在同一个包根目录，保持相对路径。材料页含完整body、context及完整补充资源、原始源束JSON链接，图片/PDF实际同SHA文件也在shared-source。\n每条五维独立判断。不能看另一方/机器/Gold答案，不请求AI代填。保存原始独立初判后，再组织补材重判或裁定，保留初判版本。此表没有真人复核栏，没有任何真实编码。\n';
  await put(path.join(coder,'填写说明.txt'),guide);
  workbookRecords.push({side,worksheet:sheetName,file:await binding(outputPath),rows_N:4000,unique_blind_N:800,
    columns:['blind_id','current_source_body','dimension','blank_0_1_value','blank_reason'],
    header_row:1,first_data_row:2,last_data_row:4001,dimension_order:DIMENSIONS,
    max_current_body_chars:Math.max(...packets.map(p=>p.source_bundle.source_record.text.length)),
    packet_input:await binding(packetPath),manual:await binding(path.join(coder,'manual.txt')),status:'pre_release'});
}
await savejson(path.join(OUT,'_build/artifact-checks.json'),artifactChecks);
await savejson(path.join(OUT,'material-pages-index.json'),{version:VERSION,material_page_N:1600,pages:materialPages});
await savejson(path.join(OUT,'workbook-manifest.json'),{version:VERSION,status:'pre_release',workbooks:workbookRecords,
  source_package_seal:sourceSealBinding,source_member_N:sourceMembersBefore.length,
  human_or_AI_labels_created_N:0,human_review_columns_added_N:0,final_release_freeze_completed:false,
  source_material_rendering:'literal escaped text without deletions; raw canonical source bundle bytes linked separately',input_bindings:inputBindings});
for(const before of sourceMembersBefore) assert.deepEqual(await binding(before.absolute_path),before);
assert.deepEqual(await binding(sourceSealBinding.absolute_path),sourceSealBinding);
console.log(JSON.stringify({status:'workbooks_and_full_material_pages_written_unsealed_pending_independent_readback',workbooks_N:2,
  rows_per_workbook:4000,material_pages_N:1600,shared_asset_N:deliveryFiles.length,source_members_unchanged_N:sourceMembersBefore.length}));
