import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.dirname(fileURLToPath(import.meta.url));
const read=async n=>JSON.parse(await fs.readFile(path.join(root,n),'utf8'));
const metrics=await read('metrics.json');
const history=await read('history_version_audit.json');
const workbookData=await read('workbook_data.json');
const dimNames={S:'安全性',E:'有效性',Ec:'经济性',I:'创新性',F:'公平性'};
const wb=Workbook.create();
const style=(sh,lastCol,lastRow,headerRow)=>{
  sh.showGridLines=false;
  sh.getRange(`A1:${lastCol}${lastRow}`).format.font={name:'Arial',size:10,color:'#223047'};
  sh.getRange(`A${headerRow}:${lastCol}${headerRow}`).format={fill:'#203A5E',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:28};
  sh.getRange(`A1:${lastCol}${lastRow}`).format.verticalAlignment='center';
  sh.freezePanes.freezeRows(headerRow);
};

const main=wb.worksheets.add('五维对照');
main.getRange('A2').values=[['自动规则五维复核']];
main.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#203A5E'};
main.getRange('A3').values=[['A/C为按人工标准盲评的AI编码；两个样本框分别计算，均为已暴露的规则开发材料。']];
const heads=['样本框','维度','参照','共同可判n','旧规则κ','新规则κ','原LLMκ','新规则精确率','新规则召回率','TP','FP','FN','TN'];
main.getRange('A4:M4').values=[heads];
const lines=[];
for(const scope of ['H427','current1268'])for(const d of ['S','E','Ec','I','F'])for(const ref of ['A','C']){
  const entry=metrics.comparisons[scope].references[ref][d];
  const ms=entry.methods;
  const old=ms.rules_v26_2.common_unweighted;
  const next=ms.rules_v27.common_unweighted;
  const llm=ms.llm_unchanged.common_unweighted;
  const c=next.confusion_on_joint_determinate;
  lines.push([scope,dimNames[d],ref,entry.common_n,old.binary_agreement.kappa,next.binary_agreement.kappa,
              llm.binary_agreement.kappa,next.conditional_scores.precision,next.conditional_scores.recall,
              c.TP,c.FP,c.FN,c.TN]);
}
main.getRange(`A5:M${4+lines.length}`).values=lines;
style(main,'M',4+lines.length,4);
main.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#203A5E'};
main.getRange(`E5:G${4+lines.length}`).setNumberFormat('0.000');
main.getRange(`H5:I${4+lines.length}`).setNumberFormat('0.0%');
main.getRange('A1:A24').format.columnWidth=16;
main.getRange('B1:B24').format.columnWidth=14;
main.getRange('C1:C24').format.columnWidth=9;
main.getRange('D1:M24').format.columnWidth=15;

const hist=wb.worksheets.add('历史数值来源');
hist.getRange('A2').values=[['0.867与0.654的来源']];
hist.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#203A5E'};
hist.getRange('A3').values=[['同一批2965条旧原文上分别替换词典与LLM；此表测方法间一致，不能当作人工参照效度。']];
hist.getRange('A4:H4').values=[['规则 / LLM版本','比较句数','五维合并κ','安全性κ','有效性κ','经济性κ','创新性κ','公平性κ']];
const scenarios=[
 ['v2规则 / v2 LLM 全量','v2_dictionary_vs_v2_llm_all3387',3387],
 ['v2规则 / v2 LLM 同批','v2_dictionary_vs_v2_llm_matched2965',2965],
 ['v3规则 / v2 LLM 同批','v3_dictionary_vs_v2_llm_matched2965',2965],
 ['v2规则 / v3 LLM 同批','v2_dictionary_vs_v3_llm_matched2965',2965],
 ['v3规则 / v3 LLM 同批','v3_dictionary_vs_v3_llm_matched2965',2965],
];
hist.getRange('A5:H9').values=scenarios.map(([title,key,n])=>{
  const k=history.kappa[key];
  return [title,n,k.pooled,k['安全性'],k['有效性'],k['经济性'],k['创新性'],k['公平性']];
});
hist.getRange('A12:B15').values=[
 ['旧句数',3387],['新版LLM可对齐句数',2965],
 ['同批词典标签变更条数',history.within_matched_ids_changed_label_sets.dictionary_v2_to_v3],
 ['同批LLM标签变更条数',history.within_matched_ids_changed_label_sets.llm_v2_to_v3],
];
style(hist,'H',15,4);
hist.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#203A5E'};
hist.getRange('C5:H9').setNumberFormat('0.000');
hist.getRange('A1:A15').format.columnWidth=27;
hist.getRange('B1:H15').format.columnWidth=19;

const detail=wb.worksheets.add('逐条变更');
const dh=['ID','样本框','原文','变化维度',
          '旧S','新S','旧E','新E','旧Ec','新Ec','旧I','新I','旧F','新F',
          'A-S','C-S','A-E','C-E','A-Ec','C-Ec','A-I','C-I','A-F','C-F',
          '新S证据','新E证据','新Ec证据','新I证据','新F证据'];
const detailRows=workbookData.rows.filter(r=>r.changed_dimensions).map(r=>{
  const refs=r.references;
  return [r.id,r.scope,r.text,r.changed_dimensions,
          ...['S','E','Ec','I','F'].flatMap(d=>[r.before[d],r.after[d]]),
          ...['S','E','Ec','I','F'].flatMap(d=>[refs.A?.[d]??'',refs.C?.[d]??'']),
          ...['S','E','Ec','I','F'].map(d=>r.evidence[d])];
});
detail.getRange('A1:AC1').values=[dh];
detail.getRange(`A2:AC${detailRows.length+1}`).values=detailRows;
style(detail,'AC',detailRows.length+1,1);
detail.getRange(`A1:A${detailRows.length+1}`).format.columnWidth=20;
detail.getRange(`B1:B${detailRows.length+1}`).format.columnWidth=21;
detail.getRange(`C1:C${detailRows.length+1}`).format.columnWidth=58;
detail.getRange(`D1:D${detailRows.length+1}`).format.columnWidth=14;
detail.getRange(`E1:X${detailRows.length+1}`).format.columnWidth=7;
detail.getRange(`Y1:AC${detailRows.length+1}`).format.columnWidth=34;
detail.freezePanes.freezeColumns(2);

wb.recalculate();
for(const [sheetName,range,file] of [
  ['五维对照','A2:M10','preview_kappa.png'],
  ['历史数值来源','A2:H10','preview_history.png'],
  ['逐条变更','A1:J6','preview_changes.png'],
]){
  const shot=await wb.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(root,file),new Uint8Array(await shot.arrayBuffer()));
}
for(const [sheetName,range] of [['五维对照','A4:M7'],['历史数值来源','A4:H9'],['逐条变更','A1:D4']]){
  const check=await wb.inspect({kind:'table',sheetId:sheetName,range,tableMaxRows:7,tableMaxCols:13,maxChars:1800});
  console.log(sheetName,check.ndjson.slice(0,1800));
}
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'formula errors'});
console.log('error scan',errors.ndjson.slice(0,1000));
const out=await SpreadsheetFile.exportXlsx(wb);
const target=path.join(root,'自动规则五维复核.xlsx');
await out.save(target);
console.log(JSON.stringify({target,comparisons:lines.length,changes:detailRows.length}));
