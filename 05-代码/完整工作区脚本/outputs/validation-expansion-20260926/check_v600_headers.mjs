// Read-only import/render of the delivered workbook; no cell changes or export.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.join(path.dirname(fileURLToPath(import.meta.url)),'V600工作簿交付');
const sha=x=>createHash('sha256').update(x).digest('hex');
for(const coder of ['A','C']){
 const file=path.join(root,`新增验证600-${coder}-AI评审.xlsx`),before=await fs.readFile(file);
 const book=await SpreadsheetFile.importXlsx(await FileBlob.load(file));
 const check=await book.inspect({kind:'table',range:'独立盲评!A1:J4',include:'values,formulas',tableMaxRows:4,tableMaxCols:10,maxChars:2000});
 const picture=await book.render({sheetName:'独立盲评',range:'A1:J4',scale:1,format:'png'});
 if(sha(await fs.readFile(file))!==sha(before))throw Error('Read-only workbook changed');
 await fs.writeFile(path.join(root,`v600-${coder}-full-heading.png`),new Uint8Array(await picture.arrayBuffer()),{flag:'wx'});
 await fs.writeFile(path.join(root,`v600-${coder}-full-heading-inspection.ndjson`),check.ndjson,{flag:'wx'});
 console.log(JSON.stringify({coder,workbook_sha256:sha(before),reimport_header_rendered:true,workbook_modified:false}));
}
