import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { FileBlob, Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const ROOT = '/PROJECT_ROOT/outputs/goal-calibration-20261010';
const DATA = path.join(ROOT, '07-statistics/agent-blind-tables-current-recompute-sol');
const OUT = path.join(ROOT, '09-delivery/agent-review-20261010');
const mode = process.argv[2] || 'reviews';
const SUPPORT = path.join(ROOT, mode === 'human-review' ? 'logs/human-feedback-review-delivery' : mode === 'targeted-human-review' ? 'logs/targeted-human-followup-review-delivery' : 'logs/agent-review-delivery');
await fs.mkdir(OUT, { recursive: true });
await fs.mkdir(SUPPORT, { recursive: true });
const review = JSON.parse(await fs.readFile(path.join(DATA, 'review-rows.json'), 'utf8'));
const metrics = JSON.parse(await fs.readFile(path.join(DATA, 'metrics-all-available.json'), 'utf8'));
const dimensions = ['S', 'E', 'Ec', 'I', 'F'];
const dimNames = { S: 'S 安全性', E: 'E 有效性', Ec: 'Ec 经济性', I: 'I 创新性', F: 'F 公平性' };
const deps = { NMPA: '药监局', NHSA: '医保局', NHC: '卫健委' };
const versions = { pilot02: '补材判读 pilot02', coverage01: '覆盖判读 coverage01', 'renewal-rejudge-v11': '续约补材重判 v11', 'source-impact4-v12': '源材料修正重判 v12' };
const col = n => { let s = ''; for (let x = n + 1; x; x = Math.floor((x - 1) / 26)) s = String.fromCharCode(65 + (x - 1) % 26) + s; return s; };
const text = x => typeof x === 'string' ? x : x == null ? '' : JSON.stringify(x);
const label = x => x === null ? '待定' : x;
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fittedHeight = (s, width) => Math.max(30, 12 + text(s).split('\n').reduce((n, line) => n + Math.max(1, Math.ceil(Array.from(line).length / (width * 0.65))), 0) * 13);
const expectedHashes = { 'review-rows.json': 'b2d0d2c414f04e4241bb1b355f3563b84eaab6274a22a92fe360dc14e36a677e' };
for (const [file, hash] of Object.entries(expectedHashes)) {
  if (sha(await fs.readFile(path.join(DATA, file))) !== hash) throw Error(`Input hash mismatch: ${file}`);
}
if (review.records.length !== 77 || review.long_rows.length !== 385) throw Error('Unexpected review sample size');

function setup(sheet, title, note, headers, rows, widths, headerRow = 6) {
  const lastCol = col(headers.length - 1), end = headerRow + rows.length;
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}${end}`).format.font = { name: 'Arial', size: 10, color: '#243044' };
  sheet.getRange(`A1:${lastCol}${end}`).format.verticalAlignment = 'center';
  sheet.getRange('A2').values = [[title]];
  sheet.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true, color: '#243044' };
  sheet.getRange('A4').values = [[note]];
  sheet.getRange('A4').format.font = { name: 'Arial', size: 10, italic: true, color: '#526072' };
  sheet.getRange(`A${headerRow}:${lastCol}${headerRow}`).values = [headers];
  const head = sheet.getRange(`A${headerRow}:${lastCol}${headerRow}`);
  head.format.fill = '#334A65';
  head.format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
  head.format.horizontalAlignment = 'center';
  head.format.rowHeight = 30;
  head.format.wrapText = true;
  if (rows.length) sheet.getRange(`A${headerRow + 1}:${lastCol}${end}`).values = rows;
  sheet.getRange(`A${headerRow + 1}:${lastCol}${end}`).format.rowHeight = 30;
  widths.forEach((w, i) => sheet.getRange(`${col(i)}${headerRow}:${col(i)}${end}`).format.columnWidth = w);
  sheet.freezePanes.freezeRows(headerRow);
  return end;
}

async function verifyAndSave(wb, filename, views, extraCheck) {
  wb.recalculate();
  if (extraCheck) extraCheck();
  const inspect = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A', options: { useRegex: true, maxResults: 30 }, maxChars: 4000 });
  await fs.writeFile(path.join(SUPPORT, `${filename}.inspect.ndjson`), inspect.ndjson);
  if (/"value":"#(?:REF!|DIV\/0!|VALUE!|NAME\?|NUM!|N\/A)/.test(inspect.ndjson)) throw Error('Formula error found');
  for (const [sheetName, range, slug] of views) {
    const preview = await wb.render({ sheetName, range, scale: 1.2, format: 'png' });
    await fs.writeFile(path.join(SUPPORT, `${filename}-${slug}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  const output = await SpreadsheetFile.exportXlsx(wb);
  const target = path.join(OUT, filename);
  await output.save(target);
  const raw = await fs.readFile(target);
  try { await fs.rename(`${target}.inspect.ndjson`, path.join(SUPPORT, `${filename}.export-inspect.ndjson`)); }
  catch (err) { if (err.code !== 'ENOENT') throw err; }
  console.log(JSON.stringify({ output: target, bytes: raw.length, sha256: sha(raw), views: views.map(x => x[0]) }));
}

async function createReview(coder) {
  const wb = Workbook.create();
  const main = wb.worksheets.add('编码表');
  const source = wb.worksheets.add('原文语境');
  main.tabColor = '#334A65';
  const sourceRows = [], sourceStarts = new Map();
  const sourceKindNames = { current: '当前条款', paragraph: '正文段落', heading: '标题', table: '表格', structural_relation: '结构关联', ordered_list: '有序列表', supplemental_group: '补充条款组', same_snapshot_source_numbered_group_geometry: '原文编号结构' };
  const addSourceBlock = (id, block, kind, locator, original, version) => {
    const chars = Array.from(original), pieces = [];
    for (let i = 0; i < chars.length; i += 1000) pieces.push(chars.slice(i, i + 1000).join(''));
    if (!pieces.length) pieces.push('');
    pieces.forEach((piece, i) => sourceRows.push([id, pieces.length > 1 ? `${block} (${i + 1}/${pieces.length})` : block, sourceKindNames[kind] || kind, locator, piece, version]));
    if (pieces.join('') !== original) throw Error('Source text changed while fitting rows');
  };
  for (const r of review.records) {
    sourceStarts.set(r.id, 7 + sourceRows.length);
    const locator = r.source.source_ref?.locator || {};
    const locText = l => [l.paragraph_id, ...(l.paragraph_ids || []), l.source_unit_id, ...(l.pages || l.physical_pages || []).map(x => `页${x}`)].filter(Boolean).join(' / ');
    addSourceBlock(r.id, '当前条款', 'current', locText(locator), r.source.current_text, text(r.source.source_version));
    for (const c of r.source.contexts) addSourceBlock(r.id, c.context_id, c.kind, locText(c.structure || c.source_ref?.locator || {}), typeof c.text === 'string' ? c.text : '[结构信息，无独立正文]\n' + JSON.stringify(c.structure || c.source_ref?.locator || {}, null, 2), c.source_document || '');
  }
  const rows = review.long_rows.map(r => {
    const record = review.records.find(x => x.id === r.id);
    const actual = r[coder].latest;
    return [r.id, deps[r.department] || r.department, dimNames[r.dimension], label(actual.value), actual.evidence.reason || '', record[coder].latest.current_text_as_read_in_that_round || r.current_text, versions[actual.round] || actual.round, null];
  });
  const end = setup(main, `${coder} 编码复核表`, '直接修改D列编码值、E列判定理由。0=不编码；1=编码；待定=无法判断。', ['条款编号', '部门', '维度', '编码值', '判定理由', '该轮判读原句', '判断版本', '完整语境位置'], rows, [24, 11, 15, 10, 66, 74, 29, 23]);
  main.getRange(`D7:E${end}`).format.fill = '#FFF2CC';
  main.getRange(`D7:D${end}`).dataValidation = { rule: { type: 'list', values: ['0', '1', '待定'] } };
  main.getRange(`D7:D${end}`).setNumberFormat('0');
  main.getRange(`D7:D${end}`).format.horizontalAlignment = 'center';
  main.getRange(`E7:G${end}`).format.wrapText = true;
  main.getRange(`E7:G${end}`).format.verticalAlignment = 'top';
  rows.forEach((row, i) => main.getRange(`A${i + 7}:H${i + 7}`).format.rowHeight = Math.min(409, Math.max(fittedHeight(row[4], 66), fittedHeight(row[5], 74), 36)));
  main.getRange(`H7:H${end}`).values = review.long_rows.map(r => [`原文语境第${sourceStarts.get(r.id)}行`]);
  main.freezePanes.freezeColumns(3);
  const sourceEnd = setup(source, `${coder}表对应原文与完整语境`, '77条、642个语境块（含结构信息）；长段按连续片段展示。6条补材重判，71条保留原判。', ['条款编号', '原文块编号', '类型', '原文位置', '完整文本或结构', '来源版本或文档'], sourceRows, [24, 31, 14, 32, 105, 32]);
  source.getRange(`E7:F${sourceEnd}`).format.wrapText = true;
  source.getRange(`E7:F${sourceEnd}`).format.verticalAlignment = 'top';
  sourceRows.forEach((row, i) => source.getRange(`A${i + 7}:F${i + 7}`).format.rowHeight = Math.min(409, fittedHeight(row[4], 105)));
  source.freezePanes.freezeColumns(1);
  await verifyAndSave(wb, `编码复核表-${coder}.xlsx`, [['编码表', 'A1:E10', '编码'], ['原文语境', 'A1:E9', '语境']], () => {
    const vals = main.getRange(`A7:H${end}`).values;
    if (vals.length !== 385) throw Error('Review rows missing');
    vals.forEach((v, i) => { if (v[3] !== label(review.long_rows[i][coder].latest.value)) throw Error('Label mismatch'); });
    if (sourceRows.length < 719) throw Error('Source blocks missing');
  });
}

const names = {
  A_B_pilot01: 'A/B 原始pilot01', A_B_pilot02: 'A/B 补材pilot02', A_B_coverage01: 'A/B 覆盖36',
  'A_B_renewal-rejudge-v11': 'A/B 续约重判2', 'A_B_source-impact4-v12': 'A/B 源修正4',
  A_B_development77_base_v11: 'A/B 基础77', A_B_latest_actual_development_composite77: 'A/B 实际修改后77',
  rule_v17_complete77_vs_AI_reference_v3: '规则77→另行裁定v3',
  native38_complete_format_subset_vs_AI_reference_v3: 'LLM38→另行裁定v3',
  native38_complete_format_subset_vs_historical_AI_reference_v2: 'LLM38→旧参照v2',
  native_partial7_saved_subset_vs_AI_reference_v3: 'LLM部分7→另行裁定v3',
  native_partial7_saved_subset_vs_historical_AI_reference_v2: 'LLM部分7→旧参照v2',
  rule17_vs_native38_implementation_agreement: '规则与LLM38相互一致',
  rule17_vs_partial7_implementation_agreement: '规则与LLM部分7相互一致',
  rule17_complete77_vs_actual_latest_A: '规则77→修改表A',
  rule17_complete77_vs_actual_latest_B: '规则77→修改表B',
  native38_saved_complete_format_subset_vs_actual_latest_A: 'LLM38→修改表A',
  native38_saved_complete_format_subset_vs_actual_latest_B: 'LLM38→修改表B',
  partial7_saved_per_record_subset_vs_actual_latest_A: 'LLM部分7→修改表A',
  partial7_saved_per_record_subset_vs_actual_latest_B: 'LLM部分7→修改表B',
};

async function createMetrics() {
  const addPath = path.join(ROOT, '07-statistics/agent-modified-table-reference-recompute-sol/metrics-addendum.json');
  const add = JSON.parse(await fs.readFile(addPath, 'utf8'));
  if (add.comparisons.length !== 6) throw Error('Expected six actual A/B reference comparisons');
  const all = [...metrics.comparisons, ...add.comparisons];
  const wb = Workbook.create();
  const summary = wb.worksheets.add('指标概览');
  const detail = wb.worksheets.add('逐维复算');
  const pending = wb.worksheets.add('待完成指标');
  summary.tabColor = '#334A65';
  const detailRows = [], rowIndex = new Map();
  for (const c of all) for (const d of dimensions) {
    const x = c.dimensions[d], q = x.four_cells;
    const rowNo = 7 + detailRows.length;
    rowIndex.set(`${c.name}|${d}`, rowNo);
    const na = Object.entries(x.metrics).filter(([,v]) => v.value === null).map(([k,v]) => `${k}: ${v.NA_reason}`).join('；');
    detailRows.push([names[c.name] || c.display_name || c.name, dimNames[d], x.assigned_N, x.saved_pair_N, null, q.a, q.b, q.c, q.d, x.left_counts['1'] || 0, x.left_counts['0'] || 0, x.right_counts['1'] || 0, x.right_counts['0'] || 0, x.left_null_N, x.right_null_N, x.left_failed_or_unfilled_N, x.right_failed_or_unfilled_N, null, null, null, null, null, null, ...Array(5).fill(c.role === 'machine_vs_reference' ? null : '不适用'), (x.difference_ids || []).join('、'), na || '—', c.version_scope_notes]);
  }
  const headers = ['比较', '维度', '分配条数', '保存配对', '可判配对', 'a / TP', 'b / FP', 'c / FN', 'd / TN', '左正例', '左负例', '右正例', '右负例', '左待定', '右待定', '左失败/未填', '右失败/未填', '可判覆盖率', 'Po', 'Pe', 'κ', '正类一致性', '负类一致性', 'Precision', 'Recall', 'F1', 'Specificity', 'NPV', '差异条款', 'NA原因', '版本说明'];
  const end = setup(detail, '全部实际保存比较的逐维复算', 'A/B四格：行=A、列=B；机器四格：行=机器、列=参照。待定与失败均单独保留。', headers, detailRows, [38, 15, ...Array(15).fill(13), ...Array(11).fill(15), 46, 55, 65]);
  detail.freezePanes.freezeColumns(2);
  detail.getRange(`C7:AB${end}`).format.horizontalAlignment = 'right';
  detail.getRange(`R7:AB${end}`).setNumberFormat('0.000');
  detail.getRange(`AC7:AE${end}`).format.wrapText = true;
  detail.getRange(`A7:AE${end}`).format.rowHeight = 58;
  for (let i = 0; i < detailRows.length; i++) {
    const r = i + 7, c = all[Math.floor(i / 5)];
    const f = {
      E: `=SUM(F${r}:I${r})`, R: `=IF(C${r}=0,"NA",E${r}/C${r})`,
      S: `=IF(E${r}=0,"NA",(F${r}+I${r})/E${r})`,
      T: `=IF(E${r}=0,"NA",((F${r}+G${r})*(F${r}+H${r})+(H${r}+I${r})*(G${r}+I${r}))/E${r}^2)`,
      U: `=IF(E${r}=0,"NA",IF(T${r}=1,"NA",(S${r}-T${r})/(1-T${r})))`,
      V: `=IF(2*F${r}+G${r}+H${r}=0,"NA",2*F${r}/(2*F${r}+G${r}+H${r}))`,
      W: `=IF(2*I${r}+G${r}+H${r}=0,"NA",2*I${r}/(2*I${r}+G${r}+H${r}))`,
    };
    if (c.role === 'machine_vs_reference') Object.assign(f, {
      X: `=IF(F${r}+G${r}=0,"NA",F${r}/(F${r}+G${r}))`,
      Y: `=IF(F${r}+H${r}=0,"NA",F${r}/(F${r}+H${r}))`,
      Z: `=IF(2*F${r}+G${r}+H${r}=0,"NA",2*F${r}/(2*F${r}+G${r}+H${r}))`,
      AA: `=IF(G${r}+I${r}=0,"NA",I${r}/(G${r}+I${r}))`,
      AB: `=IF(H${r}+I${r}=0,"NA",I${r}/(H${r}+I${r}))`,
    });
    for (const [k,v] of Object.entries(f)) detail.getRange(`${k}${r}`).formulas = [[v]];
  }
  const latest = metrics.comparisons.find(c => c.name === 'A_B_latest_actual_development_composite77');
  const mainComps = [latest, ...add.comparisons];
  const summaryRows = [], summaryMeta = [];
  for (const c of mainComps) for (const d of dimensions) {
    const x = c.dimensions[d];
    summaryRows.push([names[c.name] || c.display_name || c.name, dimNames[d], x.assigned_N, x.saved_pair_N, null, null, null, null, null, null, c.name.includes('partial') ? '部分结果；不替代完整批次' : c.role === 'AI_A_vs_AI_B' ? '修改后一致性；开发材料' : '按实际A/B表参照；开发材料']);
    summaryMeta.push({ c, d, detailRow: rowIndex.get(`${c.name}|${d}`) });
  }
  const sEnd = setup(summary, '按Agent修改表计算的当前指标', '主表使用A/B实际修改值；另行裁定v3与历史比较保留在“逐维复算”。项目点值要求≥0.80。', ['比较', '维度', '分配条数', '保存配对', '可判配对', 'κ', 'Precision', 'Recall', 'F1', '点值状态', '结果范围'], summaryRows, [38, 15, 13, 13, 13, 13, 13, 13, 13, 24, 42]);
  summary.getRange(`F7:I${sEnd}`).setNumberFormat('0.000');
  summary.getRange(`C7:I${sEnd}`).format.horizontalAlignment = 'right';
  summary.getRange(`A7:K${sEnd}`).format.rowHeight = 34;
  for (let i = 0; i < summaryRows.length; i++) {
    const r = i + 7, m = summaryMeta[i], dr = m.detailRow;
    for (const [k,v] of Object.entries({ E: 'E', F: 'U', G: 'X', H: 'Y', I: 'Z' })) summary.getRange(`${k}${r}`).formulas = [[`='逐维复算'!${v}${dr}`]];
    const status = m.c.role === 'AI_A_vs_AI_B'
      ? `=IF(ISNUMBER(F${r}),IF(F${r}>=0.8,"κ点值达标","κ点值未达标"),"NA：不可据此验收")`
      : `=IF(COUNT(F${r}:I${r})<4,"NA：有指标未定义",IF(MIN(F${r}:I${r})>=0.8,"四项点值达标","有点值未达标"))`;
    summary.getRange(`J${r}`).formulas = [[status]];
  }
  summary.getRange(`F7:I${sEnd}`).conditionalFormats.add('cellIs', { operator: 'lessThan', formula: 0.8, format: { fill: '#FDE9E7', font: { color: '#A12920', bold: true } } });
  const missingLabels = ['800条A/B、分类及加权区间', '开发样本的总体95%区间', '完整77条LLM分类指标', 'LLM同版本重复稳定性', '规则重复稳定性', '4481条注意力结构与稳健性', '语义正确性与实际真人复核'];
  const pendingRows = metrics.uncomputed_or_NA.map((x,i) => [missingLabels[i], i === 1 ? '不适用' : i === 6 ? '需原文复核' : '尚未完成', x.reason]);
  setup(pending, '尚不能计算或不适用的指标', 'NA不是1；开发材料不作为总体抽样检验。本轮完成已有值复算，未新增语义判读。', ['项目', '状态', '依据或缺少的材料'], pendingRows, [43, 21, 106]);
  pending.getRange('A7:C13').format.wrapText = true;
  pending.getRange('A7:C13').format.rowHeight = 70;
  await verifyAndSave(wb, '指标完整复算.xlsx', [['指标概览', 'A1:J13', '概览'], ['逐维复算', 'A1:I12', '四格'], ['待完成指标', 'A1:C10', '待完成']], () => {
    const checkCols = { Po: 'S', Pe: 'T', kappa: 'U', Ppos: 'V', Pneg: 'W', precision: 'X', recall: 'Y', F1: 'Z', specificity: 'AA', NPV: 'AB' };
    for (const c of all) for (const d of dimensions) {
      const r = rowIndex.get(`${c.name}|${d}`);
      for (const [key, value] of Object.entries(c.dimensions[d].metrics)) {
        if (!checkCols[key]) continue;
        const actual = detail.getRange(`${checkCols[key]}${r}`).values[0][0];
        if (value.value === null ? actual !== 'NA' : typeof actual !== 'number' || Math.abs(actual - value.value) > 1e-10) throw Error(`Metric mismatch ${c.name} ${d} ${key}: ${actual} != ${value.value}`);
      }
    }
  });
}

async function applyHumanReview() {
  const supplementPath = path.join(ROOT, '04-calibration/human-review-evidence-supplements-sol/supplements.json');
  const supplementBytes = await fs.readFile(supplementPath);
  if (sha(supplementBytes) !== '11243a9498092015dde1d1ad18bf66fa887067da54f062b5c00f4231e1d44da9') throw Error('Supplement seal input changed');
  const supplement = JSON.parse(supplementBytes);
  const updated = JSON.parse(await fs.readFile(path.join(ROOT, '07-statistics/human-feedback-current-recompute-sol/metrics.json'), 'utf8'));
  if (updated.comparisons.length !== 6) throw Error('Expected six updated comparisons');
  const extraSources = [];
  for (const id of ['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045']) {
    const record = review.records.find(x => x.id === id);
    const binding = record.AI_reference.saved_row.root_adjudication_v3.case_exactly_from_root.material_packet;
    const bytes = await fs.readFile(binding.path);
    if (sha(bytes) !== binding.sha256) throw Error('Pending source packet changed');
    const packet = JSON.parse(bytes);
    for (const resource of packet.source_bundle.source_full_text_resources) {
      if (sha(Buffer.from(resource.text, 'utf8')) !== resource.text_utf8_sha256) throw Error('Full source text hash mismatch');
      extraSources.push({ id, block: resource.source_resource_id, kind: '完整补充原文', locator: '原文第' + resource.locator.physical_line_range_1based_inclusive.join('—') + '行', text: resource.text, source: path.basename(resource.locator.snapshot_absolute_path) + '；' + resource.source_version_id });
    }
  }
  const receipt = { created_at_utc: new Date().toISOString(), role: 'Apply explicit user-provided human review to current AI review tables; not new independent human first coding', label_changes: [{ id: 'RECODE25-01423', dimension: 'S', cell: 'D277', old: 0, value: 1 }, { id: 'RECODE25-04333', dimension: 'S', cell: 'D367', old: 1, value: 0 }], preserved_pending: ['RECODE25-03415 E', 'RECODE25-00036 S', 'RECODE25-00038 S', 'RECODE25-00045 S'], output_files: [] };
  for (const coder of ['A', 'B']) {
    const filename = `编码复核表-${coder}.xlsx`;
    const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(OUT, filename)));
    const main = wb.worksheets.getItem('编码表'), source = wb.worksheets.getItem('原文语境');
    const before = main.getRange('A7:H391').values;
    const sourcesBefore = source.getRange('A7:F764').values;
    const sourceRows = [], starts = new Map();
    const append = ({ id, block, kind, locator, text: original, source: origin }) => {
      if (!starts.has(id)) starts.set(id, 765 + sourceRows.length);
      const chars = Array.from(original), chunks = [];
      for (let i = 0; i < chars.length; i += 500) chunks.push(chars.slice(i, i + 500).join(''));
      chunks.forEach((piece, i) => sourceRows.push([id, chunks.length > 1 ? `${block} (${i + 1}/${chunks.length})` : block, kind, locator, piece, origin]));
      if (chunks.join('') !== original) throw Error('Supplement text changed');
    };
    // The normalized append records are read from a sealed source-only agent output.
    for (const entry of supplement.append_rows) {
      const resource = supplement.resources.find(x => (x.resource_id || x.id || x.supplement_id) === (entry.resource_id || entry.supplement_id));
      if (!resource) throw Error('Supplement resource binding missing: ' + JSON.stringify(entry));
      if (entry.full_text !== resource.full_continuous_text || sha(Buffer.from(entry.full_text, 'utf8')) !== entry.text_sha256) throw Error('Supplement exact text mismatch');
      if (sha(await fs.readFile(entry.source_file_path)) !== entry.source_file_sha256) throw Error('Supplement source changed');
      const loc = entry.source_locator;
      const conciseLocator = loc.section_and_paragraph || `${loc.sections}；原文第${loc.txt_line_start_1based}—${loc.txt_line_end_inclusive_1based}行`;
      append({ id: entry.record_id, block: entry.resource_id, kind: '原判使用的完整补材', locator: conciseLocator, text: resource.full_continuous_text, source: entry.source_title + '\n源文件SHA256：' + entry.source_file_sha256 });
    }
    extraSources.forEach(append);
    const sourceEnd = 764 + sourceRows.length;
    for (let r = 765; r <= sourceEnd; r++) source.getRange(`A${r}:F${r}`).copyFrom(source.getRange('A764:F764'), 'all');
    source.getRange(`A765:F${sourceEnd}`).values = sourceRows;
    source.getRange(`D765:F${sourceEnd}`).format.wrapText = true;
    source.getRange(`D765:F${sourceEnd}`).format.verticalAlignment = 'top';
    sourceRows.forEach((row, i) => source.getRange(`A${i + 765}:F${i + 765}`).format.rowHeight = Math.min(409, Math.max(160, fittedHeight(row[4], 105) * 1.7)));
    source.getRange('A4').values = [['77条原材料及原判补材完整展示。末尾新增补材按条款编号检索，长段连续分行。']];
    main.getRange('A4').values = [['真人直接修改D列编码值、E列理由。先读固定手册和原文语境，无法判断填待定。']];
    for (const change of receipt.label_changes) {
      const row = Number(change.cell.slice(1));
      if (main.getRange(`A${row}`).values[0][0] !== change.id || main.getRange(change.cell).values[0][0] !== change.old) throw Error('Original change target mismatch');
      main.getRange(change.cell).values = [[change.value]];
      main.getRange(`E${row}`).values = [[change.id.endsWith('01423') ? '按真人复核意见改为1。当前表行同时规定6年基础保护及4年例外，应分别判断；不能仅按例外排除基础安排。6年基础保护所援引的安全性、有效性及质量数据要求提供安全性证据。记录安全性证据要求，不表示药品已经安全，也不把数据保护解释为数据安全。' : '按真人复核意见改为0。当前第一条仅说明制定处方审核规范旨在保障患者用药安全，属于一般宗旨；没有提出实质药物风险、评估证据或具体安全控制要求，依现行手册不编码安全性。不得借后续条款的实质内容反向补入本条。']];
      main.getRange(`G${row}`).values = [['真人复核意见已应用 20261010']];
      main.getRange(`A${row}:H${row}`).format.rowHeight = Math.min(409, fittedHeight(main.getRange(`E${row}`).values[0][0], 66));
    }
    const pendingE = 158;
    main.getRange(`E${pendingE}`).values = [[text(before[pendingE - 7][4]) + '\n待真人核定：当前“提升整体健康水平”是否超出一般宗旨、构成实质治疗获益，须按手册统一边界。暂保留原值1；“减少用药差错”支持安全性，不自动支持有效性。']];
    main.getRange(`G${pendingE}`).values = [['原判保留；有效性边界待真人核定']];
    for (const [i, row] of before.entries()) {
      const id = row[0], dim = dimensions[i % 5], r = i + 7;
      if (starts.has(id)) main.getRange(`H${r}`).values = [[text(row[7]) + `；补材第${starts.get(id)}行起`]];
      if (['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045'].includes(id) && dim === 'S') {
        main.getRange(`E${r}`).values = [[text(row[4]) + '\n待真人核定：现已补齐完整纳入条件及终止情形，含安全性优势/重大安全性问题原文。原理由基于较少材料，暂保留原值0；请判断当前条款对具名标准的援引能否承载安全性编码。']];
        main.getRange(`G${r}`).values = [['原判保留；补齐标准待真人核定']];
      }
      if ((['RECODE25-01729', 'RECODE25-02233', 'RECODE25-02269'].includes(id) && dim === 'I') || (id === 'RECODE25-04915' && dim === 'F')) main.getRange(`E${r}`).values = [[text(row[4]) + '\n原判使用的完整补充材料已收入原文语境，编码值维持原值。请结合补材核验本条引用边界及判定理由。']];
      if (starts.has(id) || r === pendingE) main.getRange(`A${r}:H${r}`).format.rowHeight = Math.min(409, Math.max(fittedHeight(main.getRange(`E${r}`).values[0][0], 66), fittedHeight(row[5], 74), 36));
    }
    const supplementIds = [...starts.keys()];
    await verifyAndSave(wb, filename, [['编码表', 'A276:E278', '改值'], ['编码表', 'A157:E159', '待核定'], ['原文语境', 'A765:F767', '补材']], () => {
      const after = main.getRange('A7:H391').values;
      if (JSON.stringify(source.getRange('A7:F764').values) !== JSON.stringify(sourcesBefore)) throw Error('Original sources changed');
      after.forEach((row, i) => { const expected = receipt.label_changes.find(x => x.id === row[0] && before[i][2] === dimNames.S); if (row[3] !== (expected ? expected.value : before[i][3])) throw Error('Unrequested label change'); });
    });
    receipt.output_files.push({ filename, appended_rows_N: sourceRows.length, supplemental_ids: supplementIds, sha256: sha(await fs.readFile(path.join(OUT, filename))) });
  }
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(OUT, '指标完整复算.xlsx')));
  const detail = wb.worksheets.getItem('逐维复算'), summary = wb.worksheets.getItem('指标概览'), pending = wb.worksheets.getItem('待完成指标');
  const oldAdd = JSON.parse(await fs.readFile(path.join(ROOT, '07-statistics/agent-modified-table-reference-recompute-sol/metrics-addendum.json'), 'utf8'));
  for (const c of updated.comparisons) {
    const index = oldAdd.comparisons.findIndex(x => x.name === c.name);
    if (index < 0) throw Error('Unknown updated comparison');
    for (const [i, d] of dimensions.entries()) {
      const r = 77 + index * 5 + i, x = c.dimensions[d], q = x.four_cells;
      detail.getRange(`F${r}:M${r}`).values = [[q.a, q.b, q.c, q.d, x.left_counts['1'] || 0, x.left_counts['0'] || 0, x.right_counts['1'] || 0, x.right_counts['0'] || 0]];
      detail.getRange(`AC${r}`).values = [[x.difference_ids.join('、')]];
      detail.getRange(`AE${r}`).values = [['按当前复核表：2处真人明确改值已应用，其余保留原AI判读；03415有效性及3条安全性待核定。']];
      summary.getRange(`K${12 + index * 5 + i}`).values = [[c.name.includes('partial') ? '部分结果；当前复核表参照' : '当前复核表参照；真人核验未完成']];
    }
  }
  summary.getRange('A2').values = [['按当前复核表计算的指标']];
  summary.getRange('A4').values = [['2处真人明确改值已应用。其余原判及待定边界仍需核验。历史比较保留于逐维复算及原表备份。']];
  summary.getRange('K7:K11').values = Array.from({ length: 5 }, () => ['修改后表间一致性；真人核验未完成']);
  pending.getRange('B13').values = [['部分复核意见已应用']];
  pending.getRange('C13').values = [['2处安全性改值已应用，4条完整依据已补齐。03415有效性及00036/00038/00045安全性待核定。完整77条真人核验未完成，正式800条独立真人初判未完成。']];
  const latestABIndex = metrics.comparisons.findIndex(c => c.name === 'A_B_latest_actual_development_composite77');
  detail.getRange(`AE${7 + latestABIndex * 5}:AE${11 + latestABIndex * 5}`).values = Array.from({ length: 5 }, () => ['原AI判读，经2处真人明确改值共同修改；κ表示修改后表间一致性。']);
  await verifyAndSave(wb, '指标完整复算.xlsx', [['指标概览', 'A11:K13', '新指标'], ['待完成指标', 'A12:C13', '待完成']], () => {
    for (const c of updated.comparisons) {
      const idx = oldAdd.comparisons.findIndex(x => x.name === c.name);
      for (const [i, d] of dimensions.entries()) for (const [k, column] of Object.entries({ Po: 'S', Pe: 'T', kappa: 'U', Ppos: 'V', Pneg: 'W', precision: 'X', recall: 'Y', F1: 'Z', specificity: 'AA', NPV: 'AB' })) {
        const expected = c.dimensions[d].metrics[k].value, actual = detail.getRange(`${column}${77 + idx * 5 + i}`).values[0][0];
        if (expected === null ? actual !== 'NA' : typeof actual !== 'number' || Math.abs(expected - actual) > 1e-10) throw Error(`Updated metric mismatch ${c.name} ${d} ${k}`);
      }
    }
  });
  receipt.output_files.push({ filename: '指标完整复算.xlsx', sha256: sha(await fs.readFile(path.join(OUT, '指标完整复算.xlsx'))) });
  await fs.writeFile(path.join(SUPPORT, 'applied-human-feedback-receipt.json'), JSON.stringify(receipt, null, 2));
}

async function applyTargetedHumanReview() {
  const baseline = path.join(ROOT, '00-baseline/20261010-pre-targeted-human-followup-edits');
  const manifest = JSON.parse(await fs.readFile(path.join(baseline, 'seal.json'), 'utf8'));
  const decisionPath = path.join(ROOT, 'logs/user-targeted-human-followup-received-20261010.json');
  const decisionsBytes = await fs.readFile(decisionPath);
  if (sha(decisionsBytes) !== '048cd9d5db25422687efe302f456d1434f5b10679d8ab30cdcfbd29aff89d28e') throw Error('Human decisions changed');
  const decisions = JSON.parse(decisionsBytes);
  const updatedPath = path.join(ROOT, '07-statistics/human-targeted-followup-recompute-sol/metrics.json');
  const updatedBytes = await fs.readFile(updatedPath);
  if (sha(updatedBytes) !== 'cb0eab8e0beef7a648a9742de6f246e87ace919839145d50c5f6b927e95d32ed') throw Error('Targeted metrics seal changed');
  const updated = JSON.parse(updatedBytes);
  if (updated.comparisons.length !== 6) throw Error('Expected six comparisons');
  const receipt = { created_at_utc: new Date().toISOString(), role: 'User-confirmed human posthoc review of four targeted cases; not independent human first coding', human_decisions_received: true, label_changes: decisions.label_changes, current_pending_cases: [], source_reception_sha256: sha(decisionsBytes), metric_json_sha256: sha(updatedBytes), output_files: [] };
  for (const coder of ['A', 'B']) {
    const filename = `编码复核表-${coder}.xlsx`;
    const entry = manifest.files.find(x => path.basename(x.path) === filename);
    if (sha(await fs.readFile(path.join(OUT, filename))) !== entry.sha256) throw Error('Delivery changed after backup');
    const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(OUT, filename)));
    const main = wb.worksheets.getItem('编码表'), source = wb.worksheets.getItem('原文语境');
    const before = main.getRange('A7:H391').values;
    const sourcesBefore = JSON.stringify(source.getRange('A1:F848').values);
    for (const change of decisions.label_changes) {
      const row = Number(change.cell.slice(1));
      if (main.getRange(`A${row}`).values[0][0] !== change.id || main.getRange(`C${row}`).values[0][0] !== dimNames[change.dimension] || main.getRange(change.cell).values[0][0] !== change.old) throw Error('Target mismatch');
      main.getRange(change.cell).values = [[change.value]];
      main.getRange(`E${row}`).values = [[change.reason]];
      main.getRange(`G${row}`).values = [['真人补充复核结论已应用 20261010']];
      main.getRange(`A${row}:H${row}`).format.rowHeight = Math.min(409, Math.max(fittedHeight(change.reason, 66), fittedHeight(before[row - 7][5], 74), 36));
    }
    main.getRange('A4').values = [['本轮真人复核及四项补核结论已应用。D列为编码值，E列为核定理由；完整材料见H列所指原文语境。']];
    await verifyAndSave(wb, filename, [['编码表', 'A12:E12', '00036'], ['编码表', 'A17:E17', '00038'], ['编码表', 'A22:E22', '00045'], ['编码表', 'A158:E158', '03415']], () => {
      if (JSON.stringify(source.getRange('A1:F848').values) !== sourcesBefore) throw Error('Sources changed');
      const after = main.getRange('A7:H391').values;
      after.forEach((row, i) => {
        const change = decisions.label_changes.find(x => Number(x.cell.slice(1)) === i + 7);
        row.forEach((value, colIndex) => {
          const expected = change && colIndex === 3 ? change.value : change && colIndex === 4 ? change.reason : change && colIndex === 6 ? '真人补充复核结论已应用 20261010' : before[i][colIndex];
          if (JSON.stringify(value) !== JSON.stringify(expected)) throw Error(`Unrequested change ${coder} ${i + 7} ${colIndex}`);
        });
      });
    });
    receipt.output_files.push({ filename, sha256: sha(await fs.readFile(path.join(OUT, filename))) });
  }
  const filename = '指标完整复算.xlsx';
  const entry = manifest.files.find(x => path.basename(x.path) === filename);
  if (sha(await fs.readFile(path.join(OUT, filename))) !== entry.sha256) throw Error('Metric delivery changed');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(OUT, filename)));
  const detail = wb.worksheets.getItem('逐维复算'), summary = wb.worksheets.getItem('指标概览'), pending = wb.worksheets.getItem('待完成指标');
  const oldAdd = JSON.parse(await fs.readFile(path.join(ROOT, '07-statistics/agent-modified-table-reference-recompute-sol/metrics-addendum.json'), 'utf8'));
  const setCounts = (r, x) => {
    const q = x.four_cells;
    detail.getRange(`F${r}:M${r}`).values = [[q.a, q.b, q.c, q.d, x.left_counts['1'] || 0, x.left_counts['0'] || 0, x.right_counts['1'] || 0, x.right_counts['0'] || 0]];
    detail.getRange(`AC${r}`).values = [[x.difference_ids.join('、')]];
  };
  for (const c of updated.comparisons) {
    const idx = oldAdd.comparisons.findIndex(x => x.name === c.name);
    if (idx < 0) throw Error('Unknown comparison');
    for (const [i, d] of dimensions.entries()) {
      const r = 77 + idx * 5 + i;
      setCounts(r, c.dimensions[d]);
      detail.getRange(`AE${r}`).values = [['本轮真人复核及四项补核结论已应用；机器原输出保持原值，当前77条用于开发诊断。']];
      summary.getRange(`K${12 + idx * 5 + i}`).values = [[c.name.includes('partial') ? '仅7条部分输出；复核后参照' : c.name.includes('native38') ? '仅38条已存输出；复核后参照' : '77条开发诊断；复核后参照']];
    }
  }
  const latestABIndex = metrics.comparisons.findIndex(c => c.name === 'A_B_latest_actual_development_composite77');
  if (latestABIndex < 0) throw Error('Missing A/B comparison');
  for (const [i, d] of dimensions.entries()) {
    setCounts(7 + latestABIndex * 5 + i, updated.A_B_comparison.dimensions[d]);
    detail.getRange(`AE${7 + latestABIndex * 5 + i}`).values = [['AI预填表经相同真人事后意见修正；κ为修改后表间一致性，未替代独立真人初判信度。']];
  }
  summary.getRange('A2').values = [['按真人复核后表值计算的指标']];
  summary.getRange('A4').values = [['两轮共6处改值及完整补材已保存。机器原输出未更改；77条用于开发诊断，38条/7条部分输出按实际分母计算。']];
  summary.getRange('K7:K11').values = Array.from({ length: 5 }, () => ['真人意见同步修正后表间一致性']);
  pending.getRange('B13').values = [['本轮复核与四项补核已应用']];
  pending.getRange('C13').values = [['此前2处安全性改值、4条补材及本次4项补核已保存，本轮已列出的4项分歧已解决。正式800条独立真人初判及机器检验尚未完成。']];
  await verifyAndSave(wb, filename, [['指标概览', 'A12:K13', '规则'], ['指标概览', 'A22:K23', 'LLM'], ['待完成指标', 'A13:C13', '复核状态']], () => {
    for (const c of updated.comparisons) {
      const idx = oldAdd.comparisons.findIndex(x => x.name === c.name);
      for (const [i, d] of dimensions.entries()) for (const [k, column] of Object.entries({ Po: 'S', Pe: 'T', kappa: 'U', Ppos: 'V', Pneg: 'W', precision: 'X', recall: 'Y', F1: 'Z', specificity: 'AA', NPV: 'AB' })) {
        const expected = c.dimensions[d].metrics[k].value, actual = detail.getRange(`${column}${77 + idx * 5 + i}`).values[0][0];
        if (expected === null ? actual !== 'NA' : typeof actual !== 'number' || Math.abs(expected - actual) > 1e-10) throw Error(`Metric mismatch ${c.name} ${d} ${k}`);
      }
    }
  });
  receipt.output_files.push({ filename, sha256: sha(await fs.readFile(path.join(OUT, filename))) });
  await fs.writeFile(path.join(SUPPORT, 'applied-targeted-human-followup-receipt.json'), JSON.stringify(receipt, null, 2));
}

if (mode === 'targeted-human-review') await applyTargetedHumanReview();
else if (mode === 'human-review') await applyHumanReview();
else if (mode === 'reviews') {
  await createReview('A');
  await createReview('B');
  await fs.writeFile(path.join(SUPPORT, 'original-delivered-labels.json'), JSON.stringify({ created_at_utc: new Date().toISOString(), records: review.long_rows.map(r => ({ id: r.id, dimension: r.dimension, A: r.A.latest.value, B: r.B.latest.value, A_reason: r.A.latest.evidence.reason, B_reason: r.B.latest.evidence.reason })), actual_human_review_completed: false, user_edit_workflow: 'Edit the existing coding value and reason cells directly; no extra human review columns' }, null, 2));
} else if (mode === 'metrics') await createMetrics();
else throw Error(`Unknown mode ${mode}`);
