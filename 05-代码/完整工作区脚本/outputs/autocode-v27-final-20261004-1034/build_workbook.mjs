import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const dir=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(await fs.readFile(path.join(dir,'workbook_data.json'),'utf8'));
const wb=Workbook.create();
const overview=wb.worksheets.add('结果总览');
const calc=wb.worksheets.add('指标计算');
const detail=wb.worksheets.add('逐条编码');
const dims=['S','E','Ec','I','F'];
const names={S:'安全性',E:'有效性',Ec:'经济性',I:'创新性',F:'公平性'};
const methods={rules_v26_2:'自动规则 v26.2',rules_v27:'自动规则 v27',llm_unchanged:'LLM 原已执行版本'};
const color='#244760';
const font={name:'Arial',size:10,color:'#202B35'};
function header(sheet,range){sheet.getRange(range).format={fill:color,font:{...font,bold:true,color:'#FFFFFF'},rowHeight:34,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};}
for(const s of [overview,calc,detail])s.showGridLines=false;

const metricRows=data.metrics.map(m=>[m.scope,names[m.dimension],m.reference,methods[m.method],m.confusion.TP,m.confusion.FP,m.confusion.FN,m.confusion.TN]);
calc.getRange('A1:O1').values=[['样本组','维度','参照','方法','TP','FP','FN','TN','配对数 n','观察一致率','偶然一致率','Cohen κ','精确率','召回率','F1']];
calc.getRange(`A2:H${metricRows.length+1}`).values=metricRows;
const formulas=metricRows.map((_,i)=>{const r=i+2;return [`=SUM(E${r}:H${r})`,`=(E${r}+H${r})/I${r}`,`=((E${r}+F${r})*(E${r}+G${r})+(G${r}+H${r})*(F${r}+H${r}))/(I${r}*I${r})`,`=IF(K${r}=1,"n.a.",(J${r}-K${r})/(1-K${r}))`,`=IF(E${r}+F${r}=0,"n.a.",E${r}/(E${r}+F${r}))`,`=IF(E${r}+G${r}=0,"n.a.",E${r}/(E${r}+G${r}))`,`=IF(2*E${r}+F${r}+G${r}=0,"n.a.",2*E${r}/(2*E${r}+F${r}+G${r}))`];});
calc.getRange(`I2:O${metricRows.length+1}`).formulas=formulas;
calc.getRange(`A1:O${metricRows.length+1}`).format.font=font;
calc.getRange(`A1:O${metricRows.length+1}`).format.rowHeight=24;
calc.getRange('A1:D61').format.columnWidth=18;
calc.getRange('D1:D61').format.columnWidth=24;
calc.getRange('E1:O61').format.columnWidth=13;
calc.getRange('E2:I61').setNumberFormat('0');
calc.getRange('J2:K61').setNumberFormat('0.0%');
calc.getRange('L2:L61').setNumberFormat('0.000');
calc.getRange('M2:O61').setNumberFormat('0.0%');
header(calc,'A1:O1');
calc.freezePanes.freezeRows(1);
calc.tables.add('A1:O61',true,'MetricCalculations');
calc.getRange('A64').values=[['来源：当前 A/C 首次标注与冻结预测逐条配对；TP/FP/FN/TN 按同一共同可判子集计算。']];
calc.getRange('A65').values=[['历史分层加权结果另保存在 metrics.json；本表为未加权比较，不合并两个样本组。']];

const metricRow=new Map(data.metrics.map((m,i)=>[[m.scope,m.dimension,m.reference,m.method].join('/'),i+2]));
overview.getRange('A2').values=[['自动规则五维修订结果']];
overview.getRange('A3').values=[[`全量 ${data.summary.n} 条，自动规则待定 ${data.summary.pending_n} 条；${data.summary.changed_units} 条至少一个维度发生变化。`]];
overview.getRange('A4').values=[['固定 CAL-5D v1.3 定义。LLM 为原已执行结果，本次未重跑。']];
overview.getRange('A1:I25').format.font=font;
overview.getRange('A2').format.font={...font,size:16,bold:true};
overview.getRange('A1:I25').format.rowHeight=26;
overview.getRange('A1:I25').format.columnWidth=18;
overview.getRange('H1:I25').format.columnWidth=12;
for(const [scope,start] of [['H427',6],['current1268',15]]){
  overview.getRange(`A${start-1}`).values=[[scope==='H427'?'H427：427 条已暴露开发材料':'current1268：1,268 条既有比较材料']];
  overview.getRange(`A${start}:I${start}`).values=[['维度','旧规则—A κ','旧规则—C κ','新规则—A κ','新规则—C κ','原 LLM—A κ','原 LLM—C κ','A 配对数','C 配对数']];
  header(overview,`A${start}:I${start}`);
  dims.forEach((d,i)=>{
    const row=start+1+i;overview.getRange(`A${row}`).values=[[names[d]]];
    const pairs=[['A','rules_v26_2'],['C','rules_v26_2'],['A','rules_v27'],['C','rules_v27'],['A','llm_unchanged'],['C','llm_unchanged']];
    const links=pairs.map(([r,m])=>`='指标计算'!L${metricRow.get([scope,d,r,m].join('/'))}`);
    links.push(...['A','C'].map(r=>`='指标计算'!I${metricRow.get([scope,d,r,'rules_v27'].join('/'))}`));
    overview.getRange(`B${row}:I${row}`).formulas=[links];
  });
  overview.getRange(`B${start+1}:G${start+5}`).setNumberFormat('0.000');
  overview.getRange(`H${start+1}:I${start+5}`).setNumberFormat('0');
  overview.getRange(`D${start+1}:E${start+5}`).format.fill='#EDF2F6';
}
overview.getRange('A22').values=[['A/C 是按人工编码标准执行的 AI 编码员，不能视为真人金标准。']];
overview.getRange('A23').values=[['每个维度在同一参照下使用相同条目；历史待定不填 0，A 与 C 的配对数可能不同。']];
overview.getRange('A24').values=[['这些材料已用于开发审查，结果属于描述性比较，不构成新的独立验证。']];
overview.getRange('A25').values=[['精确率、召回率、F1 与混淆计数见“指标计算”；原文、标签、证据见“逐条编码”。']];
overview.tabColor=color;

const columns=['条目ID','样本组','原文',...dims.map(d=>'新规则_'+d),'修订维度',...dims.map(d=>'旧规则_'+d),...dims.map(d=>'A_'+d),...dims.map(d=>'C_'+d),...dims.map(d=>'证据_'+d),'条件列表修复','创新适用范围补入','来源文件'];
const values=data.rows.map(r=>[r.id,r.scope,r.text,...dims.map(d=>r.after[d]),r.changed_dimensions,...dims.map(d=>r.before[d]),...dims.map(d=>r.references.A?.[d]??null),...dims.map(d=>r.references.C?.[d]??null),...dims.map(d=>r.evidence[d]),r.context_repaired?'是':'否',r.innovation_scope_added?'是':'否',r.source]);
detail.getRange('A1:AF1').values=[columns];
detail.getRange(`A2:AF${values.length+1}`).values=values;
detail.getRange(`A1:AF${values.length+1}`).format={font,verticalAlignment:'top'};
detail.getRange('A1:B4925').format.columnWidth=22;
detail.getRange('C1:C4925').format.columnWidth=140;
detail.getRange('D1:X4925').format.columnWidth=11;
detail.getRange('Y1:AC4925').format.columnWidth=80;
detail.getRange('AD1:AE4925').format.columnWidth=20;
detail.getRange('AF1:AF4925').format.columnWidth=100;
detail.getRange('C2:C4925').format.wrapText=true;
detail.getRange('Y2:AF4925').format.wrapText=true;
header(detail,'A1:AF1');
for(let i=0;i<values.length;i++){
  const r=values[i];
  const lines=Math.max(Math.ceil(r[2].length/75),...r.slice(24,29).map(x=>Math.ceil(x.length/43)),Math.ceil((r[31]??'').length/74));
  detail.getRange(`A${i+2}:AF${i+2}`).format.rowHeight=Math.max(30,Math.min(409,lines*14+8));
}
detail.freezePanes.freezeRows(1);detail.freezePanes.freezeColumns(2);
detail.tables.add('A1:AF4925',true,'RuleCodingRows');

wb.recalculate();
const numeric=calc.getRange('L2:O61').values;
data.metrics.forEach((m,i)=>{[m.kappa,m.precision,m.recall,m.f1].forEach((expected,j)=>{const actual=numeric[i][j];if(expected===null){if(actual!=='n.a.')throw new Error(`Expected unavailable ${i},${j}`);}else if(Math.abs(actual-expected)>1e-10)throw new Error(`Metric mismatch ${i},${j}: ${actual} != ${expected}`);});});
console.log((await wb.inspect({kind:'table',range:'结果总览!A6:I11',include:'values,formulas',tableMaxRows:6,tableMaxCols:9,maxChars:2800})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
for(const [sheetName,range,name] of [['结果总览','A1:I25','overview'],['指标计算','A1:O8','metrics'],['逐条编码','A1:I5','rows'],['逐条编码','Y1:AE5','evidence']]){
  const preview=await wb.render({sheetName,range,scale:1,format:'png'});
  await fs.writeFile(path.join(dir,`${name}-preview.png`),new Uint8Array(await preview.arrayBuffer()));
}
const output=await SpreadsheetFile.exportXlsx(wb);
await output.save(path.join(dir,'自动规则五维修订结果-v27.xlsx'));
await fs.writeFile(path.join(dir,'workbook_verification.json'),JSON.stringify({metrics_checked:data.metrics.length,formula_values_match_python:true,rows:values.length,sheets:3,generated_at:new Date().toISOString()},null,2));
console.log('Saved 自动规则五维修订结果-v27.xlsx');
