import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

process.on('uncaughtException', error => { console.error(String(error?.message ?? error)); console.error(String(error?.stack ?? '').split('\n').slice(0, 6).join('\n')); process.exit(1); });
process.on('unhandledRejection', error => { console.error(String(error?.message ?? error)); console.error(String(error?.stack ?? '').split('\n').slice(0, 6).join('\n')); process.exit(1); });

const ROOT = '/PROJECT_ROOT/outputs/goal-calibration-20261010';
const SUPPORT = path.join(ROOT, 'logs/remaining4-calibration-delivery');
const INPUT = path.join(SUPPORT, 'report-inputs.json');
const TARGET = path.join(ROOT, '09-delivery/agent-review-20261010/剩余4项单独校准表.xlsx');
const data = JSON.parse(await fs.readFile(INPUT, 'utf8'));
// XLSX XML cannot store PDF form feeds; show their reversible visible symbol.
const displayRows = data.materials.map(row => row.map(value => typeof value === 'string' ? value.replaceAll('\f', '␌') : value));
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
for (const binding of data.bindings) if (sha(await fs.readFile(binding.path)) !== binding.sha256) throw Error(`Changed source: ${binding.path}`);
if (data.rows.length !== 4 || data.scope.records !== 3) throw Error('Wrong review scope');
const wb = Workbook.create();
const review = wb.worksheets.add('校准表');
const materials = wb.worksheets.add('原文语境');
const diagram = wb.worksheets.add('流程原图');
const col = i => String.fromCharCode(65 + i);
function base(s, end, title) {
  s.showGridLines = false;
  s.getRange(`A1:${end}60`).format.font = { name: 'Arial', size: 11, color: '#243044' };
  s.getRange(`A1:${end}60`).format.rowHeight = 26;
  s.getRange('A2').values = [[title]];
  s.getRange('A2').format.font = { name: 'Arial', size: 15, bold: true, color: '#243044' };
}
function header(s, labels) {
  const range = s.getRange(`A6:${col(labels.length - 1)}6`);
  range.values = [labels];
  range.format.fill = '#334A65';
  range.format.font = { name: 'Arial', size: 11, bold: true, color: '#FFFFFF' };
  range.format.wrapText = true;
  range.format.rowHeight = 34;
  range.format.horizontalAlignment = 'center';
}
function rowHeight(row, widths) {
  return Math.min(409, Math.max(65, 14 + Math.max(...row.map((v, i) => String(v ?? '').split('\n').reduce((n, line) => n + Math.max(1, Math.ceil(Array.from(line).length / (widths[i] * .6))), 0))) * 15));
}
base(review, 'I', '剩余4项单独校准表');
review.tabColor = '#CB9343';
review.getRange('A4').values = [[data.instruction]];
review.getRange('A4').format.font = { name: 'Arial', size: 11, color: '#526072' };
review.getRange('A5').values = [['02573经济性及此前6项已复核，本次不重复。完整条款、同版语境和原流程图均已放入本文件。']];
header(review, ['条款编号', '部门', '维度', '编码0/1', '判断理由', '本项核验问题', '当前完整条款', '所需语境位置', '原A/B对应位置']);
review.getRange('A7:A10').setNumberFormat('@');
review.getRange('A7:I10').values = data.rows;
const widths = [14, 12, 16, 12, 58, 64, 86, 55, 30];
widths.forEach((width, i) => review.getRange(`${col(i)}6:${col(i)}10`).format.columnWidth = width);
review.getRange('A7:I10').format.wrapText = true;
review.getRange('A7:I10').format.verticalAlignment = 'top';
review.getRange('D7:E10').format.fill = '#FFF2CC';
review.getRange('D7:E10').format.font = { name: 'Arial', size: 11, color: '#1C4C92' };
review.getRange('D7:D10').setNumberFormat('0');
review.getRange('D7:D10').dataValidation = { rule: { type: 'list', values: ['0', '1'] } };
data.rows.forEach((row, i) => review.getRange(`A${i+7}:I${i+7}`).format.rowHeight = rowHeight(row, widths));
review.freezePanes.freezeRows(6);
review.freezePanes.freezeColumns(3);

base(materials, 'E', '原文语境与现行手册');
materials.tabColor = '#56716A';
materials.getRange('A4').values = [['同一材料分行连续展示；按分段序号顺读。补材为同版原PDF整页文字；␌表示原PDF换页符。']];
materials.getRange('A5').values = [['00138：申报前沟通、审评中优先沟通、工作要求分别保留，须由复核者判断它们与当前条款的关系。']];
header(materials, ['材料编号', '内容与分段', '原文位置', '完整材料文字（连续分段）', '来源文件']);
const end = data.materials.length + 6;
materials.getRange(`A7:E${end}`).values = displayRows;
const mw = [22, 48, 58, 116, 74];
mw.forEach((width, i) => materials.getRange(`${col(i)}6:${col(i)}${end}`).format.columnWidth = width);
materials.getRange(`A7:E${end}`).format.wrapText = true;
materials.getRange(`A7:E${end}`).format.verticalAlignment = 'top';
displayRows.forEach((row, i) => {
  const range = materials.getRange(`A${i+7}:E${i+7}`);
  range.format.rowHeight = rowHeight(row, mw);
  if (i === 0 || displayRows[i-1][0] !== row[0]) range.format.fill = '#E8EFEB';
});
materials.freezePanes.freezeRows(6);
materials.freezePanes.freezeColumns(1);

base(diagram, 'Q', '03876：同版原流程图');
diagram.tabColor = '#334A65';
diagram.getRange('A4').values = [['来源：国家医保局《常用问答》2026版，PDF物理第11页／印刷第8页。图3原页，未修改。']];
diagram.getRange('A5').values = [['请结合原文语境中的同版价格协商说明与商保目录使用说明判断经济性；目录纳入不直接等同实际承保或报销。']];
diagram.getRange('A1:Q54').format.columnWidth = 13;
const imageBytes = await fs.readFile(data.image_path);
diagram.images.add({ blob: imageBytes.buffer.slice(imageBytes.byteOffset, imageBytes.byteOffset + imageBytes.byteLength), contentType: 'image/png', alt: '03876同版原图3：商保创新药目录申报全流程', anchor: { from: { row: 6, col: 0 }, extent: { widthPx: 1500, heightPx: Math.round(1500 * 1485 / 2100) } } });

const blank = review.getRange('D7:E10').values;
if (blank.some(row => row.some(v => v !== null && v !== undefined && v !== ''))) throw Error('Review labels or reasons prefilled');
for (const block of data.blocks) {
  if (block.text.includes('␌')) throw Error('Visible control marker already in source');
  const restored = displayRows.filter(row => row[0] === block.key).map(row => row[3]).join('').replaceAll('␌', '\f');
  if (restored !== block.text || sha(Buffer.from(restored)) !== block.text_sha256) throw Error(`Lossy context: ${block.key}`);
}
const errorScan = await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 30 }, maxChars: 2000 });
await fs.writeFile(path.join(SUPPORT, 'error-scan.ndjson'), errorScan.ndjson);
for (const [sheetName, range, slug] of [
  ['校准表', 'A1:F10', 'review-inputs'],
  ['校准表', 'F6:I10', 'review-clauses'],
  ['原文语境', 'A1:D9', 'materials-start'],
  ['原文语境', `A${end-2}:D${end}`, 'materials-last'],
  ['流程原图', 'A1:Q51', 'diagram'],
]) {
  const preview = await wb.render({ sheetName, range, scale: 1, format: 'png' });
  await fs.writeFile(path.join(SUPPORT, slug + '.png'), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(TARGET);
const verification = { output: TARGET, sha256: sha(await fs.readFile(TARGET)), slots: 4, records: 3, editable_cells_blank: 8, materials_reversibly_preserved_blocks: data.blocks.length, display_control_encoding: { U000C: '␌' }, original_image_sha256: sha(imageBytes), originals_edited: false, independent_blind_validation: false };
await fs.writeFile(path.join(SUPPORT, 'authoring-verification.json'), JSON.stringify(verification, null, 2) + '\n');
console.log(JSON.stringify(verification));
