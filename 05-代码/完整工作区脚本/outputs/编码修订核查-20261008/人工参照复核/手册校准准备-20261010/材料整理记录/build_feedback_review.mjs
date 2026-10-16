import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const admin = path.dirname(fileURLToPath(import.meta.url));
const cal = path.dirname(admin);
const proxy = path.join(cal, '代理试填-20261010');
const out = path.join(proxy, '复核反馈处理-20261010');
const payload = JSON.parse(await fs.readFile(path.join(admin, '无答案校准内容.json'), 'utf8'));
const review = JSON.parse(await fs.readFile(path.join(out, '复核处理记录.json'), 'utf8'));
const byId = new Map(payload.units.map(u => [u.material_id, u]));
const dims = ['S', 'E', 'Ec', 'I', 'F'];
const font = 'Heiti SC';
const previews = path.join(out, 'previews');
await fs.mkdir(previews, { recursive: true });

function lines(text, width) {
  return String(text ?? '').split('\n').reduce((n, t) => n + Math.max(1, Math.ceil(Array.from(t).length / (width * 0.46))), 0);
}
function rowHeight(values, widths, min = 48) {
  const height = Math.max(min, Math.max(...values.map((v, i) => lines(v, widths[i]))) * 17 + 12);
  if (height > 409) throw new Error(`内容超过可读行高：${height}`);
  return height;
}
function formatNewSheet(sheet, headers, widths, bodyRows) {
  sheet.showGridLines = false;
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}5`).values = [headers];
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}${bodyRows + 5}`).format.font = { name: font, size: 11, color: '#18202A' };
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}${bodyRows + 5}`).format.wrapText = true;
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}${bodyRows + 5}`).format.verticalAlignment = 'top';
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}5`).format.fill = '#243B53';
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}5`).format.font = { name: font, size: 11, bold: true, color: '#FFFFFF' };
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}5`).format.rowHeight = 35;
  sheet.getRange(`A5:${String.fromCharCode(64 + headers.length)}5`).format.horizontalAlignment = 'center';
  for (let i = 0; i < widths.length; i++) sheet.getRange(`${String.fromCharCode(65+i)}1`).format.columnWidth = widths[i];
  sheet.getRange('A2').format.font = { name: font, size: 15, bold: true, color: '#18202A' };
  sheet.getRange('A3').format.font = { name: font, size: 11, color: '#18202A' };
  sheet.freezePanes.freezeRows(5);
  sheet.freezePanes.freezeColumns(2);
}

const log = {};
for (const coder of ['A', 'B']) {
  const data = review.workbooks[coder];
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(proxy, `代理试填-${coder}（供真人复核）.xlsx`)));
  const main = wb.worksheets.getItem('填写');
  const guide = wb.worksheets.getItem('填写说明');
  const record = wb.worksheets.add('复核记录');
  const evidence = wb.worksheets.add('引文依据');
  const reviewRows = [];
  const evidenceRows = [];
  const lookup = new Map();
  for (let i = 0; i < data.rows.length; i++) {
    const r = data.rows[i];
    const u = byId.get(r.material_id);
    const start = evidenceRows.length + 6;
    for (let j = 0; j < r.evidence_records.length; j++) {
      const ev = r.evidence_records[j];
      let source;
      if (ev.scope === 'current') {
        source = `${u.source_name}\n${u.source_locator}\n页码：${(u.pages ?? []).join('、')}`;
      } else {
        const d = u.context_descriptors[ev.context_index];
        source = `${d.source_name}\n${d.source_locator}\n页码：${(d.pages ?? []).join('、')}\n材料包语境序号：${ev.context_index + 1}`;
      }
      evidenceRows.push([r.material_id, r.dimension_name, j + 1, ev.scope === 'current' ? '当前句段' : '必要语境', ev.quote, source, ev.connection]);
    }
    const end = evidenceRows.length + 5;
    const pointer = start === end ? `引文依据第${start}行` : `引文依据第${start}—${end}行`;
    reviewRows.push([r.material_id, r.dimension_name, r.original_label, r.user_direction, r.state, r.feedback_reason ?? '本次未获该维新的真人裁定', r.reason, pointer, null]);
    lookup.set(`${r.material_id}/${r.dimension}`, { ...r, pointer, reviewRow: i + 6 });
  }
  formatNewSheet(record, ['材料编号', '维度', '原代理初判', '用户复核方向', '截至本次生成的状态', '用户复核依据', '补写判定理由', '完整引文位置', '实际复核补充'], [16, 13, 13, 15, 29, 58, 84, 31, 70], reviewRows.length);
  record.getRange('A2').values = [[`校准解释复核记录（代理${coder}）`]];
  record.getRange('A3').values = [['原初判、用户意见和解释补写分别记录；有倾向或缺依据的标签在“填写”中留空供裁定。']];
  record.getRange(`A6:I${reviewRows.length + 5}`).values = reviewRows;
  record.getRange(`C6:D${reviewRows.length + 5}`).setNumberFormat('0');
  record.getRange(`I6:I${reviewRows.length + 5}`).format.fill = '#FFF8E3';
  const rt = record.tables.add(`A5:I${reviewRows.length + 5}`, true, `ReviewRecords${coder}`);
  rt.style = 'TableStyleMedium2';
  for (let i = 0; i < reviewRows.length; i++) record.getRange(`A${i+6}:I${i+6}`).format.rowHeight = rowHeight(reviewRows[i], [16,13,13,15,29,58,84,31,70], 70);

  formatNewSheet(evidence, ['材料编号', '维度', '引文序号', '证据作用域', '完整有意义引文', '来源与原文位置', '用于当前判断的联系'], [16,13,13,18,110,68,80], evidenceRows.length);
  evidence.getRange('A2').values = [[`校准判定引文依据（代理${coder}）`]];
  evidence.getRange('A3').values = [['引文保留条件、否定和对象限定；必要语境须说明如何补足当前命题。']];
  evidence.getRange(`A6:G${evidenceRows.length + 5}`).values = evidenceRows;
  evidence.getRange(`C6:C${evidenceRows.length + 5}`).setNumberFormat('0');
  const et = evidence.tables.add(`A5:G${evidenceRows.length + 5}`, true, `ReviewEvidence${coder}`);
  et.style = 'TableStyleMedium2';
  for (let i = 0; i < evidenceRows.length; i++) evidence.getRange(`A${i+6}:G${i+6}`).format.rowHeight = rowHeight(evidenceRows[i], [16,13,13,18,110,68,80], 75);

  const matrix = payload.units.map(u => {
    const rs = dims.map(d => lookup.get(`${u.material_id}/${d}`));
    const notes = rs.filter(r => r.feedback_reason).map(r => `${r.dimension_name}：${r.state}；${r.user_direction == null ? '不强制定0/1' : `复核方向${r.user_direction}`}。`);
    return [
      ...rs.map(r => r.working_label),
      ...rs.map(r => `${r.reason}\n完整引文：${r.pointer}。\n处理状态及原初判：复核记录第${r.reviewRow}行。`),
      notes.length ? notes.join('\n') : null,
    ];
  });
  main.getRange('C6:M45').values = matrix;
  main.getRange('A2').values = [[`校准复核工作表（代理${coder}，供真人裁定）`]];
  main.getRange('A3').values = [['B12经济性已按用户明确复核改0；倾向或缺依据项留空，原初判与完整证据分别记录。其余标签仍为代理建议。']];
  for (let i = 0; i < matrix.length; i++) {
    const texts = [main.getRange(`B${i+6}`).values[0][0], ...matrix[i].slice(5,10), matrix[i][10]];
    main.getRange(`A${i+6}:M${i+6}`).format.rowHeight = rowHeight(texts, [80,35,35,35,35,35,40], 72);
    for (let j = 0; j < dims.length; j++) if (matrix[i][j] == null) main.getRange(`${String.fromCharCode(67+j)}${i+6}`).format.fill = '#FFE5CC';
  }
  guide.getRange('A2').values = [[`代理${coder}校准复核填写说明`]];
  guide.getRange('A3').values = [['本表接续用户复核意见；原代理初判及首次试填副本另行封存。不是新的独立盲评。']];
  guide.getRange('B11:C11').values = [['接续复核；逐项裁定后另存', '标签空白表示本次尚未最终裁定，不是0。其余值仍为代理建议；理由和完整引文已补写。']];
  guide.getRange('C13').values = [['接触过代理答案和这次反馈的继续判读属于复核；不得以修改后一致标签重算独立κ。']];
  guide.getRange('A31:C35').values = [
    ['本次解释复核阶段', '用户反馈后补写理由与证据', '与原独立初判分开记录；不重跑机器或改正文'],
    ['明确采用的修改', coder === 'B' ? '校准12经济性1→0' : '校准12经济性原0与用户确认一致', '依据是价格协商阶段及目录结果不等于经济性实质内容'],
    ['尚需裁定的标签数', data.awaiting_adjudication, '倾向项目和06/17/25公平性在填写表留空；不强制改0'],
    ['反馈记录来源', '用户在本对话提供，2026-10-10', '没有新增或推定真人姓名、日期和独立填写记录'],
    ['真人接续填写位置', '填写表C:G标签、复核记录I列补充；实际人员填第24—29行', '接续标签与实际信息填完后另存；手册冻结后另取未讨论材料检验'],
  ];
  guide.getRange('A31:C35').format.font = { name: font, size: 11, color: '#18202A' };
  guide.getRange('A31:C35').format.wrapText = true;
  guide.getRange('A31:C35').format.verticalAlignment = 'top';
  guide.getRange('A31:C35').format.rowHeight = 82;

  wb.recalculate();
  const inspections = [];
  inspections.push((await wb.inspect({ kind: 'table', range: '填写!A15:G18', include: 'values,formulas', tableMaxRows: 4, tableMaxCols: 7, maxChars: 2000 })).ndjson);
  inspections.push((await wb.inspect({ kind: 'table', range: '复核记录!A60:H66', include: 'values,formulas', tableMaxRows: 7, tableMaxCols: 8, maxChars: 2800 })).ndjson);
  inspections.push((await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 50 }, maxChars: 1000 })).ndjson);
  await fs.writeFile(path.join(out, `inspect_review_${coder}.ndjson`), inspections.join('\n'));
  const views = {
    main: ['填写', 'A16:G17'],
    reasons: ['填写', 'J16:M17'],
    record: ['复核记录', 'A61:F65'],
    evidence: ['引文依据', 'D66:G68'],
    guide: ['填写说明', 'A31:C35'],
  };
  for (const [name, [sheetName, range]] of Object.entries(views)) {
    const img = await wb.render({ sheetName, range, scale: 1, format: 'png' });
    await fs.writeFile(path.join(previews, `${coder}_${name}.png`), new Uint8Array(await img.arrayBuffer()));
  }
  const output = path.join(out, `校准复核工作表-${coder}.xlsx`);
  await (await SpreadsheetFile.exportXlsx(wb)).save(output);
  log[coder] = { path: output, labels_filled: data.working_labels_filled, pending_labels: data.awaiting_adjudication, reason_count: 200, evidence_rows: evidenceRows.length, confirmed_changes: data.confirmed_changes };
  console.log(JSON.stringify(log[coder]));
}
await fs.writeFile(path.join(out, '复核工作表导出记录.json'), JSON.stringify(log, null, 2) + '\n');
