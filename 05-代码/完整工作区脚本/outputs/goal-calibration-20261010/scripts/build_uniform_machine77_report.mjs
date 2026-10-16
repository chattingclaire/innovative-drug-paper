import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const ROOT = '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010';
const SUPPORT = path.join(ROOT, 'logs/uniform-machine77-report-delivery');
const INPUT = path.join(SUPPORT, 'report-inputs.json');
const TARGET = path.join(ROOT, '09-delivery/agent-review-20261010/本轮77条机器编码与指标.xlsx');
const data = JSON.parse(await fs.readFile(INPUT, 'utf8'));
const names = { S: 'S 安全性', E: 'E 有效性', Ec: 'Ec 经济性', I: 'I 创新性', F: 'F 公平性' };
const col = n => { let s = ''; for (let x = n + 1; x; x = Math.floor((x - 1) / 26)) s = String.fromCharCode(65 + (x - 1) % 26) + s; return s; };
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
if (data.rows.length !== 385 || data.scope.assigned_N !== 77) throw Error('Incomplete cohort');
for (const binding of data.bindings) {
  if (sha(await fs.readFile(binding.path)) !== binding.sha256) throw Error(`Changed input: ${binding.path}`);
}
const wb = Workbook.create();
const summary = wb.worksheets.add('指标');
const detail = wb.worksheets.add('编码对照');
summary.tabColor = '#334A65';
function base(sheet, endCol, endRow, title) {
  sheet.showGridLines = false;
  const area = sheet.getRange(`A1:${endCol}${endRow}`);
  area.format.font = { name: 'Arial', size: 10, color: '#243044' };
  area.format.verticalAlignment = 'center';
  area.format.rowHeight = 25;
  sheet.getRange('A2').values = [[title]];
  sheet.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true, color: '#243044' };
}
function header(sheet, row, labels) {
  const range = sheet.getRange(`A${row}:${col(labels.length - 1)}${row}`);
  range.values = [labels];
  range.format.fill = '#334A65';
  range.format.font = { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' };
  range.format.horizontalAlignment = 'center';
  range.format.wrapText = true;
  range.format.rowHeight = 32;
}
base(detail, 'N', 391, '77条五维编码对照');
detail.getRange('A4').values = [['参照为当前A/B；LLM与规则均保留本轮原判。引文列为节选，完整引文在初判文件中。']];
detail.getRange('A4').format.font = { name: 'Arial', size: 10, italic: true, color: '#526072' };
header(detail, 6, ['条款编号', '部门', '维度', '参照', 'LLM', '规则', '参照理由', 'LLM理由', '规则理由', '当前完整条款', 'LLM引文节选及位置', '规则依据类型', 'LLM完整初判文件', '完整材料文件']);
const rows = data.rows.map(row => {
  const copy = [...row];
  if (copy[10].length > 1200) copy[10] = copy[10].slice(0, 1200) + '\n〔其余引文及完整字段见初判文件〕';
  return copy;
});
detail.getRange('A7:N391').values = rows;
[25, 11, 16, 8, 8, 8, 60, 60, 60, 72, 75, 40, 45, 45].forEach((width, i) => detail.getRange(`${col(i)}6:${col(i)}391`).format.columnWidth = width);
detail.getRange('D7:F391').setNumberFormat('0');
detail.getRange('G7:N391').format.wrapText = true;
detail.getRange('G7:N391').format.verticalAlignment = 'top';
rows.forEach((row, index) => {
  const height = Math.max(...row.slice(6, 11).map((text, i) => {
    const width = [60, 60, 60, 72, 75][i];
    return 10 + String(text).split('\n').reduce((n, part) => n + Math.max(1, Math.ceil(Array.from(part).length / (width * .65))), 0) * 13;
  }));
  detail.getRange(`A${index + 7}:N${index + 7}`).format.rowHeight = Math.min(409, Math.max(42, height));
});
detail.getRange('E7:E391').conditionalFormats.addCustom('AND(ISNUMBER(E7),E7<>D7)', { fill: '#FCE4D6', font: { color: '#9C3126' } });
detail.getRange('F7:F391').conditionalFormats.addCustom('AND(ISNUMBER(F7),F7<>D7)', { fill: '#FCE4D6', font: { color: '#9C3126' } });
detail.freezePanes.freezeRows(6);
detail.freezePanes.freezeColumns(3);

base(summary, 'J', 62, '本轮77条机器编码指标');
[16, 16, 12, 12, 12, 12, 12, 12, 12, 12].forEach((width, i) => summary.getRange(`${col(i)}4:${col(i)}62`).format.columnWidth = width);
summary.getRange('A3').values = [['77条开发材料。参照为AI初表加真人局部事后复核，正式独立检验仍待完成。']];
summary.getRange('A3').format.font = { name: 'Arial', size: 10, italic: true, color: '#526072' };
header(summary, 5, ['机器', '维度', 'κ', '精确率', '召回率', 'F1']);
header(summary, 20, ['机器', '维度', '共同可判N', '参照正类', '参照负类', 'TP', 'FP', 'FN', 'TN', '待定']);
header(summary, 35, ['机器', '维度', '观察一致率', '机会一致率', '正类一致率', '负类一致率', '特异度', '负预测值', '机器正类']);
const metrics = [];
for (const [machineIndex, [machine, predictedColumn, source]] of [['LLM', 'E', data.native_dimensions], ['规则', 'F', data.rule_dimensions]].entries()) {
  for (const [dimIndex, dim] of data.dimensions.entries()) {
    const offset = machineIndex * 5 + dimIndex;
    const top = 6 + offset, count = 21 + offset, aux = 36 + offset;
    const dimension = names[dim];
    const range = "'编码对照'!";
    const dimRange = `${range}$C$7:$C$391`, refRange = `${range}$D$7:$D$391`, predRange = `${range}$${predictedColumn}$7:$${predictedColumn}$391`;
    summary.getRange(`A${top}:B${top}`).values = [[machine, dimension]];
    summary.getRange(`A${count}:B${count}`).values = [[machine, dimension]];
    summary.getRange(`A${aux}:B${aux}`).values = [[machine, dimension]];
    summary.getRange(`C${count}:J${count}`).formulas = [[
      `=SUM(F${count}:I${count})`,
      `=COUNTIFS(${dimRange},$B${count},${refRange},1)`,
      `=COUNTIFS(${dimRange},$B${count},${refRange},0)`,
      ...[[1,1],[0,1],[1,0],[0,0]].map(([reference, prediction]) => `=COUNTIFS(${dimRange},$B${count},${refRange},${reference},${predRange},${prediction})`),
      `=COUNTIFS(${dimRange},$B${count},${predRange},"待定")`,
    ]];
    summary.getRange(`C${aux}:I${aux}`).formulas = [[
      `=IF(C${count}=0,"NA",(F${count}+I${count})/C${count})`,
      `=IF(C${count}=0,"NA",((F${count}+G${count})*(F${count}+H${count})+(I${count}+H${count})*(I${count}+G${count}))/C${count}^2)`,
      `=IF(2*F${count}+G${count}+H${count}=0,"NA",2*F${count}/(2*F${count}+G${count}+H${count}))`,
      `=IF(2*I${count}+G${count}+H${count}=0,"NA",2*I${count}/(2*I${count}+G${count}+H${count}))`,
      `=IF(I${count}+G${count}=0,"NA",I${count}/(I${count}+G${count}))`,
      `=IF(I${count}+H${count}=0,"NA",I${count}/(I${count}+H${count}))`,
      `=SUM(F${count}:G${count})`,
    ]];
    summary.getRange(`C${top}:F${top}`).formulas = [[
      `=IF(C${count}=0,"NA",IF(D${aux}=1,"NA",(C${aux}-D${aux})/(1-D${aux})))`,
      `=IF(F${count}+G${count}=0,"NA",F${count}/(F${count}+G${count}))`,
      `=IF(F${count}+H${count}=0,"NA",F${count}/(F${count}+H${count}))`,
      `=E${aux}`,
    ]];
    metrics.push({ machine, dim, top, count, aux, expected: source[dim] });
  }
}
summary.getRange('C6:F15').setNumberFormat('0.000');
summary.getRange('C36:H45').setNumberFormat('0.000');
summary.getRange('C21:J30').setNumberFormat('0');
summary.getRange('I36:I45').setNumberFormat('0');
summary.getRange('A17').values = [['核心点指标项目目标为逐维≥0.80。本表保留5项LLM分歧；规则与参照一致。']];
summary.getRange('A18').values = [['95%区间：本轮开发材料不用于总体推断。p值未计算，编码表无需显著性星号。']];
summary.getRange('A47').values = [['共同手册v1.3F。LLM统一执行提示v16；规则v18。13个LLM批次共同构成一次77条运行。']];
header(summary, 50, ['机器', '分配条款', '完成条款', '二元判断', '待定判断', '技术失败', '未完成条款', '条款覆盖率']);
summary.getRange('A51:H52').values = [
  ['LLM', 77, 77, data.scope.native_valid_slots, data.scope.native_null_slots, 0, 0, 1],
  ['规则', 77, 77, data.scope.rule_valid_slots, data.scope.rule_null_slots, data.scope.rule_failure_slots, 0, 1],
];
summary.getRange('H51:H52').setNumberFormat('0.0%');
summary.getRange('A54').values = [['A/B当前保存值一致（κ=1），独立真人初判信度尚未完成。相同设置LLM独立重复尚未完成。']];
summary.getRange('A56').values = [['数据来源：当前编码复核表A/B；本轮LLM各批封存初判；规则v18 run77-first。']];
summary.getRange('A57').values = [['完整政策材料、机器原判与理由路径见编码对照。参照修改后须另存版本并重新复算。']];

const recalculationChecks = [];
// Temporary engine tests change the derived view only; restore before export.
const original = detail.getRange('E7').values[0][0];
if (data.rows[0][2] !== 'S 安全性' || data.rows[0][3] !== 0 || original !== 1) throw Error('Unexpected control record');
detail.getRange('E7').values = [[0]];
if (summary.getRange('G21').values[0][0] !== 0 || summary.getRange('C6').values[0][0] !== 1) throw Error('Zero recalculation failed');
recalculationChecks.push({ temporary_input: 'E7=0', expected_FP: 0, actual_FP: summary.getRange('G21').values[0][0] });
detail.getRange('E7').values = [['待定']];
if (summary.getRange('C21').values[0][0] !== 76 || summary.getRange('J21').values[0][0] !== 1) throw Error('Unknown recalculation failed');
recalculationChecks.push({ temporary_input: 'E7=待定', expected_joint_N: 76, actual_joint_N: summary.getRange('C21').values[0][0], actual_null_N: summary.getRange('J21').values[0][0] });
detail.getRange('E7').values = [[original]];
wb.recalculate();
const near = (a, b) => b === null ? a === 'NA' : typeof a === 'number' && Math.abs(a - b) < 1e-12;
for (const metric of metrics) {
  const values = summary.getRange(`C${metric.top}:F${metric.top}`).values[0];
  ['kappa','precision','recall','F1'].forEach((key, i) => { if (!near(values[i], metric.expected.metrics[key])) throw Error(`${metric.machine}/${metric.dim}/${key} mismatch`); });
  const cells = summary.getRange(`F${metric.count}:I${metric.count}`).values[0];
  ['TP','FP','FN','TN'].forEach((key, i) => { if (cells[i] !== metric.expected.four_cells[key]) throw Error(`four-cell mismatch: ${metric.dim}/${key}`); });
  const auxiliary = summary.getRange(`C${metric.aux}:H${metric.aux}`).values[0];
  ['Po','Pe','Ppos','Pneg','specificity','NPV'].forEach((key, i) => { if (!near(auxiliary[i], metric.expected.metrics[key])) throw Error(`auxiliary mismatch: ${metric.dim}/${key}`); });
}
if (JSON.stringify(detail.getRange('D7:F391').values) !== JSON.stringify(rows.map(row => row.slice(3,6)))) throw Error('Export view label changed');
const errorScan = await wb.inspect({ kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A|#NULL!|#SPILL!|#CALC!', options:{useRegex:true,maxResults:30}, maxChars:4000 });
await fs.writeFile(path.join(SUPPORT,'formula-error-scan.ndjson'),errorScan.ndjson);
if (/"value":"#/.test(errorScan.ndjson)) throw Error('Formula error');
for (const [sheetName, range, slug] of [['指标','A1:J30','summary'],['指标','A33:J57','auxiliary'],['编码对照','A1:I9','detail-start'],['编码对照','A156:I159','detail-middle'],['编码对照','A364:I367','detail-later']]) {
  const preview = await wb.render({sheetName,range,scale:1.2,format:'png'});
  await fs.writeFile(path.join(SUPPORT,`${slug}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(TARGET);
const verification = { output:TARGET, sha256:sha(await fs.readFile(TARGET)), report_input_sha256:sha(await fs.readFile(INPUT)), formula_crosschecks_N:100, four_cells_crosschecks_N:40, restored_raw_label_view_slots_N:1155, recalculationChecks, formal_acceptance:false, raw_firsts_edited:false };
await fs.writeFile(path.join(SUPPORT,'authoring-verification.json'),JSON.stringify(verification,null,2)+'\n');
console.log(JSON.stringify(verification));
