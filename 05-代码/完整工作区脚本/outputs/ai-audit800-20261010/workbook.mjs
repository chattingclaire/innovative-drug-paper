import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const base=path.dirname(fileURLToPath(import.meta.url));
const input=path.join(base,'source-A/coder-A/formal800-A-frozen.xlsx');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const sheet=wb.worksheets.getItemAt(0);
await fs.mkdir(path.join(base,'checks'),{recursive:true});
console.log((await wb.inspect({kind:'sheet',include:'id,name'})).ndjson);
console.log((await wb.inspect({kind:'table',range:"'初判-pre-release'!A1:E6",tableMaxRows:6,tableMaxCols:5,maxChars:2000})).ndjson);
const mode=process.argv[2]||'inspect';
if(mode==='inspect'){
 const img=await wb.render({sheetName:'初判-pre-release',range:'A1:E6',scale:1,format:'png'});
 await fs.writeFile(path.join(base,'checks/template.png'),new Uint8Array(await img.arrayBuffer()));
}else if(mode==='final'){
 const review=JSON.parse(await fs.readFile(path.join(base,'checks/workbook-data.json'),'utf8'));
 if(review.length!==4000)throw new Error('Expected exactly 4000 judgments');
 sheet.getRange('D2:E4001').values=review;
 // Fit the newly populated reason cells while retaining the supplied columns and rows.
 sheet.getRange('E2:E4001').format.wrapText=true;
 sheet.getRange('A2:E4001').format.autofitRows();
 wb.recalculate();
 console.log((await wb.inspect({kind:'table',range:"'初判-pre-release'!C2:E6",include:'values,formulas',tableMaxRows:5,tableMaxCols:3,maxChars:2500})).ndjson);
 console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'final error scan'})).ndjson);
 for(const [name,range] of [['completed-first','A1:E6'],['completed-middle','A1997:E2001'],['completed-last','A3997:E4001']]){
  const img=await wb.render({sheetName:'初判-pre-release',range,scale:1,format:'png'});
  await fs.writeFile(path.join(base,'checks',name+'.png'),new Uint8Array(await img.arrayBuffer()));
 }
 await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(base,'source-A/coder-A/AI抽检800条-五维结果.xlsx'));
}
