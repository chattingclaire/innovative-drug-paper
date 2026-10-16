import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const data=JSON.parse(await fs.readFile(new URL('./结果数据.json',import.meta.url),'utf8'));
const outputDir=new URL('.',import.meta.url);
const wb=Workbook.create();
const s=wb.worksheets.add('指标结果');
const raw=wb.worksheets.add('逐项对照');
const material=wb.worksheets.add('阅读材料');
s.showGridLines=false; raw.showGridLines=false;
material.showGridLines=false;
s.tabColor='#243A5A';
const headers=['材料编号','来源编号','部门','维度','维度代码','原A复核','原B复核','裁定参照','自动规则','LLM','当前原文','必要语境','原A复核理由','原B复核理由','追加裁定说明','规则依据','LLM理由'];
const rows=data.raw.map(r=>[r.material_id,r.global_id,r.department,r.dimension_name,r.dimension,r.original_A,r.original_B,r.reference,r.rule,r.LLM,r.current_text,'阅读材料：'+r.material_id,r.A_review_reason,r.B_review_reason,r.adjudication_note,r.rule_reason,r.LLM_reason]);
raw.getRange('A1:Q201').values=[headers,...rows];
raw.getRange('A1:Q201').format.font={name:'Arial',size:11,color:'#243247'};
raw.getRange('A1:Q201').format.verticalAlignment='center';
raw.getRange('A1:Q1').format={fill:'#243A5A',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center',verticalAlignment:'center'};
for(const [cols,w] of [['A1:A201',88],['B1:B201',150],['C1:E201',78],['F1:J201',92],['K1:N201',480],['O1:O201',340],['P1:Q201',480]])raw.getRange(cols).format.columnWidthPx=w;
raw.getRange('F2:J201').format.horizontalAlignment='right';
raw.getRange('K2:Q201').format.wrapText=true;
raw.getRange('K2:Q201').format.verticalAlignment='top';
raw.getRange('K2:Q201').format.autofitRows();
raw.tables.add('A1:Q201',true,'CodingComparison').style='TableStyleLight9';
raw.freezePanes.freezeRows(1);raw.freezePanes.freezeColumns(4);
raw.getRange('H2:H201').conditionalFormats.addCustom('=H2<>F2',{fill:'#FFF0C2'});
raw.getRange('I2:J201').conditionalFormats.addCustom('=I2<>$H2',{fill:'#FDE5E5',font:{color:'#9E2929',bold:true}});

const materialRows=[];
let reconstructedSources=0;
for(let i=1;i<=4;i++){
 const input=JSON.parse(await fs.readFile(new URL('../无答案输入/批次'+String(i).padStart(2,'0')+'.json',import.meta.url),'utf8'));
 for(const u of input.units){
  const sources=[{kind:'当前句段',index:0,text:u.current_text,locator:u.source_name+' '+u.source_locator},...u.contexts.map((text,j)=>({kind:'必要语境',index:j+1,text,locator:(u.context_descriptors[j]?.source_name??u.source_name)+' '+(u.context_descriptors[j]?.source_locator??'所附语境'+(j+1))}))];
  for(const source of sources){
   const chars=Array.from(source.text),parts=[];
   for(let start=0;start<chars.length;start+=220)parts.push(chars.slice(start,start+220).join(''));
   if(parts.join('')!==source.text)throw new Error('Material reconstruction mismatch');
   parts.forEach((text,j)=>materialRows.push([u.material_id,source.kind,source.index,j+1,source.locator,text]));
   reconstructedSources++;
  }
 }
}
const materialLast=materialRows.length+1;
material.getRange('A1:F'+materialLast).values=[['材料编号','来源类型','语境序号','显示片段','来源位置','原文（同一来源按片段顺序连续阅读）'],...materialRows];
material.getRange('A1:F'+materialLast).format.font={name:'Arial',size:11,color:'#243247'};
material.getRange('A1:F1').format={fill:'#243A5A',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center',verticalAlignment:'center'};
material.getRange('A1:D'+materialLast).format.columnWidthPx=90;
material.getRange('E1:E'+materialLast).format.columnWidthPx=290;
material.getRange('F1:F'+materialLast).format.columnWidthPx=780;
material.getRange('A2:F'+materialLast).format.wrapText=true;
material.getRange('A2:F'+materialLast).format.verticalAlignment='top';
material.getRange('A2:F'+materialLast).format.autofitRows();
material.freezePanes.freezeRows(1);material.freezePanes.freezeColumns(2);
material.tables.add('A1:F'+materialLast,true,'SourceMaterials').style='TableStyleLight9';

s.getRange('A1:S61').format.font={name:'Arial',size:11,color:'#243247'};
s.getRange('A1:S61').format.verticalAlignment='center';
s.getRange('A1:S61').format.rowHeight=25;
s.getRange('A2').values=[['40条同手册编码核查']];
s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:'#243A5A'};
s.getRange('A2:H2').format.borders={bottom:{style:'thin',color:'#243A5A'}};
s.getRange('A3').values=[['40条开发材料：医保19、药监18、卫健3；参照为复核结果与校准17追加裁定。']];
s.getRange('A3').format.font={name:'Arial',size:11,italic:true,color:'#627086'};
s.getRange('A4').values=[['项目目标']];
s.getRange('B4').values=[[data.target]];
s.getRange('B4').setNumberFormat('0.00');
s.getRange('C4').values=[['κ、P、R、F1分别核查']];
s.getRange('S6').values=[['说明']];
s.getRange('S7').values=[['P为精确率，R为召回率；两者与F1取值0—1。']];
s.getRange('S9').values=[['0.80为本项目目标。NA表示相应分母为0，不能判达标。']];
s.getRange('S11').values=[['开发分数用于检查执行口径；后续独立检验另行实施。']];
s.getRange('S13').values=[['原A/B的校准17公平性仍为0，裁定参照为1。']];
s.getRange('S15').values=[['表内所有方法与同一裁定参照比较；模型为gpt-5.6-sol。']];
s.getRange('S6:S61').format.columnWidthPx=515;
s.getRange('S6:S61').format.wrapText=false;
s.getRange('S6').format.font={name:'Arial',size:11,bold:true,color:'#243A5A'};
for(const [cols,w] of [['A1:B61',85],['C1:C61',135],['D1:G61',82],['H1:H61',130],['I1:I61',22],['J1:P61',68],['Q1:Q61',90],['R1:R61',24]])s.getRange(cols).format.columnWidthPx=w;
const mainHeader=['范围','维度','编码方法','κ','P','R','F1','目标核查'];
const countHeader=['N','TP','FP','FN','TN','参照1数','机器1数','一致率'];
function headerAt(row){
 s.getRange('A'+row+':H'+row).values=[mainHeader];
 s.getRange('J'+row+':Q'+row).values=[countHeader];
 for(const range of ['A'+row+':H'+row,'J'+row+':Q'+row])s.getRange(range).format={fill:'#243A5A',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center',verticalAlignment:'center'};
}
headerAt(6);headerAt(20);
const positions=[];
let overallRow=7,deptRow=21;
const src="'逐项对照'!";
function countif(dim,dep,predCol,pred,ref){
 const args=[src+'$E$2:$E$201','"'+dim+'"'];
 if(dep!=='总体')args.push(src+'$C$2:$C$201','"'+dep+'"');
 if(predCol)args.push(src+'$'+predCol+'$2:$'+predCol+'$201',String(pred),src+'$H$2:$H$201',String(ref));
 return '=COUNTIFS('+args.join(',')+')';
}
for(const m of data.metrics){
 const row=m.department==='总体'?overallRow++:deptRow++;
 positions.push([row,m]);
 s.getRange('A'+row+':C'+row).values=[[m.department,m.dimension_name,m.method]];
 const predCol=m.method==='自动规则编码'?'I':'J';
 s.getRange('J'+row+':N'+row).formulas=[[
  countif(m.dimension,m.department),
  countif(m.dimension,m.department,predCol,1,1),
  countif(m.dimension,m.department,predCol,1,0),
  countif(m.dimension,m.department,predCol,0,1),
  countif(m.dimension,m.department,predCol,0,0)
 ]];
 s.getRange('O'+row+':Q'+row).formulas=[['=K'+row+'+M'+row,'=K'+row+'+L'+row,'=IF(J'+row+'=0,"NA",(K'+row+'+N'+row+')/J'+row+')']];
 const chance='(O'+row+'*P'+row+'+(J'+row+'-O'+row+')*(J'+row+'-P'+row+'))';
 s.getRange('D'+row+':H'+row).formulas=[[
 '=IF(J'+row+'=0,"NA",IF(J'+row+'^2='+chance+',"NA",(Q'+row+'-'+chance+'/J'+row+'^2)/(1-'+chance+'/J'+row+'^2)))',
 '=IF(K'+row+'+L'+row+'=0,"NA",K'+row+'/(K'+row+'+L'+row+'))',
 '=IF(K'+row+'+M'+row+'=0,"NA",K'+row+'/(K'+row+'+M'+row+'))',
 '=IF(2*K'+row+'+L'+row+'+M'+row+'=0,"NA",2*K'+row+'/(2*K'+row+'+L'+row+'+M'+row+'))',
 '=IF(OR(D'+row+'="NA",E'+row+'="NA",F'+row+'="NA",G'+row+'="NA"),"不可估计",IF(MIN(D'+row+':G'+row+')>=$B$4,"达到0.80","未达到0.80"))'
 ]];
 if(row%2===0)for(const range of ['A'+row+':H'+row,'J'+row+':Q'+row])s.getRange(range).format.fill='#F3F6FA';
}
s.getRange('D7:G50').setNumberFormat('0.000');
s.getRange('Q7:Q50').setNumberFormat('0.0%');
s.getRange('D7:G50').format.horizontalAlignment='right';
s.getRange('J7:Q50').format.horizontalAlignment='right';
s.getRange('D7:G50').conditionalFormats.addCustom('=AND(ISNUMBER(D7),D7<$B$4)',{fill:'#FDE5E5',font:{color:'#9E2929',bold:true}});
s.getRange('H7:H50').conditionalFormats.addCustom('=H7="未达到0.80"',{fill:'#FDE5E5',font:{color:'#9E2929',bold:true}});
s.getRange('H7:H50').conditionalFormats.addCustom('=H7="不可估计"',{fill:'#FFF0C2'});
s.getRange('A53').values=[['原标签κ']];
s.getRange('C53').values=[['复核结果固定快照']];
s.getRange('A53').format.font={name:'Arial',size:11,bold:true,color:'#243A5A'};
s.getRange('S53').values=[['此表保留原标签；A/B复核后的κ不称独立初判信度。']];
s.getRange('A54:G54').values=[['维度','原A—原B','规则—原A','规则—原B','LLM—原A','LLM—原B','规则—LLM']];
s.getRange('A54:G54').format={fill:'#243A5A',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,horizontalAlignment:'center',verticalAlignment:'center'};
s.getRange('A55:G59').values=data.original_review_diagnostic_kappa.map(r=>[r.dimension_name,r['原A—原B'],r['规则—原A'],r['规则—原B'],r['LLM—原A'],r['LLM—原B'],r['规则—LLM']]);
s.getRange('B55:G59').setNumberFormat('0.000');
s.getRange('B55:G59').format.horizontalAlignment='right';
s.getRange('A18').values=[['部门分层结果']];
s.getRange('A18').format.font={name:'Arial',size:11,bold:true,color:'#243A5A'};
wb.recalculate();
let verified=0;
for(const [row,m]of positions){
 const a=s.getRange('D'+row+':G'+row).values[0];
 const b=s.getRange('J'+row+':P'+row).values[0];
 const expected=[m.kappa,m.precision,m.recall,m.F1];
 a.forEach((v,i)=>{if(expected[i]===null){if(v!=='NA')throw new Error('Expected NA '+row);}else if(typeof v!=='number'||Math.abs(v-expected[i])>1e-11)throw new Error('Metric mismatch '+row+' '+v+' '+expected[i]);verified++;});
 const eb=[m.n_valid,m.TP,m.FP,m.FN,m.TN,m.reference_positive,m.prediction_positive];
 b.forEach((v,i)=>{if(v!==eb[i])throw new Error('Counts mismatch '+row+' '+i);verified++;});
 const status=s.getRange('H'+row).values[0][0];
 if(status!==m.project_target_status)throw new Error('Status mismatch '+row+' '+status);
}
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},maxChars:3500});
await fs.writeFile(new URL('./工作簿核查.json',outputDir),JSON.stringify({verified_cells:verified,metric_rows:positions.length,reconstructed_sources:reconstructedSources,material_display_rows:materialRows.length,formula_error_scan:scan.ndjson},null,2));
for(const [sheetName,range,name]of [['指标结果','A2:Q16','指标结果-总体.png'],['指标结果','A18:Q50','指标结果-部门.png'],['指标结果','A52:H59','指标结果-原复核.png'],['逐项对照','A1:J6','逐项对照.png'],['逐项对照','K1:Q3','逐项对照-依据.png'],['阅读材料','A1:F6','阅读材料.png']]){
 const p=await wb.render({sheetName,range,scale:1.25,format:'png'});
 await fs.writeFile(new URL('./'+name,outputDir),new Uint8Array(await p.arrayBuffer()));
}
const f=await SpreadsheetFile.exportXlsx(wb);
await f.save(fileURLToPath(new URL('./40条编码核查结果.xlsx',outputDir)));
console.log(JSON.stringify({saved:fileURLToPath(new URL('./40条编码核查结果.xlsx',outputDir)),verified_cells:verified,metric_rows:positions.length}));
