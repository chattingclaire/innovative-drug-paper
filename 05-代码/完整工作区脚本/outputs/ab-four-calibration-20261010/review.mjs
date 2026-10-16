import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root='/Users/rainbow/Desktop/战略院/药企项目-创新药';
const target=root+'/outputs/goal-calibration-20261010/09-delivery/agent-review-20261010/剩余4项单独校准表.xlsx';
const out=root+'/outputs/ab-four-calibration-20261010';
const edit=process.argv.includes('--edit');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(target));
if (!edit) await fs.copyFile(target,out+'/before.xlsx');
if(edit){
 const rows=JSON.parse(await fs.readFile(out+'/judgments.json','utf8'));
 wb.worksheets.getItem('校准表').getRange('D7:E10').values=rows;
 wb.recalculate();
 console.log((await wb.inspect({kind:'table',range:'校准表!A6:E10',include:'values,formulas',tableMaxRows:5,tableMaxCols:5,maxChars:4500})).ndjson);
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#N/A',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
 const xlsx=await SpreadsheetFile.exportXlsx(wb); await xlsx.save(out+'/artifact-edited.xlsx');
}
const blob=await wb.render({sheetName:'校准表',range:'A6:F10',scale:1.2,format:'png'});
await fs.writeFile(out+'/'+(edit?'after':'before')+'.png',new Uint8Array(await blob.arrayBuffer()));
console.log('Rendered',edit?'after':'before');
