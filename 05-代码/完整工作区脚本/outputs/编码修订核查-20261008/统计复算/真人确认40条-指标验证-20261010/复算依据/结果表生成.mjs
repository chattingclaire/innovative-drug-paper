import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const d=JSON.parse(await fs.readFile('/tmp/validation40-workbook-data.json','utf8'));
const wb=Workbook.create();
const result=wb.worksheets.add('指标结果');
const diff=wb.worksheets.add('差异清单');
const data=wb.worksheets.add('逐维对照');
const names={S:'安全性',E:'有效性',Ec:'经济性',I:'创新性',F:'公平性'};
const methods={rule:'规则法',llm:'大模型'};
const font={name:'Arial',size:11,color:'#243247'};
function setup(s,range){s.showGridLines=false;s.getRange(range).format.font=font;s.getRange(range).format.verticalAlignment='center';s.getRange(range).format.rowHeight=27;}
function header(s,range){const r=s.getRange(range);r.format.fill='#233B5D';r.format.font={...font,bold:true,color:'#FFFFFF'};r.format.wrapText=true;r.format.horizontalAlignment='center';r.format.rowHeight=42;r.format.borders={insideVertical:{style:'thin',color:'#FFFFFF'}};}
function widths(s,arr){arr.forEach((w,i)=>s.getRangeByIndexes(0,i,1,1).format.columnWidthPx=w);}
function value(s,cell,v){s.getRange(cell).values=[[v]];}
function formula(s,cell,v){s.getRange(cell).formulas=[[v]];}
setup(result,'A1:O30'); setup(diff,`A1:I${d.differences.length+5}`);setup(data,'A1:R201');
result.tabColor='#233B5D';
widths(result,[95,86,72,86,100,72,85,90,90,90,88,92,92,88,96]);
widths(diff,[88,90,88,83,80,80,540,265,150]);
widths(data,[88,150,70,86,86,86,86,78,78,510,265,250,180,130,28,95,100,100]);
value(result,'A2','40条复核指标验证');result.getRange('A2').format.font={...font,size:16,bold:true};
result.getRange('A3:O3').format.borders={bottom:{style:'thin',color:'#B5C2D2'}};
value(result,'A3','参照：于小迪、陈海婷确认一致的40条结论。每条五维，共200项。确认转述日期：2026-10-10。');
result.getRange('A5:I5').values=[['方法','材料数','标签数','一致项数','标签一致率','差异项数','五维全同条数','宏平均F1','微平均F1']];header(result,'A5:I5');
result.getRange('A10:O10').values=[['方法','维度','材料数','参照为1','机器为1','TP','FP','FN','TN','一致率','Cohen κ','精确率','召回率','F1','偶然一致率']];header(result,'A10:O10');
const rawHeaders=['材料编号','原始编号','部门','维度','确认参照','规则预测','大模型预测','规则一致','大模型一致','确认理由','语境对照','材料来源','来源位置','参照单元格'];
data.getRange('A1:N1').values=[rawHeaders];
data.getRange('A2:N201').values=d.data.map((r,i)=>[r.material_id,r.global_id,r.department,r.dimension_name,r.reference,r.rule,r.llm,null,null,r.reference_reason,r.context_comparison,r.source_name,r.source_locator,`${String.fromCharCode(67+i%5)}${6+Math.floor(i/5)}`]);
for(let r=2;r<=201;r++){
 formula(data,`H${r}`,`=IF(E${r}=F${r},1,0)`);formula(data,`I${r}`,`=IF(E${r}=G${r},1,0)`);
}
const dt=data.tables.add('A1:N201',true,'PairedLabels');dt.style='TableStyleLight9';header(data,'A1:N1');
data.getRange('A2:N201').format.rowHeight=70;
data.getRange('J2:N201').format.wrapText=true;
data.getRange('E2:I201').setNumberFormat('0');
data.getRange('E2:I201').format.horizontalAlignment='center';
data.getRange('H2:I201').conditionalFormats.add('cellIs',{operator:'equal',formula:0,format:{fill:'#FFF1DF',font:{color:'#8B4C13',bold:true}}});
data.freezePanes.freezeRows(1);data.freezePanes.freezeColumns(4);
data.getRange('P1:R1').values=[['材料编号','规则一致项','模型一致项']];header(data,'P1:R1');
data.getRange('P2:P41').values=d.references.map(r=>[r.material_id]);
for(let r=2;r<=41;r++){
 formula(data,`Q${r}`,`=COUNTIFS($A$2:$A$201,P${r},$H$2:$H$201,1)`);
 formula(data,`R${r}`,`=COUNTIFS($A$2:$A$201,P${r},$I$2:$I$201,1)`);
}
const sourceLines=[
 ['确认方式','用户转述两位真人对当前复核结果均无异议；A为于小迪，B为陈海婷。'],
 ['确认范围','40条结论；两份表共200个相同标签。未据此计算独立盲法人际信度。'],
 ['理由来源','本表理由引自A表“复核记录”G列。两表标签相同，理由文字可不同，原表均已存档。'],
 ['A表',d.manifest.workbooks.A.path],['B表',d.manifest.workbooks.B.path],
 ['规则来源',d.manifest.rule_bindings.rule_output.path],['模型来源',d.manifest.llm_bindings.llm_output.path],
 ['校准手册',d.manifest.rule_bindings.calibration_manual.path],['机器手册',d.manifest.rule_bindings.machine_manual.path],
 ['匹配情况','40条目标原文、来源一致。2条语境文本与顺序相同；20条校准片段均能逐字找到。'],
 ['语境说明','片段新增或改写不等于机器未读其语义。各项差异也可能来自手册边界变化。'],
 ['统计口径','固定有目的校准样本内的未加权描述。分母为0显示未定义；无总体置信区间。'],
 ['来源记录','完整哈希、固定标签及用户确认原话见同目录“确认与版本记录.json”和存档。']
];
data.getRange('T1').format.columnWidthPx=110;data.getRange('U1').format.columnWidthPx=740;
data.getRange('T1:U1').values=[['来源项目','内容']];header(data,'T1:U1');
data.getRange(`T2:U${sourceLines.length+1}`).values=sourceLines;
data.getRange(`T2:U${sourceLines.length+1}`).format.font=font;
data.getRange(`T2:U${sourceLines.length+1}`).format.wrapText=true;
data.getRange(`T2:U${sourceLines.length+1}`).format.verticalAlignment='center';
data.getRange(`T2:U${sourceLines.length+1}`).format.rowHeight=90;

const dimRange="'逐维对照'!$D$2:$D$201", refRange="'逐维对照'!$E$2:$E$201";
for(let i=0;i<d.metrics.length;i++){
 const m=d.metrics[i],r=11+i,predRange=`'逐维对照'!$${m.method==='rule'?'F':'G'}$2:$${m.method==='rule'?'F':'G'}$201`;
 result.getRange(`A${r}:B${r}`).values=[[methods[m.method],names[m.dimension]]];
 const count=(p,ref)=>`=COUNTIFS(${dimRange},B${r},${predRange},${p},${refRange},${ref})`;
 formula(result,`C${r}`,`=SUM(F${r}:I${r})`);
 formula(result,`D${r}`,`=F${r}+H${r}`);formula(result,`E${r}`,`=F${r}+G${r}`);
 formula(result,`F${r}`,count(1,1));formula(result,`G${r}`,count(1,0));formula(result,`H${r}`,count(0,1));formula(result,`I${r}`,count(0,0));
 formula(result,`J${r}`,`=IF(C${r}=0,"未定义",(F${r}+I${r})/C${r})`);
 formula(result,`O${r}`,`=IF(C${r}=0,"未定义",(D${r}*E${r}+(C${r}-D${r})*(C${r}-E${r}))/(C${r}*C${r}))`);
 formula(result,`K${r}`,`=IF(O${r}=1,"未定义",(J${r}-O${r})/(1-O${r}))`);
 formula(result,`L${r}`,`=IF(F${r}+G${r}=0,"未定义",F${r}/(F${r}+G${r}))`);
 formula(result,`M${r}`,`=IF(F${r}+H${r}=0,"未定义",F${r}/(F${r}+H${r}))`);
 formula(result,`N${r}`,`=IF(2*F${r}+G${r}+H${r}=0,"未定义",2*F${r}/(2*F${r}+G${r}+H${r}))`);
 if(i%2===1)result.getRange(`A${r}:O${r}`).format.fill='#F1F4F8';
}
for(const [i,start,end,unitCol] of [[0,11,15,'Q'],[1,16,20,'R']]){
 const r=6+i;value(result,`A${r}`,methods[d.summaries[i].method]);
 formula(result,`B${r}`,"=COUNTA('逐维对照'!P2:P41)");
 formula(result,`C${r}`,`=SUM(C${start}:C${end})`);
 formula(result,`D${r}`,`=SUM(F${start}:F${end})+SUM(I${start}:I${end})`);
 formula(result,`E${r}`,`=D${r}/C${r}`);
 formula(result,`F${r}`,`=C${r}-D${r}`);
 formula(result,`G${r}`,`=COUNTIF('逐维对照'!${unitCol}2:${unitCol}41,5)`);
 formula(result,`H${r}`,`=AVERAGE(N${start}:N${end})`);
 formula(result,`I${r}`,`=2*SUM(F${start}:F${end})/(2*SUM(F${start}:F${end})+SUM(G${start}:G${end})+SUM(H${start}:H${end}))`);
}
result.getRange('B6:D7').setNumberFormat('0');result.getRange('F6:G7').setNumberFormat('0');result.getRange('E6:E7').setNumberFormat('0.0%');result.getRange('H6:I7').setNumberFormat('0.000');
result.getRange('C11:I20').setNumberFormat('0');result.getRange('J11:J20').setNumberFormat('0.0%');result.getRange('K11:N20').setNumberFormat('0.000');result.getRange('O11:O20').setNumberFormat('0.0%');
result.getRange('A16:O16').format.borders={top:{style:'thin',color:'#92A5BF'}};
value(result,'A23','如何读这组结果');result.getRange('A23').format.font={...font,bold:true};
value(result,'A24','本轮差异主要集中在公平性。规则法创新性也有7项与参照不同，均为机器0、参照1。');
value(result,'A25','TP：机器1、参照1；FP：机器1、参照0；FN：机器0、参照1；TN：机器0、参照0。');
value(result,'A26','宏平均F1为五维F1均值；微平均F1合并200项计数。五维全同要求一条材料的五个标签全部一致。');
value(result,'A28','这40条是有目的选取的手册校准材料。机器采用较早手册，语境呈现也有差别，结果用于本轮开发诊断。');
value(result,'A29','这些差异不能全部归因于识别错误，也不能直接作为总体效度或新版手册的独立验证结果。');
result.getRange('A28:O29').format.font={...font,color:'#6B4C29'};

value(diff,'A2','与确认参照不同的31项');diff.getRange('A2').format.font={...font,size:16,bold:true};
value(diff,'A3','规则法21项，大模型10项。方向仅说明机器与参照的0/1差别，相关手册与语境限制见“指标结果”。');
diff.getRange('A5:I5').values=[['材料编号','方法','维度','差异方向','机器预测','确认参照','确认理由','语境对照','原始编号']];
diff.getRange(`A6:I${5+d.differences.length}`).values=d.differences.map(r=>[r.material_id,methods[r.method],r.dimension_name,r.difference_type,r.prediction,r.reference,r.reference_reason,r.context_comparison,r.global_id]);
const ft=diff.tables.add(`A5:I${5+d.differences.length}`,true,'LabelDifferences');ft.style='TableStyleLight9';header(diff,'A5:I5');
diff.getRange(`A6:I${5+d.differences.length}`).format.rowHeight=82;diff.getRange(`D6:H${5+d.differences.length}`).format.wrapText=true;diff.getRange(`E6:F${5+d.differences.length}`).format.horizontalAlignment='center';
diff.freezePanes.freezeRows(5);diff.freezePanes.freezeColumns(3);
wb.recalculate();
// Each worksheet result is compared with the independently computed integer counts.
for(let i=0;i<d.metrics.length;i++){
 const m=d.metrics[i];const actual=result.getRange(`C${11+i}:O${11+i}`).values[0];
 const expected=[m.n,m.reference_positive,m.prediction_positive,m.tp,m.fp,m.fn,m.tn,m.agreement,m.kappa,m.precision,m.recall,m.f1];
 expected.forEach((v,j)=>{if(typeof actual[j]!=='number'||Math.abs(actual[j]-v)>1e-10)throw Error(`metric ${i}/${j}: ${actual[j]} != ${v}`);});
}
for(let i=0;i<2;i++){
 const m=d.summaries[i],actual=result.getRange(`B${6+i}:I${6+i}`).values[0];
 const expected=[40,200,m.label_matches,m.label_agreement,m.n_differences,m.exact_unit_matches,m.macro_f1,m.micro_f1];
 expected.forEach((v,j)=>{if(Math.abs(actual[j]-v)>1e-10)throw Error(`summary ${i}/${j}`);});
}
const inspection=(await wb.inspect({kind:'table',range:'指标结果!A10:O20',include:'values,formulas',tableMaxRows:11,tableMaxCols:15,maxChars:2500})).ndjson;
const errors=(await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:3000})).ndjson;
await fs.writeFile('/tmp/validation40-artifact/inspection.ndjson',inspection+'\n'+errors);
for(const [sheetName,range,file] of [['指标结果','A1:O29','summary'],['差异清单','A1:I10','differences'],['逐维对照','A1:J7','data'],['逐维对照','T1:U7','sources']]){
 const preview=await wb.render({sheetName,range,scale:1.5,format:'png'});await fs.writeFile(`/tmp/validation40-artifact/${file}.png`,new Uint8Array(await preview.arrayBuffer()));
}
await(await SpreadsheetFile.exportXlsx(wb)).save(`${d.out}/40条复核指标验证.xlsx`);
console.log(JSON.stringify({output:`${d.out}/40条复核指标验证.xlsx`,metric_checks:120,summary_checks:16,errors}));
