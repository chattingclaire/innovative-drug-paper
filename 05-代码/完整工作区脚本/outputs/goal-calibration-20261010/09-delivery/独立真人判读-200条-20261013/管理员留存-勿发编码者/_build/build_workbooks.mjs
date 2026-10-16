import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const here=path.dirname(fileURLToPath(import.meta.url));
const admin=path.dirname(here), out=path.dirname(admin);
const mapping=JSON.parse(await fs.readFile(path.join(admin,'blind-assignment.json'),'utf8'));
const frozen=JSON.parse(await fs.readFile(path.join(admin,'sampling-freeze.json'),'utf8'));
const manual=await fs.readFile(frozen.manual.path);
const checks=[];
const guide=`真人独立判读填写说明

本套有200条材料。每条分别判断安全性S、有效性E、经济性Ec、创新性I、公平性F，共1000个判断。

1. 先解压整个压缩包，保持文件夹结构。阅读“共同编码手册.txt”。双击“开始阅读.html”进入材料目录，也可以点击Excel的B列打开对应原文。
2. 表内每条占五行，依次为S、E、Ec、I、F。只填写黄色的D、E两列，不修改盲号、材料路径、维度、行序和表头。
3. D列：符合手册判据填1；材料充分但不符合填0。不能仅凭关键词、文件题名或部门推定。五个维度分别判断。
4. E列：每个0或1都写简短理由，包含当前原文连续引文或位置；使用语境时写语境编号及引文。判0也说明最接近的内容为何未满足。I的研发支持关系、F的公平关系按手册要求说明。
5. 若确有关键原文缺失、指代无法解析或真实规则冲突，D留空，E以“待定：”开头，写清缺什么。完全空白表示尚未填写，不代表0。其他能判断的维度照常填写。
6. 请本人独立完成，首次提交前不查看另一位编码者或机器的答案，不用AI代填，也不先商量后改成一致。材料问题记录后交管理员统一处理。
7. 完成后保存Excel，并填写“提交说明.txt”，将这两个原始文件交回管理员。首次提交后需要修改的，另存新版本，保留原始文件。

随包手册是本次共同执行的冻结版本，内容原样保留。手册末尾“候选”等用语是底稿的历史版本说明；本次材料现已正式发放，可开始判读。

材料页上方是当前待判条款；下方为完整语境、来源资料及附件。请按手册的语境使用规则判读，不能把其他条款的议题全部归到当前条款。
`;
for(const side of ['A','B']){
  const folder=path.join(out,'发给编码者'+side);
  await fs.mkdir(folder,{recursive:true});
  await fs.writeFile(path.join(folder,'共同编码手册.txt'),manual);
  await fs.writeFile(path.join(folder,'填写说明.txt'),`编码者${side}材料\n\n`+guide);
  await fs.writeFile(path.join(folder,'提交说明.txt'),`编码者${side}首次提交说明（请本人填写）\n\n姓名或可核实的个人代号：\n开始判读日期时间：\n完成判读日期时间：\n是否本人独立完成，未使用AI代填：\n首次提交前是否看过另一位编码者或机器的答案：\n首次提交前是否与他人讨论过具体答案，或据此修改过结果：\n材料缺失、补材或其他需要说明的情况（没有请写“无”）：\n\n请如实填写，不符合独立条件也保留真实记录。\n`);
  const target=path.join(folder,`独立判读-${side}-200条.xlsx`);
  try{await fs.access(target);throw Error('Refuse overwriting issued workbook');}catch(e){if(e.code!=='ENOENT')throw e;}
  const wb=Workbook.create(), s=wb.worksheets.add('独立初判');
  s.showGridLines=false;
  s.getRange('A1:E1').values=[['材料盲号','原文材料（点击打开）','维度','判定（填0或1）','理由与原文依据（待定请说明缺失内容）']];
  const rows=mapping.methods[side].flatMap(r=>['S','E','Ec','I','F'].map(d=>[r.original_blind_id,r.material_locator,d,null,null]));
  s.getRange('A2:E1001').values=rows;
  s.getRange('A1:E1001').format.font={name:'Arial',size:11,color:'#203044'};
  s.getRange('A1:E1001').format.verticalAlignment='center';
  s.getRange('A1:E1001').format.rowHeight=30;
  s.getRange('A1:E1').format={fill:'#314B63',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:40,wrapText:true,horizontalAlignment:'center'};
  s.getRange('A1:A1001').format.columnWidth=15;
  s.getRange('B1:B1001').format.columnWidth=32;
  s.getRange('C1:C1001').format.columnWidth=8;
  s.getRange('D1:D1001').format.columnWidth=19;
  s.getRange('E1:E1001').format.columnWidth=80;
  s.getRange('A2:C1001').format.fill='#F1F4F7';
  s.getRange('B2:B1001').format.font={name:'Arial',size:11,color:'#1764AA',underline:'single'};
  s.getRange('C2:D1001').format.horizontalAlignment='center';
  s.getRange('D2:E1001').format.fill='#FFF4D6';
  s.getRange('E2:E1001').format.wrapText=true;
  s.getRange('D2:D1001').setNumberFormat('0');
  s.getRange('D2:D1001').dataValidation={rule:{type:'list',values:['0','1']}};
  for(let row=2;row<=1001;row+=5)s.getRange(`A${row}:E${row}`).format.borders={top:{style:'thin',color:'#AEBECD'}};
  s.freezePanes.freezeRows(1);
  wb.recalculate();
  const inspection=await wb.inspect({kind:'region',sheetId:s.name,range:'A1:E6',maxChars:3000,tableMaxRows:6,tableMaxCols:5});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1000});
  const preview=await wb.render({sheetName:s.name,range:'A1:E11',scale:1.5,format:'png'});
  await fs.writeFile(path.join(here,`${side}-preview.png`),new Uint8Array(await preview.arrayBuffer()));
  const xlsx=await SpreadsheetFile.exportXlsx(wb); await xlsx.save(target);
  checks.push({side,inspection:inspection.ndjson,error_scan:errors.ndjson,rows:rows.length,expected_blank_input_cells:2000});
}
await fs.writeFile(path.join(here,'artifact-checks.json'),JSON.stringify(checks,null,2));
await fs.writeFile(path.join(out,'发放说明.txt'),`真人独立判读材料（2026年10月13日）\n\n把“编码者A材料.zip”发给第一位真人，把“编码者B材料.zip”发给另一位真人。每人200条，五维分别判断。两人独立完成，第一次提交前不相互讨论答案。\n\n每个压缩包都有空白Excel、共同编码手册、填写说明、200条原文页面和必要附件。解压后打开“开始阅读.html”或Excel即可。\n\n请收回两份填写后的原始Excel和各自的“提交说明.txt”，保留首次提交原件。存在分歧或待定的条目，收齐后再统一处理。\n\n“管理员留存-勿发编码者”包含抽样与盲号对应记录，不发给编码者。旧200条复核文件原样保留。\n\n本轮从已登记未参与开发的1151条剩余材料中抽取200条，不能把本轮结果直接称作4481条全量的独立验证。此次只发放人工材料，不重跑全量机器编码。\n`);
console.log(JSON.stringify({workbooks:2,units_each:200,rows_each:1000,answers_prefilled:0}));
