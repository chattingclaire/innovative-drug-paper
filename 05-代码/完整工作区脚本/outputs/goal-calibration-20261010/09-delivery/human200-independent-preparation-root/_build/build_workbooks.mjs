import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const OUT=path.dirname(HERE);
const data=JSON.parse(await fs.readFile(path.join(HERE,'workbook-input.json'),'utf8'));
const checks=[];
for(const side of ['A','B']){
  const records=data.sides[side];
  assert.equal(records.length,200);
  assert.equal(new Set(records.map(x=>x.blind_id)).size,200);
  const filename=path.join(OUT,`coder-${side}`,`独立编码表-${side}-200条.xlsx`);
  assert(!(await fs.access(filename).then(()=>true,()=>false)),'Do not overwrite an existing workbook');
  const wb=Workbook.create();
  const sheet=wb.worksheets.add('独立初判');
  sheet.getRange('A1:E1').values=[['盲号（点击读完整材料）','条款正文','维度','值（0/1）','理由（待定原因/补材）']];
  const matrix=[];
  for(const record of records){
    assert(record.body.length<=32767,'Do not truncate source body');
    for(const dim of data.dimensions)matrix.push([record.blind_id,record.body,dim,null,null]);
  }
  sheet.getRange('A2:E1001').values=matrix;
  sheet.getRange('A1:E1001').format.font={name:'Arial',size:11,color:'#222222'};
  sheet.getRange('A1:E1001').format.verticalAlignment='top';
  sheet.getRange('A1:E1').format={fill:'#334155',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:32,verticalAlignment:'center',horizontalAlignment:'center'};
  const widths={A:27,B:90,C:8,D:12,E:46};
  for(const [column,width] of Object.entries(widths))sheet.getRange(`${column}1:${column}1001`).format.columnWidth=width;
  sheet.getRange('B2:B1001').format.wrapText=true;
  sheet.getRange('E2:E1001').format.wrapText=true;
  sheet.getRange('A2:A1001').format.font={name:'Arial',size:11,color:'#0563C1'};
  sheet.getRange('C2:D1001').format.horizontalAlignment='center';
  sheet.getRange('D2:E1001').format.fill='#FFFBE6';
  sheet.getRange('D2:D1001').setNumberFormat('0');
  sheet.getRange('D2:D1001').dataValidation={rule:{type:'list',values:['0','1']}};
  const widthUnits=s=>[...s].reduce((n,c)=>n+(c.codePointAt(0)>255?2:1),0);
  for(let i=0;i<records.length;i++){
    const lines=records[i].body.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(widthUnits(line)/80)),0);
    sheet.getRange(`A${2+i*5}:E${6+i*5}`).format.rowHeight=Math.min(409,Math.max(42,lines*17+14));
  }
  sheet.freezePanes.freezeRows(1);sheet.freezePanes.freezeColumns(1);sheet.showGridLines=false;
  wb.recalculate();
  const actual=sheet.getRange('A2:E1001').values;
  assert.deepEqual(actual,matrix);
  const fields=await wb.inspect({kind:'table',range:"'独立初判'!C1:E6",include:'values,formulas',tableMaxRows:6,tableMaxCols:3,maxChars:1500});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000});
  await fs.mkdir(path.join(HERE,'previews'),{recursive:true});
  for(const [name,range] of [['top','A1:E6'],['longest',(()=>{let j=0;for(let i=1;i<records.length;i++)if(records[i].body.length>records[j].body.length)j=i;return `A${2+j*5}:E${2+j*5}`;})()]]){
    const blob=await wb.render({sheetName:'独立初判',range,scale:1,format:'png'});
    await fs.writeFile(path.join(HERE,'previews',`${side}-${name}.png`),new Uint8Array(await blob.arrayBuffer()));
  }
  const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(filename);
  checks.push({side,record_N:200,row_N:1000,original_body_values_preserved:true,D_E_all_blank:true,source_body_max_chars:Math.max(...records.map(x=>x.body.length)),fields:fields.ndjson,errors:errors.ndjson,native_material_hyperlinks_pending:true});
}
await fs.writeFile(path.join(HERE,'artifact-checks.json'),JSON.stringify(checks,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:'two_artifact_workbooks_exported',records_per_coder:200,data_rows_per_workbook:1000,D_E_all_blank:true,hyperlink_finalization_and_saved_readback_pending:true}));
