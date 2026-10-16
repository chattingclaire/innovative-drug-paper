import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const base=process.cwd();
const out=path.join(base,'outputs/本轮查看-既有AC结果与AB待填/01-既有AC结果');
const audit=path.join(base,'outputs/coding-revision-20261008-r4/ac-original-text-workbooks');
const r3=path.join(base,'outputs/coding-revision-20261007-r3');
const readLines=async p=>(await fs.readFile(p,'utf8')).trim().split('\n').map(x=>JSON.parse(x));
const inputPath=path.join(r3,'effective_blind_inputs_v14.jsonl');
const inputs=new Map((await readLines(inputPath)).map(x=>[x.id,x]));
const exclusion=JSON.parse(await fs.readFile(path.join(base,'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'),'utf8'));
const reserved=new Set(exclusion.all_registered_members_of_reserved_families_unit_ids);
const sha=async p=>crypto.createHash('sha256').update(await fs.readFile(p)).digest('hex');
const dims=['S','E','Ec','I','F'];
const reports=[];
for(const coder of ['A','C']){
  const refPath=path.join(r3,`reference/agent_${coder}_final_v14.jsonl`);
  const refs=await readLines(refPath);
  if(refs.length!==240 || new Set(refs.map(x=>x.id)).size!==240)throw Error('240 unique ID requirement');
  const rows=refs.map(ref=>{
    if(reserved.has(ref.id))throw Error('Reserved validation family unexpectedly in old results');
    const x=inputs.get(ref.id);if(!x)throw Error('Missing original text '+ref.id);
    for(const d of dims)if(![0,1].includes(ref.labels[d]))throw Error('Non-binary label');
    const t=[x.id,x.text,...dims.map(d=>ref.labels[d]),...dims.map(d=>ref.dimension_reasons[d]??''),x.source_title,JSON.stringify(x.pages),JSON.stringify(ref.evidence),JSON.stringify(ref.issues)];
    for(const v of t)if(typeof v==='string' && v.length>32767)throw Error('Excel cell limit');
    return t;
  });
  const wb=Workbook.create();const sh=wb.worksheets.add('原文与编码结果');sh.showGridLines=false;sh.tabColor='#315A7D';
  const heads=['单元ID','政策原文','安全性S','有效性E','经济性Ec','创新性I','公平性F','安全性判定理由','有效性判定理由','经济性判定理由','创新性判定理由','公平性判定理由','政策来源','来源页码','原始逐字证据','原始问题记录'];
  sh.getRange('A1:P241').values=[heads,...rows];
  sh.getRange('A1:P241').format.font={name:'Arial',size:11,color:'#20262C'};
  sh.getRange('A1:P241').format.verticalAlignment='top';
  sh.getRange('A1:P241').format.wrapText=true;
  sh.getRange('A1:P1').format={fill:'#315A7D',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:32,horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
  sh.getRange('A1:A241').format.columnWidth=22;
  sh.getRange('B1:B241').format.columnWidth=108;
  sh.getRange('C1:G241').format.columnWidth=12;
  sh.getRange('C2:G241').format.horizontalAlignment='center';
  sh.getRange('C2:G241').setNumberFormat('0');
  sh.getRange('H1:L241').format.columnWidth=62;
  sh.getRange('M1:M241').format.columnWidth=58;
  sh.getRange('N1:N241').format.columnWidth=16;
  sh.getRange('O1:P241').format.columnWidth=65;
  for(let i=0;i<rows.length;i++){
    const widthChars=[20,52,12,12,12,12,12,29,29,29,29,29,27,14,30,30];
    const lines=Math.max(...rows[i].map((v,j)=>String(v).split('\n').reduce((a,s)=>a+Math.max(1,Math.ceil(s.length/widthChars[j])),0)));
    sh.getRange(`A${i+2}:P${i+2}`).format.rowHeight=Math.min(409,Math.max(62,lines*16+12));
    if(i%2===1)sh.getRange(`A${i+2}:P${i+2}`).format.fill='#F2F5F8';
  }
  sh.freezePanes.freezeRows(1);sh.freezePanes.freezeColumns(2);
  const table=sh.tables.add('A1:P241',true,`Coder${coder}Results`);table.showFilterButton=true;
  const cx=wb.worksheets.add('完整语境');cx.showGridLines=false;
  const cr=refs.map(ref=>{const x=inputs.get(ref.id);return [x.id,JSON.stringify(x.contexts,null,2),x.context_usage??''];});
  cx.getRange('A1:C241').values=[['单元ID','完整必要语境JSON','语境使用规则'],...cr];
  cx.getRange('A1:C241').format.font={name:'Arial',size:11};
  cx.getRange('A1:C241').format.verticalAlignment='top';
  cx.getRange('A1:A241').format.columnWidth=22;cx.getRange('B1:B241').format.columnWidth=130;cx.getRange('C1:C241').format.columnWidth=60;
  cx.getRange('A1:C1').format={fill:'#315A7D',font:{bold:true,color:'#FFFFFF'},rowHeight:30};
  cx.getRange('A2:C241').format.rowHeight=70;cx.getRange('A2:C241').format.wrapText=false;
  cx.freezePanes.freezeRows(1);cx.freezePanes.freezeColumns(1);
  const notes=wb.worksheets.add('结果说明');notes.showGridLines=false;
  const noteRows=[['事项','内容'],['结果范围',`编码员${coder}的既有v14最终结果，240个单元；同一单元可按五维分别赋0或1。`],['阅读方式','原文与编码结果表包含完整政策原句、五维原标签、原判定理由、来源与证据；完整语境表按单元ID对应，长语境可进入单元格编辑或公式栏查看全文。'],['标签来源','原标签由此前的agent编码及复读形成。本次仅补原文与展示，不重新编码，不改变标签或判定理由。'],['真人复核记录','用户于2026-10-08确认：对之前A/C两份结果已做真人检验，标签未改。未提供独立盲评首次提交或具体复核流程，故保留事后复核性质。'],['命名对应','历史编码员C在论文展示名中对应编码员B；本表保留C以便与原始结果追溯。'],['页码缺失','来源页码[]表示冻结来源未提供页码，不补造页码。'],['结果文件SHA256',await sha(refPath)],['材料文件SHA256',await sha(inputPath)]];
  notes.getRange(`A1:B${noteRows.length}`).values=noteRows;
  notes.getRange(`A1:B${noteRows.length}`).format.font={name:'Arial',size:11};
  notes.getRange(`A1:B${noteRows.length}`).format.wrapText=true;notes.getRange(`A1:B${noteRows.length}`).format.verticalAlignment='top';
  notes.getRange(`A1:A${noteRows.length}`).format.columnWidth=24;notes.getRange(`B1:B${noteRows.length}`).format.columnWidth=110;
  notes.getRange(`A2:B${noteRows.length}`).format.rowHeight=60;notes.getRange('A1:B1').format={fill:'#315A7D',font:{bold:true,color:'#FFFFFF'},rowHeight:30};
  wb.recalculate();
  const inspect=await wb.inspect({kind:'table',range:'原文与编码结果!A1:G4',include:'values,formulas',tableMaxRows:4,tableMaxCols:7,maxChars:3500});
  await fs.writeFile(path.join(audit,`inspect-${coder}.json`),JSON.stringify(inspect));
  const errs=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:2000});
  await fs.writeFile(path.join(audit,`formula-scan-${coder}.json`),JSON.stringify(errs));
  const file=path.join(out,`编码员${coder}-240条结果含原文.xlsx`);
  const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(file);
  for(const [name,range] of [['main','A1:G6'],['reasons','H1:P4'],['notes','A1:B9']]){
    const preview=await wb.render({sheetName:name==='notes'?'结果说明':'原文与编码结果',range,scale:1,format:'png'});
    await fs.writeFile(path.join(audit,`${coder}-${name}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  const report={coder,file,rows:240,original_text_joined_by_unique_id:true,labels_unchanged:true,reasons_unchanged:true,reserved_family_overlap:0,ref_sha256:await sha(refPath),input_sha256:await sha(inputPath),xlsx_sha256:await sha(file)};
  reports.push(report);console.log(JSON.stringify(report));
}
await fs.writeFile(path.join(audit,'build-bindings.json'),JSON.stringify(reports,null,2));
