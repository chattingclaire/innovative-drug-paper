import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(await fs.readFile(path.join(HERE,'workbook-input.json'),'utf8'));
const output=path.join(HERE,'创新性与公平性-全部阳性查看表.xlsx');
assert(!(await fs.access(output).then(()=>true,()=>false)),'Existing output must be preserved');
const wb=Workbook.create();
const reviews=[];
const units=s=>[...String(s??'')].reduce((n,c)=>n+(c.codePointAt(0)>255?2:1),0);
for(let z=0;z<data.sheets.length;z++){
 const item=data.sheets[z],sheet=wb.worksheets.add(item.name);
 const last=String.fromCharCode(64+item.headers.length),end=4+item.rows.length;
 sheet.getRange(`A1:${last}${end}`).format.font={name:'Arial',size:10,color:'#20252B'};
 sheet.getRange('A1').values=[[item.name]];
 sheet.getRange(`A1:${last}1`).format.font={name:'Arial',size:14,bold:true,color:'#20252B'};
 sheet.getRange('A2').values=[[item.context]];
 sheet.getRange(`A2:${last}2`).format.font={name:'Arial',size:10,italic:true,color:'#5B6470'};
 sheet.getRange('A1:A2').format.wrapText=false;
 sheet.getRange(`A4:${last}4`).values=[item.headers];
 sheet.getRange(`A4:${last}4`).format={fill:'#334155',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:34,horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
 const matrix=item.rows.map(r=>r.values);
 sheet.getRange(`A5:${last}${end}`).values=matrix;
 sheet.getRange(`A5:${last}${end}`).format.verticalAlignment='top';
 const widths=z===0?{A:19,B:25,C:12,D:11,E:12,F:12,G:17,H:34,I:100,J:100,K:160,L:46,M:46}:{A:25,B:12,C:11,D:12,E:20,F:40,G:100,H:100,I:160,J:46};
 for(const [col,width] of Object.entries(widths))sheet.getRange(`${col}1:${col}${end}`).format.columnWidth=width;
 const textStart=z===0?'H':'F';
 sheet.getRange(`${textStart}5:${last}${end}`).format.wrapText=true;
 const numberRange=z===0?`E5:G${end}`:`D5:E${end}`;
 sheet.getRange(numberRange).setNumberFormat('0');
 sheet.getRange(numberRange).format.horizontalAlignment='right';
 sheet.getRange(`A5:A${end}`).format.font={name:'Arial',size:10,color:'#0563C1'};
 for(let i=0;i<item.rows.length;i++){
  let lineN=2;
  for(let j=z===0?7:5;j<item.headers.length;j++){
   const w=widths[String.fromCharCode(65+j)];
   const n=String(matrix[i][j]??'').split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(units(line)/(w-4))),0);
   lineN=Math.max(lineN,n);
  }
  sheet.getRange(`A${i+5}:${last}${i+5}`).format.rowHeight=Math.min(409,Math.max(44,lineN*15+14));
 }
 const suggested=z===0?`G5:G${end}`:`E5:E${end}`;
 sheet.getRange(suggested).conditionalFormats.add('containsText',{text:'待定',format:{fill:'#FFF2CC',font:{color:'#854D0E'}}});
 sheet.getRange(suggested).conditionalFormats.add('cellIs',{operator:'equal',formula:0,format:{fill:'#FCE4D6',font:{color:'#9C2A16'}}});
 sheet.freezePanes.freezeRows(4);sheet.freezePanes.freezeColumns(z===0?4:3);sheet.showGridLines=false;
 assert.deepEqual(sheet.getRange(`A5:${last}${end}`).values,matrix);
 reviews.push({sheet:item.name,row_N:item.rows.length,all_values_match:true});
}
wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:1500});
await fs.mkdir(path.join(HERE,'previews'),{recursive:true});
for(let z=0;z<data.sheets.length;z++){
 const item=data.sheets[z],sheet=wb.worksheets.getItem(item.name);
 const region=z===0?'A1:J6':'A1:H6';
 const blob=await wb.render({sheetName:item.name,range:region,scale:1,format:'png'});
 await fs.writeFile(path.join(HERE,'previews',`${z}-opening.png`),new Uint8Array(await blob.arrayBuffer()));
 let idx=0;
 for(let i=1;i<item.rows.length;i++)if(String(item.rows[i].values[z===0?8:6]).length>String(item.rows[idx].values[z===0?8:6]).length)idx=i;
 const r=idx+5,range=z===0?`H${r}:K${r}`:`F${r}:I${r}`;
 const longest=await wb.render({sheetName:item.name,range,scale:1,format:'png'});
 await fs.writeFile(path.join(HERE,'previews',`${z}-longest.png`),new Uint8Array(await longest.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(output);
await fs.writeFile(path.join(HERE,'artifact-checks.json'),JSON.stringify({sheets:reviews,errors:errors.ndjson,native_material_hyperlinks_pending:true},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({output,rows:data.sheets.map(x=>x.rows.length),exported:true,native_hyperlinks_pending:true}));
