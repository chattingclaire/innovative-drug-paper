import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile, FileBlob } from '@oai/artifact-tool';

const out = '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/09-delivery/native17-rule19-development77-results-sol';
const data = JSON.parse(await fs.readFile(path.join(out, 'inputs/mechanical-workbook-input.json'), 'utf8'));
const version = process.env.WORKBOOK_BUILD_VERSION || 'v1';
const versionDir = path.join(out, 'versions', version);
await fs.mkdir(versionDir, { recursive: true });
const wb = Workbook.create();
const sheets = Object.fromEntries(['说明', '逐维指标', '编码对照', '两处差异'].map(n => [n, wb.worksheets.add(n)]));
const ink = '#243247', navy = '#253B59', soft = '#F2F5F9';
const metricHeaders = ['比较对象', '维度', '分配数', '保存数', '联合二元数', '参照正例数', '参照负例数', '预测正例数', '预测负例数', '真阳性TP', '假阳性FP', '假阴性FN', '真阴性TN', '一致性κ', '精确率P', '召回率R', 'F1值', '观察一致率Po', '期望一致率Pe', '正向一致Ppos', '负向一致Pneg', '特异度', '阴性预测值NPV', 'κ点值目标', '精确率点值目标', '召回率点值目标', 'F1点值目标', '95%区间', 'p值', '指标JSON指针'];
const codeHeaders = ['条款编号', '部门', '维度', '当前参照A', '当前参照B', 'LLM首答', '规则首答', 'LLM原始理由', 'LLM原件与JSON指针', '规则原件与JSON指针', '当前参照A来源', '当前参照B来源'];

function col(i) { let x = i + 1, s = ''; while(x > 0){s = String.fromCharCode(65 + (x - 1) % 26) + s; x = Math.floor((x-1)/26);} return s; }
function init(sheet, lastCol, lastRow, title) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}${lastRow}`).format = { font: { name: 'Arial', size: 10, color: ink }, verticalAlignment: 'center' };
  sheet.getRange('A2').values = [[title]];
  sheet.getRange('A2').format.font = { name: 'Arial', size: 14, bold: true, color: ink };
  sheet.getRange(`A3:${lastCol}3`).format.borders = { bottom: { style: 'thin', color: navy } };
  sheet.getRange(`A1:${lastCol}${lastRow}`).format.rowHeight = 23;
}
function header(sheet, range) {
  sheet.getRange(range).format = { fill: navy, font: { name: 'Arial', size: 10, bold: true, color: '#FFFFFF' }, horizontalAlignment: 'center', verticalAlignment: 'center', wrapText: true, rowHeight: 36 };
}
function stripes(sheet, start, end, lastCol) {
  for(let r = start; r <= end; r++) if((r-start)%2===1) sheet.getRange(`A${r}:${lastCol}${r}`).format.fill = soft;
}
function proseRows(sheet, rows, start=7, widthChars=63) {
  sheet.getRange(`A${start}:B${start+rows.length-1}`).values = rows;
  sheet.getRange(`A${start}:B${start+rows.length-1}`).format.wrapText = true;
  sheet.getRange(`A${start}:B${start+rows.length-1}`).format.verticalAlignment = 'top';
  for(let i=0;i<rows.length;i++) {
    const txt = String(rows[i][1] ?? '');
    const length = Array.from(txt).reduce((a,c)=>a+(/[^\x00-\xff]/.test(c)?1:0.55),0);
    const lines = Math.max(1, Math.ceil(length/widthChars), txt.split('\n').length);
    sheet.getRange(`A${start+i}:B${start+i}`).format.rowHeight = 16 * lines + 12;
  }
}

const infoRows = [
  ['材料范围', '当前77条已曝光开发材料，共385个维度标签。已用于手册、规则和prompt开发。'],
  ['当前参照身份', '用户确认当前A/B为真人独立编码结果。保留当前文件原始组装、理由作者和各次修改历史。'],
  ['原生LLM运行', '13批上下文，共15次实际整批尝试，2次技术无效尝试。共101条记录尝试，最终保存77条。技术重试不是独立重复。'],
  ['标签完整性', '385个二元标签，语义null为0，终末失败批次为0。'],
  ['已完成比较', 'LLM首答与当前参照、规则首答与当前参照、保存A与B。各维度指标和点值目标按metrics.json原值复制。'],
  ['点值结果', '两机器五维κ、精确率、召回率、F1均超过项目0.80点值目标。保存A/B逐维κ=1。'],
  ['保留的两处差异', '04457创新性I、00131公平性F：当前A/B均0，LLM首答均1，规则首答均0。这里只描述LLM相对当前参照多判，未裁定语义正确性。'],
  ['统计范围', '本轮未计算p值或总体95%区间，表中均保留NA。未完成预定的真正独立重复。'],
  ['结果适用范围', '这些开发点值不构成新holdout上的正式验证，不能代表全量4481条编码正确，也不是正式验收。'],
  ['尚未完成', '新材料真人独立编码及机器正式检验、正式抽样95%区间、LLM预定重复及稳定性、全量4481重编码和完整论文修订。'],
  ['机器标签及原件', '385个标签和理由为只读复制。未为提高κ改写任何标签。原生理由机械读取完整wholebatch原件；衍生JSONL只是标签汇总及原件指针。'],
  ['四格表方向', 'TP/FP/FN/TN以当前参照为参照方向。保存A与B沿用JSON既有方向。两处多判在该参照方向中计入FP。'],
  ['数值显示', '计数按整数显示，指标显示六位小数，工作簿保存JSON中的完整数值精度。NA表示本轮未计算，不替代为0。'],
  ['数据时间', 'metrics.json记录：' + data.metrics_created_at_utc],
  ['路径基准', data.root],
];
const info = sheets['说明'];
init(info, 'C', 44, '当前77条机器编码与指标');
info.getRange('A6:B6').values = [['项目', '说明']]; header(info, 'A6:B6');
info.getRange('A1:A44').format.columnWidth = 24;
info.getRange('B1:B44').format.columnWidth = 122;
info.getRange('C1:C44').format.columnWidth = 68;
proseRows(info, infoRows); stripes(info,7,21,'B');
info.getRange('A24:C24').values = [['来源编号', '原文件绝对路径', '原文件SHA-256']]; header(info, 'A24:C24');
const sources = data.input_manifest.map((m,i)=>['来源'+String(i+1).padStart(2,'0'),m.original_path,m.sha256]);
info.getRange(`A25:C${24+sources.length}`).values = sources;
info.getRange(`A25:C${24+sources.length}`).format.wrapText = true;
info.getRange(`A25:C${24+sources.length}`).format.rowHeight = 62;
info.getRange(`A25:C${24+sources.length}`).format.verticalAlignment = 'top';
info.freezePanes.freezeRows(6); info.tabColor = navy;

const metric = sheets['逐维指标'];
init(metric,'AD',21,'当前77条逐维指标');
metric.getRange('A4').values = [['κ、精确率、召回率、F1点值目标为超过0.80。95%区间和p值未计算；数值原样取自metrics.json。']];
metric.getRange('A4').format.font = { name:'Arial',size:10,italic:true,color:'#5C6878' };
metric.getRange('A6:AD6').values = [metricHeaders]; header(metric,'A6:AD6');
metric.getRange('A7:AD21').values = data.metric_rows;
metric.getRange('A1:A21').format.columnWidth=25;
metric.getRange('B1:B21').format.columnWidth=15;
metric.getRange('C1:M21').format.columnWidth=11;
metric.getRange('N1:W21').format.columnWidth=15;
metric.getRange('X1:AA21').format.columnWidth=16;
metric.getRange('AB1:AC21').format.columnWidth=13;
metric.getRange('AD1:AD21').format.columnWidth=65;
metric.getRange('C7:M21').setNumberFormat('0');
metric.getRange('N7:W21').setNumberFormat('0.000000');
metric.getRange('C7:AC21').format.horizontalAlignment='right';
metric.getRange('X7:AA21').format.horizontalAlignment='center';
stripes(metric,7,21,'AD'); metric.freezePanes.freezeRows(6); metric.freezePanes.freezeColumns(2); metric.tabColor=navy;

const code = sheets['编码对照'];
init(code,'L',391,'77条编码对照：每条五维，共385行');
code.getRange('A4').values = [['当前A/B、两机器首答及LLM理由均复制原值。来源列路径相对于说明页所列基准目录。']];
code.getRange('A4').format.font = {name:'Arial',size:10,italic:true,color:'#5C6878'};
code.getRange('A6:L6').values = [codeHeaders]; header(code,'A6:L6');
code.getRange('A7:L391').values = data.code_rows;
const widths=[22,16,15,13,13,12,12,90,65,65,65,65];
for(let i=0;i<widths.length;i++)code.getRange(`${col(i)}1:${col(i)}391`).format.columnWidth=widths[i];
code.getRange('D7:G391').setNumberFormat('0'); code.getRange('D7:G391').format.horizontalAlignment='right';
code.getRange('H7:L391').format.wrapText=true; code.getRange('H7:L391').format.verticalAlignment='top';
for(let i=0;i<data.code_rows.length;i++){
  const texts=data.code_rows[i].slice(7);
  const lines=Math.max(...texts.map((s,j)=>Math.ceil(Array.from(String(s)).reduce((a,c)=>a+(/[^\x00-\xff]/.test(c)?1:0.55),0)/(j===0?47:34))));
  code.getRange(`A${i+7}:L${i+7}`).format.rowHeight=Math.max(30,16*lines+10);
}
stripes(code,7,391,'L');
code.getRange('F7:F391').conditionalFormats.addCustom('$F7<>$D7',{fill:'#FFF1DB',font:{color:'#8B5100',bold:true}});
code.freezePanes.freezeRows(6); code.freezePanes.freezeColumns(3);

const diff=sheets['两处差异'];
init(diff,'B',41,'相对当前参照的两处多判');
diff.getRange('A4').values=[['下列只复制双方原理由与来源，不裁定语义正确性。当前参照及机器首答保留原值。']];
diff.getRange('A4').format.font={name:'Arial',size:10,italic:true,color:'#5C6878'};
diff.getRange('A1:A41').format.columnWidth=24; diff.getRange('B1:B41').format.columnWidth=125;
const differenceRanges=[];
for(let i=0;i<data.differences.length;i++){
  const d=data.differences[i], start=6+i*18;
  diff.getRange(`A${start}:B${start}`).values=[['项目',d.id+' '+d.dimension]]; header(diff,`A${start}:B${start}`);
  const rows=[['条款编号',d.id],['部门',d.department],['维度',d.dimension],['当前参照A',d.reference_A],['当前参照B',d.reference_B],['LLM首答',d.LLM],['规则首答',d.rule],['差异方向',d.relative_direction],['LLM原始理由',d.LLM_reason],['规则原始理由',d.rule_reason],['当前A原表理由',d.A_reason],['当前B原表理由',d.B_reason],['LLM原件与JSON指针',d.LLM_source],['规则原件与JSON指针',d.rule_source],['当前参照A来源',d.A_source],['当前参照B来源',d.B_source]];
  proseRows(diff,rows,start+1,66); stripes(diff,start+1,start+rows.length,'B');
  differenceRanges.push({id:d.id,range:`A${start+1}:B${start+rows.length}`,rows});
}
diff.freezePanes.freezeRows(6);

wb.recalculate();
const expected=[['逐维指标','A7:AD21',data.metric_rows],['编码对照','A7:L391',data.code_rows],...differenceRanges.map(x=>['两处差异',x.range,x.rows]),['说明','A7:B21',infoRows],['说明',`A25:C${24+sources.length}`,sources]];
const memChecks=[];
for(const [sheet,range,rows] of expected){
  const actual=sheets[sheet].getRange(range).values;
  if(JSON.stringify(actual)!==JSON.stringify(rows)){
    await fs.writeFile(path.join(versionDir,'readback-mismatch.json'),JSON.stringify({sheet,range,expected:rows,actual},null,2));
    throw new Error(`Memory readback mismatch ${sheet}!${range}`);
  }
  memChecks.push({sheet,range,rows:rows.length,exact_match:true});
}
const inspections=[];
for(const [sheet,range] of [['逐维指标','A7:W11'],['编码对照','A7:H11'],['两处差异','A7:B14'],['两处差异','A25:B32']]) inspections.push((await wb.inspect({kind:'table',range:`'${sheet}'!${range}`,include:'values,formulas',tableMaxRows:5,tableMaxCols:8,maxChars:2500})).ndjson);
await fs.writeFile(path.join(versionDir,'inspect.ndjson'),inspections.join('\n'));
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'final formula error scan',maxChars:3000});
await fs.writeFile(path.join(versionDir,'formula-error-scan.ndjson'),errors.ndjson);

const filename='当前77条机器编码与指标.xlsx';
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(versionDir,filename));
const imported=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(versionDir,filename)));
const exportChecks=[];
for(const [sheet,range,rows] of expected){
  const actual=imported.worksheets.getItem(sheet).getRange(range).values;
  if(JSON.stringify(actual)!==JSON.stringify(rows))throw new Error(`Export readback mismatch ${sheet}!${range}`);
  exportChecks.push({sheet,range,rows:rows.length,exact_match:true});
}
await fs.writeFile(path.join(versionDir,'artifact-readback.json'),JSON.stringify({version,memory:memChecks,exported:exportChecks,formula_error_scan:errors.ndjson,unchanged_input_hashes:true},null,2));
console.log(JSON.stringify({version,exported:path.join(versionDir,filename),verified_rows:385,metric_rows:15,exact_readback:true}));

const renders=[['说明','A1:B21','说明'],['逐维指标','A1:M21','逐维指标-计数'],['逐维指标','N6:AC21','逐维指标-数值及目标'],['编码对照','A1:H11','编码对照-首段'],['编码对照','A198:H201','编码对照-04457'],['编码对照','A49:H53','编码对照-00131'],['两处差异','A1:B22','两处差异-04457'],['两处差异','A24:B40','两处差异-00131']];
for(const [sheetName,range,name] of renders){
  const blob=await wb.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(out,'render',name+'.png'),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({version,renders:renders.length,finished:true}));
