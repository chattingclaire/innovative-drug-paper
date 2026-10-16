import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const dir=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(await fs.readFile(path.join(dir,'audit_report_data.json'),'utf8'));
const extended=JSON.parse(await fs.readFile(path.join(dir,'extended_metrics.json'),'utf8'));
const wb=Workbook.create();
const main=wb.worksheets.add('κ与工作目标');
const review=wb.worksheets.add('逐条复核');
const rules=wb.worksheets.add('规则调整');
const all=wb.worksheets.add('全量编码');
const ci=wb.worksheets.add('完整指标与区间');
const ac=wb.worksheets.add('A与C一致性');
const dims=['S','E','Ec','I','F'];
const names={S:'安全性',E:'有效性',Ec:'经济性',I:'创新性',F:'公平性'};
const methods={rules_v27:'修订前 v27',rules_v28:'本轮 v28',llm_unchanged:'原 LLM，未重跑'};
const font={name:'Arial',size:10,color:'#1F2933'};
const head='#294861';
function header(s,r){s.getRange(r).format={fill:head,font:{...font,bold:true,color:'#FFFFFF'},rowHeight:32,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};}
function base(s,range){s.showGridLines=false;s.getRange(range).format={font,rowHeight:25,verticalAlignment:'center'};}
function val(s,cell,x){s.getRange(cell).values=[[x]];}
function note(s,cell,x){val(s,cell,x);s.getRange(cell).format.font={...font,color:'#4A5560'};}
base(main,'A1:S98');main.tabColor=head;
main.getRange('A1:A98').format.columnWidth=16;
main.getRange('B1:D98').format.columnWidth=16;
main.getRange('E1:S98').format.columnWidth=13;
val(main,'A2','自动规则 κ 复核与修订');main.getRange('A2').format.font={...font,bold:true,size:16};
val(main,'A4','工作目标 κ');val(main,'B4',0.8);main.getRange('B4').setNumberFormat('0.00');
note(main,'D4','0.80 是本轮复核目标，不是通用论文合格线。');
note(main,'A5',`全量 ${data.summary.total} 条；${data.summary.changed_units} 条至少一个标签改变；自动规则待定 ${data.summary.pending} 条。`);
note(main,'A6','A/C 为 AI 首次编码参照；两组均已用于规则开发，达到工作目标不等于独立验证通过。');
const metricStart=36;
const metricIndex=new Map(data.metrics.map((m,i)=>[[m.scope,m.dimension,m.reference,m.method].join('/'),metricStart+1+i]));
for(const [scope,start] of [['H427',8],['current1268',18]]){
  val(main,`A${start}`,scope==='H427'?'427 条比较组':'1,268 条比较组');
  main.getRange(`A${start+1}:K${start+1}`).values=[['维度','v27—A κ','v27—C κ','v28—A κ','v28—C κ','A工作目标','C工作目标','原LLM—A κ','原LLM—C κ','A配对数','C配对数']];
  header(main,`A${start+1}:K${start+1}`);
  dims.forEach((d,i)=>{
    const r=start+2+i;val(main,`A${r}`,names[d]);
    const index=(m,a)=>metricIndex.get([scope,d,a,m].join('/'));
    main.getRange(`B${r}:K${r}`).formulas=[[
      `=L${index('rules_v27','A')}`,`=L${index('rules_v27','C')}`,
      `=L${index('rules_v28','A')}`,`=L${index('rules_v28','C')}`,
      `=IF(D${r}>=$B$4,"达到目标","未达目标")`,`=IF(E${r}>=$B$4,"达到目标","未达目标")`,
      `=L${index('llm_unchanged','A')}`,`=L${index('llm_unchanged','C')}`,
      `=I${index('rules_v28','A')}`,`=I${index('rules_v28','C')}`]];
  });
  main.getRange(`B${start+2}:E${start+6}`).setNumberFormat('0.000');
  main.getRange(`H${start+2}:I${start+6}`).setNumberFormat('0.000');
  main.getRange(`J${start+2}:K${start+6}`).setNumberFormat('0');
  main.getRange(`D${start+2}:E${start+6}`).conditionalFormats.add('cellIs',{operator:'lessThan',formula:'$B$4',format:{fill:'#FFF1E6',font:{color:'#9B3C10'}}});
}
val(main,'A27','规则达到目标');main.getRange('B27').formulas=[['=COUNTIFS(F10:G14,"达到目标")+COUNTIFS(F20:G24,"达到目标")']];
val(main,'C27','/ 20 项');
note(main,'A29',`复核 ${data.summary.reviewed_unique_units} 条不同原文、${data.summary.reviewed_unit_dimensions} 个维度判断，覆盖全部 257 条原始分歧。`);
note(main,'A30',`与任一参照有分歧的原文：${data.summary.initial_discrepant_units} 条变为 ${data.summary.residual_discrepant_units} 条；新出现分歧 ${data.summary.new_discrepant_units} 条。`);
note(main,'A31','固定配对数，不改首次 A/C；原 LLM 未重跑，不能把本轮规则改善写成 LLM 改善。');
note(main,'A32','未完成新独立样本检验。κ、精确率和召回率描述相对参照表现，不能单独验证部门排序。');
val(main,'A34','配对计数与指标计算');
note(main,'A35','来源：封存的原 A/C 标签、v27/v28 预测及原 LLM 结果；每个维度与参照沿用 v27 共同可判条目。');
main.getRange(`A${metricStart}:S${metricStart}`).values=[['样本组','维度','参照','方法','TP','FP','FN','TN','配对数 n','观察一致率','偶然一致率','Cohen κ','精确率','召回率','F1','参照阳性数','预测阳性数','分歧标签数','κ工作目标']];
header(main,`A${metricStart}:S${metricStart}`);
const input=data.metrics.map(m=>[m.scope,names[m.dimension],m.reference,methods[m.method],m.confusion.TP,m.confusion.FP,m.confusion.FN,m.confusion.TN]);
main.getRange(`A${metricStart+1}:H${metricStart+input.length}`).values=input;
main.getRange(`I${metricStart+1}:S${metricStart+input.length}`).formulas=input.map((_,i)=>{const r=metricStart+1+i;return [
  `=SUM(E${r}:H${r})`,`=(E${r}+H${r})/I${r}`,
  `=((E${r}+F${r})*(E${r}+G${r})+(G${r}+H${r})*(F${r}+H${r}))/(I${r}*I${r})`,
  `=IF(K${r}=1,"n.a.",(J${r}-K${r})/(1-K${r}))`,
  `=IF(E${r}+F${r}=0,"n.a.",E${r}/(E${r}+F${r}))`,
  `=IF(E${r}+G${r}=0,"n.a.",E${r}/(E${r}+G${r}))`,
  `=IF(2*E${r}+F${r}+G${r}=0,"n.a.",2*E${r}/(2*E${r}+F${r}+G${r}))`,
  `=E${r}+G${r}`,`=E${r}+F${r}`,`=F${r}+G${r}`,
  `=IF(ISNUMBER(L${r}),IF(L${r}>=$B$4,"达到目标","未达目标"),"无法计算")`];});
main.getRange('E37:I96').setNumberFormat('0');main.getRange('J37:K96').setNumberFormat('0.0%');
main.getRange('L37:L96').setNumberFormat('0.000');main.getRange('M37:O96').setNumberFormat('0.0%');
main.getRange('P37:R96').setNumberFormat('0');main.tables.add('A36:S96',true,'AgreementCalculations');

const revHeads=['条目ID','样本组','维度','材料类型','原文','v27标签','专项复核标签','v28标签','A首次标签','C首次标签','原句证据','专项复核理由','上下文依据','对原分歧的复核意见','规则是否改变','本轮与复核相符','来源'];
function contextText(value){
  if(!value)return '';
  if(Array.isArray(value))return value.map(contextText).filter(Boolean).join('\n\n');
  if(typeof value!=='object')return String(value);
  const quote=value.quote||value.text;
  const location=[value.paragraph_id, value.pages?.length?`页 ${value.pages.join('、')}`:'',value.source_lines?.length?`行 ${value.source_lines.join('、')}`:''].filter(Boolean).join('，');
  return [location,quote,value.context?contextText(value.context):'',value.usage?`用途：${value.usage}`:''].filter(Boolean).join('\n')||JSON.stringify(value);
}
const reviewRows=data.reviews.map(r=>[r.id,r.scope,names[r.dimension],r.packet_role,r.text,r.old_rule,r.semantic_review,r.new_rule,r.A,r.C,r.evidence.join('；'),r.reason,contextText(r.context_evidence),r.review_assessment,r.changed?'是':'否',r.new_matches_review?'是':'否',r.source]);
base(review,`A1:Q${reviewRows.length+4}`);val(review,'A2','开发期专项复核记录');
note(review,'A3','复核意见单独保存，未替换首次 A/C；不是新的独立验证或真人金标准。');
review.getRange('A4:Q4').values=[revHeads];review.getRange(`A5:Q${reviewRows.length+4}`).values=reviewRows;header(review,'A4:Q4');
review.getRange(`A1:D${reviewRows.length+4}`).format.columnWidth=20;
review.getRange(`E1:E${reviewRows.length+4}`).format.columnWidth=95;
review.getRange(`F1:J${reviewRows.length+4}`).format.columnWidth=11;
review.getRange(`K1:M${reviewRows.length+4}`).format.columnWidth=65;
review.getRange(`N1:N${reviewRows.length+4}`).format.columnWidth=26;
review.getRange(`O1:P${reviewRows.length+4}`).format.columnWidth=17;
review.getRange(`Q1:Q${reviewRows.length+4}`).format.columnWidth=80;
review.getRange(`E5:Q${reviewRows.length+4}`).format.wrapText=true;
const textHeight=(value,width)=>String(value||'').split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/width)),0)*15+10;
reviewRows.forEach((r,i)=>review.getRange(`A${i+5}:Q${i+5}`).format.rowHeight=Math.min(409,Math.max(48,textHeight(r[4],50),...r.slice(10,13).map(v=>textHeight(v,36)))));
review.freezePanes.freezeRows(4);review.freezePanes.freezeColumns(4);review.tables.add(`A4:Q${reviewRows.length+4}`,true,'SemanticReview');

const amendRows=[];
function flattenAmendments(group,key,value){
  if(Array.isArray(value)) value.forEach((v,i)=>flattenAmendments(group,`${key} / ${i+1}`,v));
  else if(value && typeof value==='object') for(const [k,v] of Object.entries(value)) flattenAmendments(group,key?`${key} / ${k}`:k,v);
  else amendRows.push([group,key,value===null?'未提供':String(value)]);
}
for(const [g,log] of Object.entries(data.amendments)) flattenAmendments(g,'',log);
base(rules,`A1:C${amendRows.length+4}`);val(rules,'A2','规则修订依据与限制');
rules.getRange('A4:C4').values=[['专项组','记录项','具体内容']];header(rules,'A4:C4');
rules.getRange(`A5:C${amendRows.length+4}`).values=amendRows;
rules.getRange(`A1:A${amendRows.length+4}`).format.columnWidth=12;rules.getRange(`B1:B${amendRows.length+4}`).format.columnWidth=35;
rules.getRange(`C1:C${amendRows.length+4}`).format.columnWidth=135;rules.getRange(`C5:C${amendRows.length+4}`).format.wrapText=true;
amendRows.forEach((r,i)=>rules.getRange(`A${i+5}:C${i+5}`).format.rowHeight=Math.min(409,Math.max(44,(r[2].split('\n').length+Math.ceil(r[2].length/110))*13+8)));
rules.freezePanes.freezeRows(4);rules.tables.add(`A4:C${amendRows.length+4}`,true,'RuleAmendments');

const allHeads=['条目ID','样本组','原文',...dims.map(d=>'v28_'+d),...dims.map(d=>'v27_'+d),...dims.map(d=>'A_'+d),...dims.map(d=>'C_'+d),'变更维度',...dims.map(d=>'证据_'+d),'来源'];
const allRows=data.all_rows.map(r=>[r.id,r.scope,r.text,...dims.map(d=>r.after[d]),...dims.map(d=>r.before[d]),...dims.map(d=>r.references.A?.[d]??null),...dims.map(d=>r.references.C?.[d]??null),r.changed_dimensions,...dims.map(d=>r.evidence[d]),r.source]);
base(all,`A1:AD${allRows.length+1}`);all.getRange('A1:AD1').values=[allHeads];all.getRange(`A2:AD${allRows.length+1}`).values=allRows;header(all,'A1:AD1');
all.getRange(`A1:B${allRows.length+1}`).format.columnWidth=21;all.getRange(`C1:C${allRows.length+1}`).format.columnWidth=110;
all.getRange(`D1:X${allRows.length+1}`).format.columnWidth=10;all.getRange(`Y1:AC${allRows.length+1}`).format.columnWidth=65;
all.getRange(`AD1:AD${allRows.length+1}`).format.columnWidth=80;
all.getRange(`C2:C${allRows.length+1}`).format.wrapText=true;all.getRange(`Y2:AD${allRows.length+1}`).format.wrapText=true;
allRows.forEach((r,i)=>all.getRange(`A${i+2}:AD${i+2}`).format.rowHeight=Math.min(409,Math.max(30,Math.ceil(r[2].length/60)*14+8)));
all.freezePanes.freezeRows(1);all.freezePanes.freezeColumns(2);all.tables.add(`A1:AD${allRows.length+1}`,true,'AllPredictions');

const metricNames={kappa:'Cohen κ',agreement:'观察一致率 / Accuracy',precision:'精确率 Precision',recall:'召回率 Recall',f1:'阳性 F1'};
const ciRows=[];
for(const r of extended.records) for(const [metric,x] of Object.entries(r.metrics)) ciRows.push([
 r.scope,names[r.dimension],r.method==='A_C'?'A与C':methods[r.method],r.reference,r.n,r.source_clusters,
 r.reference_positive_n,r.prediction_positive_n,metricNames[metric],x.estimate,x.ci95.low,x.ci95.high,x.ci95.defined_repetitions]);
base(ci,`A1:M${ciRows.length+5}`);val(ci,'A2','逐维指标及95%区间');
note(ci,'A3','按来源文件聚类 bootstrap 5,000 次；开发材料条件区间，不包含规则选择或系统标注误差。');
note(ci,'A4','各指标分别排除无定义重复并报告有效次数；A/C为AI参照。A—C只报告一致性，不当作分类正确率。');
ci.getRange('A5:M5').values=[['样本组','维度','方法','参照','配对数','文件簇数','参照阳性数','预测阳性数','指标','估计值','95%下限','95%上限','有效重复数']];
header(ci,'A5:M5');ci.getRange(`A6:M${ciRows.length+5}`).values=ciRows;
ci.getRange(`A1:B${ciRows.length+5}`).format.columnWidth=18;ci.getRange(`C1:C${ciRows.length+5}`).format.columnWidth=24;
ci.getRange(`D1:H${ciRows.length+5}`).format.columnWidth=14;ci.getRange(`I1:I${ciRows.length+5}`).format.columnWidth=31;
ci.getRange(`J1:M${ciRows.length+5}`).format.columnWidth=15;ci.getRange(`J6:L${ciRows.length+5}`).setNumberFormat('0.000');
ci.freezePanes.freezeRows(5);ci.tables.add(`A5:M${ciRows.length+5}`,true,'ExtendedIntervals');
const acRows=extended.records.filter(r=>r.method==='A_C').map(r=>[r.scope,names[r.dimension],r.n,r.excluded_n,
 r.prediction_positive_n,r.reference_positive_n,r.metrics.agreement.estimate,r.metrics.kappa.estimate,
 r.metrics.kappa.ci95.low,r.metrics.kappa.ci95.high,r.confusion.TP,r.confusion.FP,r.confusion.FN,r.confusion.TN]);
base(ac,'A1:N16');val(ac,'A2','A与C首次提交的一致性');note(ac,'A3','按双方共同0/1条目计算；不以协商后的相同标签计算信度。现有结果为AI agent判读。');
ac.getRange('A5:N5').values=[['样本组','维度','配对数','排除数','A阳性数','C阳性数','观察一致率','Cohen κ','κ 95%下限','κ 95%上限','双方1','A1/C0','A0/C1','双方0']];header(ac,'A5:N5');
ac.getRange('A6:N15').values=acRows;ac.getRange('A1:N16').format.columnWidth=16;ac.getRange('G6:J15').setNumberFormat('0.000');
ac.freezePanes.freezeRows(5);ac.tables.add('A5:N15',true,'ACAgreement');

wb.recalculate();
let numeric=main.getRange('L37:O96').values;
data.metrics.forEach((m,i)=>[m.kappa,m.precision,m.recall,m.f1].forEach((expected,j)=>{
  if(expected===null){if(numeric[i][j]!=='n.a.')throw new Error(`Expected n.a. at ${i},${j}`);}
  else if(!Number.isFinite(numeric[i][j]) || Math.abs(numeric[i][j]-expected)>1e-10)throw new Error(`Metric mismatch ${i},${j}`);
}));
if(main.getRange('B27').values[0][0]!==data.summary.rules_v28_at_target)throw new Error('Threshold count mismatch');
// Verify the live working-target formulas and restore the recorded target.
val(main,'B4',1);wb.recalculate();
const atOne=main.getRange('B27').values[0][0];
const expectedOne=data.matrix.reduce((n,r)=>n+Number(r.rules_v28_A>=1)+Number(r.rules_v28_C>=1),0);
if(atOne!==expectedOne)throw new Error('Target formula does not update');
val(main,'B4',0.8);wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'κ与工作目标!A9:K14',include:'values,formulas',tableMaxRows:6,tableMaxCols:11,maxChars:2600})).ndjson);
const errorScan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:1000});
console.log(errorScan.ndjson);
for(const [sheetName,range,file] of [['κ与工作目标','A1:K32','summary'],['κ与工作目标','A36:S41','calculations'],['逐条复核','A4:J8','review'],['逐条复核','K4:P7','reasons'],['规则调整','A1:C7','amendments'],['全量编码','A1:H5','full'],['完整指标与区间','A1:M10','intervals'],['A与C一致性','A1:J10','ac']]){
 const blob=await wb.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(path.join(dir,`${file}-preview.png`),new Uint8Array(await blob.arrayBuffer()));
}
const exported=await SpreadsheetFile.exportXlsx(wb);await exported.save(path.join(dir,'自动规则复核与κ对照-v28.xlsx'));
await fs.writeFile(path.join(dir,'workbook_verification.json'),JSON.stringify({formula_metrics_checked:240,formula_metrics_match:true,threshold_dynamic_check:true,full_rows:allRows.length,review_dimension_rows:reviewRows.length,generated_at:new Date().toISOString()},null,2));
console.log('Saved 自动规则复核与κ对照-v28.xlsx');
