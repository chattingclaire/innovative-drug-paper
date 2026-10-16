import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const HERE='/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/09-delivery/targeted-calibration35-root';
const d=JSON.parse(await fs.readFile(path.join(HERE,'workbook-input.json'),'utf8'));
const output=path.join(HERE,'需要定向核定-34条35项.xlsx');
if(await fs.access(output).then(()=>true,()=>false)){
 const repair=JSON.parse(await fs.readFile(path.join(HERE,'question-clarification-before-final-export.json'),'utf8'));
 assert.equal(crypto.createHash('sha256').update(await fs.readFile(output)).digest('hex'),repair.old_draft_sha256);
 assert(repair.labels_and_review_values_unchanged && repair.draft_not_delivered);
 assert(!(await fs.access(path.join(HERE,'saved-readback.json')).then(()=>true,()=>false)));
}
const w=Workbook.create(),s=w.worksheets.add(d.sheet),end=5+d.rows.length;
s.getRange(`A1:H${end}`).format.font={name:'Arial',size:10,color:'#20252B'};
s.getRange('A1').values=[[d.title]];s.getRange('A1:H1').format.font={name:'Arial',size:14,bold:true,color:'#20252B'};
s.getRange('A2').values=[[d.instructions]];s.getRange('A3').values=[[d.identity_note]];
s.getRange('A2:H3').format.font={name:'Arial',size:10,italic:true,color:'#55606F'};
s.getRange('A1:H3').format.wrapText=false;
s.getRange('A5:H5').values=[d.headers];
s.getRange('A5:H5').format={fill:'#334155',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:34,horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
const values=d.rows.map(x=>x.values);s.getRange(`A6:H${end}`).values=values;
s.getRange(`A6:H${end}`).format.verticalAlignment='top';
const widths={A:24,B:9,C:72,D:9,E:72,F:50,G:13,H:13};
for(const [c,width] of Object.entries(widths))s.getRange(`${c}1:${c}${end}`).format.columnWidth=width;
s.getRange(`C6:F${end}`).format.wrapText=true;s.getRange(`D6:E${end}`).format.fill='#FFF6D5';
s.getRange(`D6:D${end}`).setNumberFormat('0');s.getRange(`G6:H${end}`).setNumberFormat('0');
s.getRange(`A6:A${end}`).setNumberFormat('@');
s.getRange(`D6:D${end}`).format.horizontalAlignment='right';s.getRange(`G6:H${end}`).format.horizontalAlignment='right';
s.getRange(`A6:A${end}`).format.font={name:'Arial',size:10,color:'#0563C1'};
const units=v=>[...String(v??'')].reduce((n,c)=>n+(c.codePointAt(0)>255?2:1),0);
for(let i=0;i<values.length;i++){
 let lines=2;
 for(const j of [2,4,5])lines=Math.max(lines,String(values[i][j]??'').split('\n').reduce((n,t)=>n+Math.max(1,Math.ceil(units(t)/(widths[String.fromCharCode(65+j)]-5))),0));
 s.getRange(`A${i+6}:H${i+6}`).format.rowHeight=Math.min(409,Math.max(46,lines*15+12));
}
s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(2);s.showGridLines=false;
assert.deepEqual(s.getRange(`A6:H${end}`).values,values);
w.recalculate();
const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:800});
await fs.mkdir(path.join(HERE,'previews'),{recursive:true});
const longest=values.reduce((best,v,i)=>units(v[4])>units(values[best][4])?i:best,0)+6;
for(const [name,range] of [['opening','A1:F7'],['longest',`C${longest}:F${longest}`]]){
 const b=await w.render({sheetName:d.sheet,range,scale:1,format:'png'});
 await fs.writeFile(path.join(HERE,'previews',name+'.png'),new Uint8Array(await b.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(w)).save(output);
await fs.writeFile(path.join(HERE,'artifact-verification.json'),JSON.stringify({row_N:35,all_values_match:true,errors:errors.ndjson,native_material_hyperlinks_pending:true},null,2)+'\n');
console.log(JSON.stringify({output,row_N:35,native_material_hyperlinks_pending:true}));
