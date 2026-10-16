import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const here=path.dirname(fileURLToPath(import.meta.url));
const outputDir=path.resolve(here,'../01a0dbb7-43f0-7a61-a367-7f0c814ee9d4/两方法重跑-20260927');
const data=JSON.parse(await fs.readFile(path.join(here,'rerun_delivery_payload.json'),'utf8'));
await fs.mkdir(outputDir,{recursive:true});
const previews=path.join(here,'delivery_previews');await fs.mkdir(previews,{recursive:true});
const audit=[];
let tableSerial=0;
const font='Arial';
const literal=v=>typeof v==='string'&&v.startsWith('=')?"'"+v:v;
function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function standard(sheet,range){
  sheet.showGridLines=false;
  sheet.getRange(range).format.font={name:font,size:10,color:'#253246'};
  sheet.getRange(range).format.verticalAlignment='center';
}
function header(sheet,address){
  sheet.getRange(address).format={fill:'#283F5B',font:{name:font,size:10,color:'#FFFFFF',bold:true},
    horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:30};
  sheet.getRange(address).format.borders={insideVertical:{style:'thin',color:'#FFFFFF'}};
}
function flat(wb,name,headers,rows,widths,{freeze=1}={}){
  const sh=wb.worksheets.add(name),last=col(headers.length-1),end=rows.length+1;
  standard(sh,`A1:${last}${end}`);
  sh.getRange(`A1:${last}1`).values=[headers];
  for(let start=0;start<rows.length;start+=400){
    const values=rows.slice(start,start+400).map(r=>r.map(literal));
    sh.getRangeByIndexes(start+1,0,values.length,headers.length).values=values;
  }
  header(sh,`A1:${last}1`);
  for(let i=0;i<headers.length;i++){
    sh.getRange(`${col(i)}1:${col(i)}${end}`).format.columnWidth=widths[i]??28;
  }
  sh.getRange(`A2:${last}${end}`).format.wrapText=true;
  sh.getRange(`A2:${last}${end}`).format.verticalAlignment='top';
  // Fit text conservatively to Excel's finite row-height limit. Full text is
  // retained; no row is shortened to an excerpt for fitting.
  for(let i=0;i<rows.length;i++){
    const lineCounts=rows[i].map((value,j)=>{
      if(typeof value!=='string')return 1;
      const w=widths[j]??28;
      return value.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil([...line].reduce((s,c)=>s+(c.charCodeAt(0)>255?1.75:1),0)/Math.max(8,w-2))),0);
    });
    const height=Math.max(30,Math.max(...lineCounts)*14+8);
    if(height>409)throw new Error(`Unfitted long text: ${name} row ${i+2} requires ${height}`);
    sh.getRange(`A${i+2}:${last}${i+2}`).format.rowHeight=height;
  }
  sh.freezePanes.freezeRows(1);if(freeze)sh.freezePanes.freezeColumns(freeze);
  const table=sh.tables.add(`A1:${last}${end}`,true,'ResearchData_'+(++tableSerial));
  table.showFilterButton=true;
  return sh;
}
async function verifyAndExport(wb,filename,views){
  wb.recalculate();
  for(const view of views){
    const report=await wb.inspect({kind:'table',sheetId:view.sheet,range:view.range,include:'values,formulas',
      tableMaxRows:8,tableMaxCols:10,tableMaxCellChars:100,maxChars:2200});
    audit.push({file:filename,sheet:view.sheet,inspection:report.ndjson});
    const png=await wb.render({sheetName:view.sheet,range:view.range,scale:1,format:'png'});
    const target=path.join(previews,filename.replace('.xlsx','')+'-'+view.sheet+'.png');
    await fs.writeFile(target,new Uint8Array(await png.arrayBuffer()));
  }
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',
    options:{useRegex:true,maxResults:100},summary:'final formula error scan',maxChars:3000});
  audit.push({file:filename,formulaErrors:errors.ndjson});
  const out=await SpreadsheetFile.exportXlsx(wb);await out.save(path.join(outputDir,filename));
}

for(const book of data.reference_books){
  const wb=Workbook.create();
  const widths=[24,20,138,8,8,8,8,8,64,64,64,64,64,120,30,38,35,70,75,70,15];
  flat(wb,'编码记录',book.header,book.rows,widths,{freeze:1});
  const manual=flat(wb,'共用规范',book.manual_header,[[0,book.notice],...book.manual_rows],[9,155],{freeze:0});
  manual.tabColor='#748397';
  const views=[{sheet:'编码记录',range:'A1:H5'},{sheet:'共用规范',range:'A1:B8'}];
  if(book.long_text_rows.length){flat(wb,'长文本逐行',book.long_text_header,book.long_text_rows,[24,20,12,25,10,155,12]);views.push({sheet:'长文本逐行',range:'A1:G5'});}
  await verifyAndExport(wb,book.filename,views);
}

const comp=data.comparison_book,wb=Workbook.create();
const views=[];
for(const s of comp.summaries){
  const sh=wb.worksheets.add(s.name);standard(sh,'A1:O40');sh.tabColor='#283F5B';
  sh.getRange('A2').values=[[s.name]];sh.getRange('A2').format.font={name:font,size:14,bold:true};
  sh.getRange('A2:O2').format.borders={bottom:{style:'thin',color:'#708295'}};
  sh.getRange('A3').values=[[s.note]];sh.getRange('A3').format.font={name:font,size:10,italic:true,color:'#5A6470'};
  sh.getRange('A5:O5').values=[s.header];header(sh,'A5:J5');header(sh,'L5:O5');
  sh.getRange('A6:O35').values=s.rows;
  const formulas=s.rows.map((_,i)=>{const r=i+6;return[
    `=IF(L${r}+M${r}=0,"n.a.",L${r}/(L${r}+M${r}))`,
    `=IF(L${r}+N${r}=0,"n.a.",L${r}/(L${r}+N${r}))`,
    `=IF(2*L${r}+M${r}+N${r}=0,"n.a.",2*L${r}/(2*L${r}+M${r}+N${r}))`];});
  sh.getRange('D6:F35').formulas=formulas;
  sh.getRange('D6:G35').setNumberFormat('0.0%');sh.getRange('H6:J35').setNumberFormat('#,##0');
  sh.getRange('L6:O35').setNumberFormat(s.scope==='current1268'?'0.00':'0');
  const widths=[9,25,8,13,13,13,17,17,16,16,3,15,15,15,15];
  widths.forEach((w,i)=>sh.getRange(`${col(i)}1:${col(i)}40`).format.columnWidth=w);
  sh.getRange('A6:O35').format.rowHeight=25;
  sh.getRange('A37').values=[['统计来源：'+s.scope+'/metrics.json；SHA256 '+s.source_sha256]];
  sh.getRange('A38').values=[['统计快照；若更改编码，请重新运行统计。旧自动版本只作同一参考下的版本比较。']];
  views.push({sheet:s.name,range:'A1:J17'});
  // Independent expected values: compare formula cells after recalculation to
  // the frozen confusion counts; no prefilled rate is used as the formula.
  wb.recalculate();
  const got=sh.getRange('D6:F35').values;
  s.rows.forEach((r,i)=>{
    const [tp,fp,fn]=r.slice(11,14);const want=[tp+fp?tp/(tp+fp):'n.a.',tp+fn?tp/(tp+fn):'n.a.',2*tp+fp+fn?2*tp/(2*tp+fp+fn):'n.a.'];
    want.forEach((v,j)=>{if(typeof v==='number'?typeof got[i][j]!=='number'||!Number.isFinite(got[i][j])||Math.abs(got[i][j]-v)>1e-10:got[i][j]!==v)throw new Error('Formula mismatch '+s.name+' '+i+' '+j);});
  });
}
flat(wb,'逐条对照',comp.detail_header,comp.detail_rows,[24,20,20,138,...Array(20).fill(11)],{freeze:1});
views.push({sheet:'逐条对照',range:'A1:I5'});
flat(wb,'LLM全量',comp.llm_header,comp.llm_rows,[24,138,...Array(5).fill(8),...Array(5).fill(64),30,38,35,70,70,15,70],{freeze:1});
views.push({sheet:'LLM全量',range:'A1:G5'});
flat(wb,'LLM证据',comp.evidence_header,comp.evidence_rows,[24,8,12,155,70],{freeze:1});
views.push({sheet:'LLM证据',range:'A1:D6'});
flat(wb,'方法说明',['序号','说明'],comp.method_notes.map((v,i)=>[i+1,v]),[9,155],{freeze:0});
views.push({sheet:'方法说明',range:'A1:B9'});
if(comp.long_text_rows.length){flat(wb,'长文本逐行',comp.long_text_header,comp.long_text_rows,[24,20,12,25,10,155,12]);views.push({sheet:'长文本逐行',range:'A1:G5'});}
await verifyAndExport(wb,comp.filename,views);
await fs.writeFile(path.join(here,'workbook_verification.json'),JSON.stringify(audit,null,2)+'\n');
console.log(JSON.stringify({outputDir,workbooks:3,previews}));
