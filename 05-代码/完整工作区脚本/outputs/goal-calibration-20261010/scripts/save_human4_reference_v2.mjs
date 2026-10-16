import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const ROOT='/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010';
const SUPPORT=path.join(ROOT,'logs/human4-reference-v2-delivery');
const data=JSON.parse(await fs.readFile(path.join(SUPPORT,'edit-inputs.json'),'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const outputs=[];
for(const b of [data.source_packet_binding,...data.source_bindings,...data.jobs.map(x=>x.source)]) {
  if(sha(await fs.readFile(b.path))!==b.sha256)throw Error('Changed bound source '+b.path);
}
for(const [index,job] of data.jobs.entries()) {
  try {await fs.access(job.target); throw Error('Destination already exists '+job.target);} catch(e){if(e.code!=='ENOENT')throw e;}
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(job.source.path));
  const s=wb.worksheets.getItem('编码表');
  for(const change of job.changes) {
    if(s.getRange(`D${change.row}`).values[0][0]!==0)throw Error('Unexpected previous value');
    s.getRange(`D${change.row}:E${change.row}`).values=[[1,change.reason]];
    s.getRange(`H${change.row}`).values=[[change.context]];
  }
  s.getRange('A4').values=[['最新4项真人局部复核值均已另存为1。E列依据由AI按完整材料整理；此次核验属于事后校准。D/E可直接修改，完整证据见H列。']];
  const context=wb.worksheets.getItem('原文语境');
  context.getRange('A4').values=[['原77条材料保留；第851—893行补入本轮4项真人核验使用的完整同版材料与共同手册。␌表示原PDF换页符。']];
  const end=data.appendix_start_row+data.appendix_rows.length-1;
  context.getRange(`A${data.appendix_start_row}:F${end}`).values=data.appendix_rows;
  context.getRange(`A${data.appendix_start_row}:F${end}`).format.font={name:'Arial',size:10,color:'#243044'};
  context.getRange(`A${data.appendix_start_row}:F${end}`).format.wrapText=true;
  context.getRange(`A${data.appendix_start_row}:F${end}`).format.verticalAlignment='top';
  data.appendix_rows.forEach((row,i)=>{
    const lines=row[4].split('\n').reduce((sum,x)=>sum+Math.max(1,Math.ceil([...x].length/55)),0);
    context.getRange(`A${data.appendix_start_row+i}:F${data.appendix_start_row+i}`).format.rowHeight=Math.max(65,Math.min(409,lines*14+12));
  });
  wb.recalculate();
  const checks=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:15},maxChars:2500});
  await fs.writeFile(path.join(SUPPORT,`reference-${index}-error-scan.ndjson`),checks.ndjson);
  for(const [sheetName,range,slug] of [['编码表','A6:E8','first'],['编码表','A178:E180','price'],['编码表','A214:E217','support'],['原文语境','A851:F852','context']]){
    const preview=await wb.render({sheetName,range,scale:1,format:'png'});
    await fs.writeFile(path.join(SUPPORT,`reference-${index}-${slug}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  const output=await SpreadsheetFile.exportXlsx(wb);await output.save(job.target);
  const raw=await fs.readFile(job.target);
  outputs.push({path:job.target,sha256:sha(raw),bytes:raw.length});
}
await fs.writeFile(path.join(SUPPORT,'authoring-verification.json'),JSON.stringify({outputs,labels_saved_per_table:4,raw_firsts_modified:false,formal_acceptance:false},null,2)+'\n');
console.log(JSON.stringify({outputs,labels_saved_per_table:4}));
