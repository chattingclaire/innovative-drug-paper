import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const admin = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.dirname(admin);
const payload = JSON.parse(await fs.readFile(path.join(admin, '无答案校准内容.json'), 'utf8'));
if (payload.units.length !== 40 || !payload.context_review_complete) throw Error('40条来源及语境需复核完成');
const font = 'Heiti SC';
const col = n => { let x=''; for(;n;n=Math.floor((n-1)/26))x=String.fromCharCode(65+(n-1)%26)+x; return x; };
const chunks = text => {
  const chars = Array.from(text);
  const result = [];
  for(let i=0;i<chars.length;i+=240)result.push(chars.slice(i,i+240).join(''));
  return result.length ? result : [''];
};
function createSheet(wb, name, headers, rows, widths, title, note) {
  const s=wb.worksheets.add(name); s.showGridLines=false;
  const end=rows.length+5, last=col(headers.length);
  const all=s.getRange(`A1:${last}${end}`);
  all.format.font={name:font,size:11,color:'#18202A'};
  all.format.verticalAlignment='top';
  s.getRange('A2').values=[[title]];
  s.getRange('A2').format.font={name:font,size:15,bold:true,color:'#18202A'};
  s.getRange('A2').format.rowHeight=29;
  s.getRange('A3').values=[[note]];
  s.getRange('A3').format.font={name:font,size:11,color:'#59636E'};
  s.getRange('A3').format.rowHeight=22;
  s.getRange(`A5:${last}5`).values=[headers];
  if(rows.length)s.getRange(`A6:${last}${end}`).values=rows;
  for(let i=0;i<widths.length;i++)s.getRange(`${col(i+1)}1:${col(i+1)}${end}`).format.columnWidth=widths[i];
  s.getRange(`A5:${last}5`).format={fill:'#243B53',font:{name:font,size:11,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
  s.getRange(`A5:${last}5`).format.rowHeight=36;
  s.getRange(`A6:${last}${end}`).format.wrapText=true;
  rows.forEach((row,i)=>{
    const lineCount=Math.max(...row.map((value,j)=>String(value??'').split('\n').reduce((sum,p)=>sum+Math.max(1,Math.ceil(Array.from(p).length/Math.max(5,widths[j]*0.46))),0)));
    s.getRange(`A${i+6}:${last}${i+6}`).format.rowHeight=Math.min(390,Math.max(42,lineCount*17+12));
  });
  s.freezePanes.freezeRows(5);
  s.freezePanes.freezeColumns(1);
  return s;
}
const log={purpose:payload.purpose,manual_sha256:payload.manual_sha256,workbooks:{},new_labels_generated:false,new_kappa_generated:false};
await fs.mkdir(path.join(admin,'previews'),{recursive:true});
for (const coder of ['A','B']) {
  const wb=Workbook.create();
  const units=payload.units;
  const judgementRows=units.map(u=>[u.material_id,u.current_text.length>500||u.current_text.split('\n').length>12?'完整当前句段见“阅读材料”同编号。':u.current_text,...Array(11).fill(null)]);
  const jud=createSheet(wb,'填写',['材料编号','当前句段','安全性','有效性','经济性','创新性','公平性','安全性理由及引文','有效性理由及引文','经济性理由及引文','创新性理由及引文','公平性理由及引文','材料问题或规则争议'],judgementRows,[16,80,12,12,12,12,12,35,35,35,35,35,40],`编码员${coder}校准试填`,'按“阅读材料”完整原文和语境逐维填写。黄色栏填写0/1及依据。');
  jud.tabColor='#243B53';
  jud.getRange('C6:M45').format.fill='#FFF8E3';
  jud.getRange('C6:G45').setNumberFormat('0');
  jud.getRange('C6:G45').format.horizontalAlignment='center';
  jud.getRange('C6:G45').dataValidation={rule:{type:'whole',operator:'between',formula1:0,formula2:1}};
  const table=jud.tables.add('A5:M45',true,'CalibrationInputs');table.showFilterButton=true;
  const materialRows=[];
  for(const u of units){
    const src=`${u.source_name}\n${u.pages?.length?'第'+u.pages.join('、')+'页；':''}${u.source_locator}`;
    const target=chunks(u.current_text);
    target.forEach((text,i)=>materialRows.push([u.material_id,`${u.current_kind||'当前句段'} ${i+1}/${target.length}`,text,src]));
    u.contexts.forEach((text,contextIndex)=>{
      if(text===u.current_text)return;
      const d=u.context_descriptors[contextIndex];
      const contextSource=`${d.source_name}\n${d.pages?.length?'第'+d.pages.join('、')+'页；':''}${d.source_locator}`;
      const pieces=chunks(text);
      pieces.forEach((part,i)=>materialRows.push([u.material_id,`${d.kind}${contextIndex+1} ${i+1}/${pieces.length}`,part,contextSource]));
    });
    if(u.conditional_reference_note){
      const note=typeof u.conditional_reference_note==='string'?u.conditional_reference_note:u.conditional_reference_note.description;
      chunks(note).forEach((text,i)=>materialRows.push([u.material_id,`援引范围提示 ${i+1}`,text,'来源复核说明；不是维度答案']));
    }
  }
  const reading=createSheet(wb,'阅读材料',['材料编号','内容位置','原文或表格结构','来源位置'],materialRows,[16,30,125,62],'政策原文与必要语境','同编号当前句段须连续阅读；表格分隔符用于排列原单元格，表名结构记录另注。');
  reading.tabColor='#A7B7C8';
  for(let i=0;i<materialRows.length;i++)if(materialRows[i][1].startsWith('当前'))reading.getRange(`A${i+6}:D${i+6}`).format.fill='#EEF3F7';
  const manualRows=[];
  payload.manual.split('\n').forEach((line,i)=>chunks(line).forEach((text,j)=>manualRows.push([i+1,j+1,text])));
  createSheet(wb,'编码手册',['原行号','续片','共同手册全文'],manualRows,[12,10,140],'五维共同编码手册','供本轮校准讨论。两份表附相同全文，讨论后冻结检验标准。');
  const instructions=[
    ['本轮材料','40条有目的开发校准材料','先独立试填，封存各自结果后再讨论。'],
    ['编码对象','当前完整句段，每维单独判0或1','同一单元可涉及多维，每维最多记1次。'],
    ['标签含义','1：实质涉及该维；0：完整材料不满足该维判据','否定、条件、限制及证据不足须按完整命题判读。'],
    ['填写依据','每维理由注明原文引文及实际使用的语境','需要语境时说明当前句如何承接，勿复制整栏标签。'],
    ['材料或规则问题','填写具体位置与影响维度','问题未解决的维度留空，补材后作出0/1判定。'],
    ['填写次序','填写完成并保存后，再进行共同讨论','讨论改变规则时记录通用决定及原文依据。'],
    ['共同手册','“编码手册”提供全文','核对实际使用全文后填写手册确认栏。'],
    ['使用范围','开发材料用于完善手册','冻结后的独立检验另行设计。'],
    ['实际填写人姓名或编号',null,'由填写人记录'],
    ['专业背景与编码经验',null,'由填写人记录'],
    ['实际开始日期',null,'由填写人记录'],
    ['实际提交日期',null,'由填写人记录'],
    ['确认使用本表所附手册',null,'确认后填写“是”，或说明实际使用文件'],
    ['本轮填写前见过的答案或讲解',null,'记录接触情况和范围'],
    ['本轮独立填写情况',null,'记录是否及何时与他人讨论'],
  ];
  const guide=createSheet(wb,'填写说明',['项目','内容或实际填写','说明'],instructions,[34,90,75],`编码员${coder}填写说明`,'实际人员信息与日期由填写人记录。标签和理由均为空白。');
  guide.getRange('B14:B20').format.fill='#FFF8E3';guide.freezePanes.unfreeze();
  wb.recalculate();
  const inspect=await wb.inspect({kind:'table',range:'填写!A5:G8',include:'values,formulas',tableMaxRows:4,tableMaxCols:7,maxChars:1800});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},maxChars:1000});
  await fs.writeFile(path.join(admin,`inspect_${coder}.ndjson`),inspect.ndjson+'\n'+errors.ndjson);
  if(jud.getRange('C6:M45').values.flat().some(v=>v!==null&&v!==''&&v!==undefined))throw Error('填写答案未保持空白');
  const views={'填写':'A2:G8','阅读材料':'A2:D8','编码手册':'A2:C10','填写说明':'A2:C9'};
  for(const [sheetName,range] of Object.entries(views)){
    const preview=await wb.render({sheetName,range,scale:1,format:'png'});
    await fs.writeFile(path.join(admin,'previews',`${coder}_${sheetName}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  const file=path.join(outputDir,`校准试填-${coder}.xlsx`);
  await (await SpreadsheetFile.exportXlsx(wb)).save(file);
  log.workbooks[coder]={path:file,units:40,blank_label_cells:200,blank_reason_cells:200,reading_rows:materialRows.length,manual_rows:manualRows.length,rendered_sheets:Object.keys(views),data_validation:'填写!C6:G45整数0至1'};
  console.log(JSON.stringify({coder,path:file,units:40,reading_rows:materialRows.length}));
}
await fs.writeFile(path.join(admin,'表格制作核查记录.json'),JSON.stringify(log,null,2)+'\n');
