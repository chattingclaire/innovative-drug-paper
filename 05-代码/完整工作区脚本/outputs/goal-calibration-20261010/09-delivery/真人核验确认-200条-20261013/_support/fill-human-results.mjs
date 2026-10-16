import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const support = path.dirname(fileURLToPath(import.meta.url));
const out = path.dirname(support);
const delivery = path.dirname(out);
const aiRoot = path.join(delivery,'AI独立复核-200条-20261013');
if(process.argv.includes('--split')){
  const python='/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
  const finalData=JSON.parse(await fs.readFile(path.join(out,'真人核验结果.json'),'utf8'));
  const aToB=new Map(finalData.records.map(r=>[r.A_id,r.B_id]));
  const sourceA=path.join(out,'真人核验确认-200条.xlsx');
  const sourceB=path.join(aiRoot,'AI复核者B/AI复核-B-200条.xlsx');
  const reference=await SpreadsheetFile.importXlsx(await FileBlob.load(sourceA));
  const noteValues=reference.worksheets.getItem('核验确认记录').getRange('A1:G29').values;
  const originalHashes=Object.fromEntries(await Promise.all([sourceA,sourceB,path.join(out,'真人核验结果.json')].map(async p=>[p,createHash('sha256').update(await fs.readFile(p)).digest('hex')])));
  const jobs=[];
  for(const coder of ['A','B']){
    const source=coder==='A'?sourceA:sourceB;
    const book=coder==='A'?reference:await SpreadsheetFile.importXlsx(await FileBlob.load(source));
    const sheetName=coder==='A'?'真人核验结果':'独立初判';
    const sheet=book.worksheets.getItem(sheetName);
    const before=sheet.getRange('A1:E1001').values;
    const map=new Map(finalData.records.map(r=>[r[`${coder}_id`],r]));
    const entries=before.slice(1).map(([id,,dim])=>{
      const j=map.get(id)?.judgments[dim];
      if(!j||![0,1].includes(j.value))throw new Error(`Unknown ${coder} record ${id}/${dim}`);
      const reason=coder==='A'?j.reason:j.reason.replace(/A-\d{3}/g,id=>aToB.get(id)??id);
      return [j.value,reason];
    });
    const readLayout="import sys,json,openpyxl\nw=openpyxl.load_workbook(sys.argv[1],data_only=False)[sys.argv[2]]\nprint(json.dumps({'widths':{c:w.column_dimensions[c].width for c in 'ABCDE'},'rows':{r:{'height':w.row_dimensions[r].height or w.sheet_format.defaultRowHeight or 15,'eFontPoints':w.cell(r,5).font.sz or 11} for r in range(1,1002)}}))";
    const layout=JSON.parse(execFileSync(python,['-c',readLayout,source,sheetName],{encoding:'utf8'}));
    jobs.push({coder,source,book,sheet,sheetName,before,entries,layout,map});
  }
  const markerReceipt=path.join(support,'split-operation-started.json');
  try{await fs.access(markerReceipt);}catch{
    const marker='/Users/rainbow/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1009.11318/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs';
    const result=execFileSync(process.execPath,[marker,'--operation-kind','edit','--expected-output-count','2','--output-format','xlsx'],{cwd:support,encoding:'utf8'});
    await fs.writeFile(markerReceipt,JSON.stringify({result},null,2));
  }
  const reports=[];
  for(const job of jobs){
    const {coder,book,sheet,sheetName,before,entries,layout}=job;
    sheet.getRange('D1:E1').values=[['真人核验判定（0/1）','核验理由与原文依据']];
    sheet.getRange('D2:E1001').values=entries;
    let longest={row:2,height:0};
    for(let i=0;i<entries.length;i++){
      const meta=layout.rows[i+2];
      const width=layout.widths.E;
      const font=meta.eFontPoints;
      const capacity=Math.max(8,Math.floor((width*7-18)/(font*96/72*0.56)*0.9));
      const lines=entries[i][1].split('\n').reduce((n,s)=>n+Math.max(1,Math.ceil([...s].reduce((v,c)=>v+(c.codePointAt(0)>255?2:1),0)/capacity)),0);
      const height=Math.max(meta.height,Math.ceil(lines*(font*1.45+1)+8));
      if(height>409)throw new Error(`${coder} row ${i+2} exceeds safe height`);
      if(height!==meta.height)sheet.getRange(`A${i+2}:E${i+2}`).format.rowHeight=height;
      if(height>longest.height)longest={row:i+2,height};
    }
    let note;
    if(coder==='A')note=book.worksheets.getItem('核验确认记录');
    else{
      note=book.worksheets.add('核验确认记录');
      note.showGridLines=false;
      note.getRange('A1:G29').values=noteValues;
      note.getRange('A1:G29').format.font={name:'Arial',size:10};
      note.getRange('A1').format.font={bold:true,size:14};
      note.getRange('A1:G1').format.rowHeight=28;
      note.getRange('A2:G9').format.rowHeight=23;
      note.getRange('A11:G11').format={fill:'#304B61',font:{bold:true,color:'#FFFFFF'},rowHeight:28,horizontalAlignment:'center',verticalAlignment:'center'};
      note.getRange('A12:G29').format.verticalAlignment='top';
      note.getRange('G12:G29').format.wrapText=true;
      note.getRange('F12:F29').format.fill='#FFF4D4';
      for(const [col,width] of Object.entries({A:22,B:20,C:9,D:10,E:10,F:16,G:86}))note.getRange(`${col}1:${col}29`).format.columnWidth=width;
      for(let r=12;r<=29;r++)note.getRange(`A${r}:G${r}`).format.rowHeight=Math.max(60,Math.ceil(String(noteValues[r-1][6]).length/40)*15+12);
      note.freezePanes.freezeRows(11);
    }
    note.getRange('B8').values=[[`本文件为${coder}编号版，主表采用${coder}材料盲号，本页保留A/B对照`]];
    book.recalculate();
    const after=sheet.getRange('A1:E1001').values;
    for(let r=0;r<1001;r++)for(let c=0;c<3;c++)if(after[r][c]!==before[r][c])throw new Error(`${coder} source cell changed ${r}/${c}`);
    if(after.slice(1).some(r=>![0,1].includes(r[3])||!r[4]))throw new Error(`${coder} incomplete`);
    const scan=await book.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1200});
    await fs.writeFile(path.join(support,`split-${coder}-inspection.ndjson`),scan.ndjson);
    for(const [label,name,range] of [['opening',sheetName,'A1:E6'],['confirmation','核验确认记录','A1:G15'],['longest',sheetName,`A${longest.row}:E${longest.row}`]]){
      const img=await book.render({sheetName:name,range,scale:1.2,format:'png'});
      await fs.writeFile(path.join(support,`split-${coder}-${label}.png`),new Uint8Array(await img.arrayBuffer()));
    }
    const folder=path.join(out,`编码者${coder}结果`);
    await fs.mkdir(folder,{recursive:true});
    const filename=`真人核验确认-${coder}-200条.xlsx`;
    const target=path.join(folder,filename);
    const candidate=path.join(support,`split-${coder}.candidate.xlsx`);
    await (await SpreadsheetFile.exportXlsx(book)).save(candidate);
    if(coder==='A')await fs.copyFile(candidate,target);
    else{
      const rename="import sys,zipfile,xml.etree.ElementTree as E\nsrc,dst=sys.argv[1:3]\nns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}\nwith zipfile.ZipFile(src) as z,zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as o:\n for item in z.infolist():\n  data=z.read(item.filename)\n  if item.filename=='xl/workbook.xml':\n   root=E.fromstring(data)\n   for s in root.find('m:sheets',ns):\n    if s.attrib['name']=='独立初判':s.set('name','真人核验结果')\n   data=E.tostring(root,encoding='utf-8',xml_declaration=True)\n  o.writestr(item,data)\n";
      execFileSync(python,['-c',rename,candidate,target]);
    }
    const sourceFolder=path.join(delivery,`独立真人判读-200条-20261013/发给编码者${coder}`);
    for(const sub of ['材料','附件'])await fs.cp(path.join(sourceFolder,sub),path.join(folder,sub),{recursive:true});
    await fs.copyFile(path.join(sourceFolder,'共同编码手册.txt'),path.join(folder,'共同编码手册.txt'));
    const submission=`真人核验确认提交说明（${coder}编号版）\n\n核验者身份：真人（用户本人，姓名未提供）\n确认日期：2026年10月13日\n结果阶段：AI辅助后的真人核验确认\n录入方式：AI根据用户本人确认代录\n\n用户已确认人工核验与复核结果一致，并明确A-036/I、A-120/I、A-178/I、A-122/I、A-160/F五项全部填1。上述条目在B版中的对应编号依原盲号映射转换。\n\n本文件采用${coder}材料编号和该编号版的原文链接，200条、1000项判断全部填写，D列为判定，E列为核验依据。正例计数S=27、E=13、Ec=20、I=32、F=16；108项为1、892项为0，无待定。\n\nA版与B版是同一份用户真人核验确认结果按两套材料盲号分别导出。A/B表示材料编号版本；两份不代表两位真人独立完成的首次盲评。982项保留原AI A/B一致值，18项按用户确认结论整合；原首判文件另行保留。\n\n文件：${filename}\n“核验确认记录”页保留18项原判与确认值及A/B编号对照。\n`;
    await fs.writeFile(path.join(folder,'提交说明.txt'),submission);
    const ids=finalData.records.map(r=>r[`${coder}_id`]).sort();
    const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>真人核验确认 ${coder}编号版</title><style>body{max-width:850px;margin:45px auto;padding:0 24px;font:17px/1.7 system-ui;color:#263544}a{color:#205ea8}</style><h1>真人核验确认 ${coder}编号版</h1><p>用户本人真人核验确认，AI根据确认结果代录。200条、1000项判断已填写。</p><ul><li><a href="${filename}">打开结果Excel</a></li><li><a href="提交说明.txt">提交说明</a></li><li><a href="共同编码手册.txt">共同编码手册</a></li></ul><h2>原文材料</h2><ul>${ids.map(id=>`<li><a href="材料/${id}.html">${id}</a></li>`).join('')}</ul></html>`;
    await fs.writeFile(path.join(folder,'开始阅读.html'),html);
    await fs.writeFile(path.join(folder,'材料目录.html'),html);
    const reopened=await SpreadsheetFile.importXlsx(await FileBlob.load(target));
    const saved=reopened.worksheets.getItem('真人核验结果').getRange('A2:E1001').values;
    for(let r=0;r<1000;r++)if(saved[r][3]!==entries[r][0]||saved[r][4]!==entries[r][1])throw new Error(`${coder} export mismatch row ${r+2}`);
    reports.push({coder,path:target,judgments:1000,pending:0,counts:finalData.positive_counts,saved_file_reimported:true});
  }
  for(const [p,hash] of Object.entries(originalHashes))if(createHash('sha256').update(await fs.readFile(p)).digest('hex')!==hash)throw new Error(`Source changed ${p}`);
  const portal=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>真人核验确认结果</title><style>body{max-width:800px;margin:45px auto;padding:0 24px;font:17px/1.7 system-ui}li{margin:15px}</style><h1>真人核验确认结果</h1><p>A、B分别采用对应的材料编号，均为用户本人核验确认后的完整200条结果。</p><ul><li><a href="编码者A结果/开始阅读.html">打开A编号版结果与材料</a></li><li><a href="编码者B结果/开始阅读.html">打开B编号版结果与材料</a></li><li><a href="真人核验确认-200条.xlsx">此前的合并核验表</a></li></ul></html>`;
  await fs.writeFile(path.join(out,'开始阅读.html'),portal);
  await fs.writeFile(path.join(support,'split-build-result.json'),JSON.stringify({reports,originalHashes},null,2));
  console.log(JSON.stringify(reports));
  process.exit(0);
}
const verifying = process.argv.includes('--verify-export');
const input = verifying ? path.join(out,'真人核验确认-200条.xlsx') : path.join(aiRoot,'AI复核者A/AI复核-A-200条.xlsx');
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(input));
if(verifying){
  const rows=wb.worksheets.getItem('真人核验结果').getRange('A1:E1001').values;
  const result=JSON.parse(await fs.readFile(path.join(out,'真人核验结果.json'),'utf8'));
  const lookup=new Map(result.records.map(r=>[r.A_id,r]));
  for(const [id,,dim,value,reason] of rows.slice(1)){
    const expected=lookup.get(id).judgments[dim];
    if(value!==expected.value||reason!==expected.reason)throw new Error(`Saved mismatch ${id}/${dim}`);
  }
  const confirmations=wb.worksheets.getItem('核验确认记录').getRange('A12:G29').values;
  for(const [id,,dim,,,value] of confirmations)if(value!==lookup.get(id).judgments[dim].value)throw new Error(`Confirmation mismatch ${id}/${dim}`);
  const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1500});
  await fs.writeFile(path.join(support,'final-export-inspection.ndjson'),scan.ndjson);
  console.log(JSON.stringify({saved_workbook_reimported:true,judgments_matched:rows.length-1,confirmations_matched:confirmations.length,scan:scan.ndjson}));
  process.exit(0);
}
const main = wb.worksheets.getItem('独立初判');

if (process.argv.includes('--preview')) {
  const view = await wb.render({sheetName:'独立初判',range:'A1:E6',scale:1.3,format:'png'});
  await fs.writeFile(path.join(support,'source-preview.png'),new Uint8Array(await view.arrayBuffer()));
  console.log((await wb.inspect({kind:'sheet',include:'id,name',maxChars:1200})).ndjson);
  console.log(wb.help('worksheet.name',{include:'index,notes,examples',maxChars:1800}).ndjson);
  console.log(JSON.stringify(main.getRange('A1:E2').values));
  process.exit(0);
}

const readJson = async p => JSON.parse(await fs.readFile(p,'utf8'));
const insist = (ok,msg) => { if(!ok) throw new Error(msg); };
const dimensions = ['S','E','Ec','I','F'];
const reviewRoot = path.join(aiRoot,'分歧复核-20261013');
const review = await readJson(path.join(reviewRoot,'分歧复核建议.json'));
const pairing = await readJson(path.join(aiRoot,'_build/pairing.json'));
const aPred = new Map((await readJson(path.join(aiRoot,'AI复核者A/predictions.json'))).map(r=>[r.blind_id,r]));
const bPred = new Map((await readJson(path.join(aiRoot,'AI复核者B/predictions.json'))).map(r=>[r.blind_id,r]));
const rowsBefore = main.getRange('A1:E1001').values;
const originalLayout = await readJson(path.join(aiRoot,'_build/A-layout-adjustments.json'));
const independent = await readJson(path.join(support,'独立校验-1000项.json'));
const pairByA = new Map(pairing.map(p=>[p.A,p]));
const confirmation = {
  reviewer_type:'真人', reviewer:'用户本人', recording_method:'AI依据用户确认代录',
  date:'2026-10-13', stage:'AI辅助后的真人核验确认',
  statements:['我人工核验与你的结果一致你填写一下结果然后给我对应的文件路径吧 填写为真人就可以','5项全部确认填1'],
  independently_blinded_human_submissions:0,
  scope:'整合982项原A/B一致值与18项用户确认的复核结果；5项边界均按用户明确回复填1。',
};
const extra = {
 'A-016/E':'原PDF第29—32页的“上述”包括一般因果推断方法；第34页的疗效估计为后续应用例证。',
 'A-084/S':'原PDF第13页（印刷第10页）后句另对窄治疗窗药物规定混用限制，不将其转作当前一般相容性评估的对象。',
 'A-088/S':'紧前第三十八条：对药品的安全性、有效性和质量可控性等进行综合审评。当前“通过”决定上市许可。',
 'A-088/E':'紧前第三十八条：对药品的安全性、有效性和质量可控性等进行综合审评。当前“通过”决定上市许可。',
 'A-105/I':'CTX-ef584d0a627b3b27b940明确30日通道将审评审批资源向符合条件的创新药临床试验申请倾斜。',
 'A-126/S':'同版《实施办法》第七条分支要求提交用于证明药品安全性、有效性和质量可控性的全部试验数据。按确指标准完整读取，此分支足以记录S，不推广为全部药类条件。',
 'A-126/E':'同版《实施办法》第七条分支要求提交用于证明药品安全性、有效性和质量可控性的全部试验数据。按确指标准完整读取，此分支足以记录E，不推广为全部药类条件。',
 'A-160/Ec':'依据包内2025年《支持创新药高质量发展的若干措施》第（七）条：“通过协商合理确定商保创新药目录内药品结算价，探索更严格的价格保密机制。”仅使用同版同一目录的直接价格机制。',
};
const resolvedReasons = {
 'A-036/I':'真人确认采用I3支持目标路径：同段明确附条件上市药品完成确证性研究需要临床数据积累和验证时间，当前以更宽裕的目录申报时间保留机会；将这一与研究任务直接相连的申请机会计作研发支持。',
 'A-120/I':'真人确认采用I3支持目标路径：同段将确证性研究所需的数据积累和验证时间，与当前最多“5年＋3年”的目录申报机会直接相连；该具体机会按研发支持纳入。保留转常规批准时间等原条件。',
 'A-178/I':'真人确认采用I3支持目标路径：“这一安排”确指同段为确证性研究预留的最多“5年＋3年”目录申请机会，当前明确评价其对创新与证据的支持；与A-036、A-120按同一证据链计入。',
 'A-122/I':'真人确认将同条前置点对点目录指导作为I3研发支持机会：当前有针对性安排创新药目录政策服务，同一（三）条允许上市申请获受理的创新药同步申请指导；该服务位于“加大创新药研发支持力度”下。认定范围为这项有具体对象与可用服务的前置安排，不单凭标题或交流形式赋I。',
 'A-160/F':'真人确认采用所需药品覆盖缺口与针对性补充机会的解释：2025年《若干措施》第（七）条将“患者获益显著且超出基本医保保障范围”的创新药重点纳入商保目录，并推荐商业健康保险和医疗互助参考使用。按该联合条件与补充推荐的直接关系计F；不推定实际承保、失治或无替代药。',
};
const adjudications = new Map();
for(const r of review.records){
  const key = `${r.A_id}/${r.dimension}`;
  const value = r.recommended_value ?? 1;
  insist(r.recommended_value !== null || r.provisional_preference === 1,`unexpected unresolved ${key}`);
  const reason = `当前：“${r.current_text}”\n核验依据：${resolvedReasons[key] ?? r.reason}${extra[key] ? '\n'+extra[key] : ''}`;
  adjudications.set(key,{...r,value,confirmed_reason:reason,rule_boundary_confirmed:r.recommended_value===null});
}
insist(adjudications.size===18,'18 adjudications required');
const finalRecords=[];
let consistent=0;
for(const pair of pairing){
 const judgments={};
 for(const dim of dimensions){
  const a=aPred.get(pair.A).judgments[dim];
  const b=bPred.get(pair.B).judgments[dim];
  const confirmed=adjudications.get(`${pair.A}/${dim}`);
  if(!confirmed){insist(a.value===b.value && [0,1].includes(a.value),`unresolved ${pair.A}/${dim}`);consistent++;}
  judgments[dim]={value:confirmed?.value ?? a.value, reason:confirmed?.confirmed_reason ?? a.reason,
    value_origin:confirmed?'真人确认复核结论':'原AI A/B一致值，整合保留',
    initial_A:a.value,initial_B:b.value,reviewer_type:'真人',confirmation_stage:'用户核验确认'};
 }
 finalRecords.push({unit_id:pair.unit_id,A_id:pair.A,B_id:pair.B,judgments});
}
insist(consistent===982,'982 consistent cells expected');
const finalByA=new Map(finalRecords.map(r=>[r.A_id,r]));
const values=rowsBefore.slice(1).map(([id,,dim])=>{
 const j=finalByA.get(id).judgments[dim];
 return [j.value,j.reason];
});
const counts=Object.fromEntries(dimensions.map(d=>[d,finalRecords.reduce((n,r)=>n+r.judgments[d].value,0)]));
insist(JSON.stringify(counts)===JSON.stringify(independent.positive_counts),'independent counts mismatch');
const protectedPaths=[input,path.join(aiRoot,'AI复核者B/AI复核-B-200条.xlsx'),path.join(aiRoot,'AI复核者A/predictions.json'),path.join(aiRoot,'AI复核者B/predictions.json'),path.join(reviewRoot,'分歧复核建议.json')];
const protectedHashes=Object.fromEntries(await Promise.all(protectedPaths.map(async p=>[p,createHash('sha256').update(await fs.readFile(p)).digest('hex')])));

// Record the artifact authoring operation once immediately before the first edit.
const markerReceipt=path.join(support,'operation-started.json');
try{await fs.access(markerReceipt);}catch{
 const marker='/Users/rainbow/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1009.11318/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs';
 const result=execFileSync(process.execPath,[marker,'--operation-kind','edit','--expected-output-count','1','--output-format','xlsx'],{cwd:support,encoding:'utf8'});
 await fs.writeFile(markerReceipt,JSON.stringify({result},null,2));
}
main.getRange('D1:E1').values=[['真人核验判定（0/1）','核验理由与原文依据']];
main.getRange('D2:E1001').values=values;
const changedRows=[];
for(let i=1;i<rowsBefore.length;i++){
 const [id,,dim]=rowsBefore[i];
 if(adjudications.has(`${id}/${dim}`)){
  const units=values[i-1][1].split('\n').reduce((sum,s)=>sum+Math.ceil([...s].reduce((n,c)=>n+(c.codePointAt(0)>255?2:1),0)/85),0);
  const height=Math.max(originalLayout.rowHeights[i+1]??42,units*18+14);
  insist(height<=409,`row ${i+1} too high: ${height}`);
  main.getRange(`A${i+1}:E${i+1}`).format.rowHeight=height;
  changedRows.push({row:i+1,id,dimension:dim,height});
 }
}
const note=wb.worksheets.add('核验确认记录');
note.showGridLines=false;
note.getRange('A1:G29').format.font={name:'Arial',size:10};
note.getRange('A1').values=[['真人核验确认记录']];
note.getRange('A1').format.font={bold:true,size:14};
const meta=[['核验者','用户本人（真人）'],['结果阶段','AI辅助后的真人核验确认'],['录入方式','AI依据本人确认代录'],['确认日期','2026年10月13日'],['本次确认','18项复核结果；原5项边界全部确认填1'],['结果构成','982项原A/B一致值＋18项真人确认结果，共1000项'],['盲号对应','主表采用A材料盲号，本页保留B盲号以便对应'],['确认原话','“我人工核验与你的结果一致”；“5项全部确认填1”']];
note.getRange('A2:B9').values=meta;
note.getRange('A2:G9').format.rowHeight=23;
note.getRange('A1:G1').format.rowHeight=28;
note.getRange('A11:G11').values=[['A材料盲号','B材料盲号','维度','A首判','B首判','真人确认值','确认要点']];
note.getRange('A11:G11').format={fill:'#304B61',font:{bold:true,color:'#FFFFFF'},rowHeight:28,horizontalAlignment:'center',verticalAlignment:'center'};
const details=review.records.map(r=>{
 const c=adjudications.get(`${r.A_id}/${r.dimension}`);
 return [r.A_id,r.B_id,r.dimension,r.A.value===null?'待定':r.A.value,r.B.value===null?'待定':r.B.value,c.value,resolvedReasons[`${r.A_id}/${r.dimension}`]??r.reason];
});
note.getRange('A12:G29').values=details;
note.getRange('A12:G29').format.verticalAlignment='top';
note.getRange('G12:G29').format.wrapText=true;
note.getRange('F12:F29').format.fill='#FFF4D4';
for(const [col,width] of Object.entries({A:22,B:20,C:9,D:10,E:10,F:16,G:86}))note.getRange(`${col}1:${col}29`).format.columnWidth=width;
for(let i=0;i<details.length;i++){
 const height=Math.max(60,Math.ceil(details[i][6].length/40)*15+12);
 note.getRange(`A${i+12}:G${i+12}`).format.rowHeight=height;
}
note.freezePanes.freezeRows(11);
wb.recalculate();
const after=main.getRange('A1:E1001').values;
for(let i=0;i<rowsBefore.length;i++)for(let c=0;c<3;c++)insist(after[i][c]===rowsBefore[i][c],`source cell changed ${i}/${c}`);
insist(after.slice(1).every(r=>[0,1].includes(r[3])&&typeof r[4]==='string'&&r[4].length>0),'incomplete results');
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final human confirmed workbook',maxChars:1500});
await fs.writeFile(path.join(support,'formula-inspection.ndjson'),errors.ndjson);
const longest=changedRows.reduce((best,r)=>r.height>best.height?r:best);
for(const [file,sheetName,range] of [['final-opening','独立初判','A1:E6'],['final-longest','独立初判',`A${longest.row}:E${longest.row}`],['final-confirmation-top','核验确认记录','A1:G15'],['final-confirmation-bottom','核验确认记录','A24:G29']]){
 const image=await wb.render({sheetName,range,scale:1.3,format:'png'});
 await fs.writeFile(path.join(support,file+'.png'),new Uint8Array(await image.arrayBuffer()));
}
const candidate=path.join(support,'result.candidate.xlsx');
await (await SpreadsheetFile.exportXlsx(wb)).save(candidate);
const filename='真人核验确认-200条.xlsx';
const output=path.join(out,filename);
// The public artifact API did not expose a worksheet rename operation. Rename
// only the worksheet title in the exported package; cell content stays authored
// by Artifact Tool. This workbook has no formulas referencing that tab name.
const renameScript="import sys,zipfile,xml.etree.ElementTree as E\nsrc,dst=sys.argv[1:3]\nns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}\nwith zipfile.ZipFile(src) as z,zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as o:\n for item in z.infolist():\n  data=z.read(item.filename)\n  if item.filename=='xl/workbook.xml':\n   root=E.fromstring(data)\n   for s in root.find('m:sheets',ns):\n    if s.attrib['name']=='独立初判':s.set('name','真人核验结果')\n   data=E.tostring(root,encoding='utf-8',xml_declaration=True)\n  o.writestr(item,data)\n";
execFileSync('/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',['-c',renameScript,candidate,output]);
const humanPackage=path.join(delivery,'独立真人判读-200条-20261013/发给编码者A');
for(const folder of ['材料','附件'])await fs.cp(path.join(humanPackage,folder),path.join(out,folder),{recursive:true});
await fs.copyFile(path.join(humanPackage,'共同编码手册.txt'),path.join(out,'共同编码手册.txt'));
await fs.writeFile(path.join(out,'真人核验结果.json'),JSON.stringify({confirmation,positive_counts:counts,records:finalRecords},null,2)+'\n');
const submission=`真人核验确认提交说明\n\n核验者身份：真人（用户本人，姓名未提供）\n确认日期：2026年10月13日\n结果阶段：AI辅助后的真人核验确认\n录入方式：AI根据用户本人确认代录\n\n用户确认原话：\n1. “我人工核验与你的结果一致你填写一下结果然后给我对应的文件路径吧 填写为真人就可以”\n2. 对A-036/I、A-120/I、A-178/I、A-122/I、A-160/F的补充确认：“5项全部确认填1”。\n\n填写结果：200条原文，每条S、E、Ec、I、F五维，共1000项，全部填写0或1。主表采用A材料盲号，D列为真人核验判定，E列为核验理由与原文依据。\n18项复核结果按用户确认填写；其他982项沿用A/B原一致值。原5项边界已经按本次人工确认填1，A-117的I、F均填0。\n\n结果计数：S=27、E=13、Ec=20、I=32、F=16项为1，共108项为1，892项为0，待定0项。\n\n本次为同一位用户的核验确认与结果整合。原AI A/B首判、分歧复核记录和两位真人盲评原始材料另行保留；不将本文件记为两位真人分别独立填写的首次盲评。\n\n文件：${filename}\n辅助数据：真人核验结果.json\n“核验确认记录”页保留18项原判与确认值。点击主表B列可打开对应原文及附件。\n`;
await fs.writeFile(path.join(out,'提交说明.txt'),submission);
const html=`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>真人核验确认结果</title><style>body{max-width:850px;margin:45px auto;padding:0 24px;font:17px/1.7 system-ui;color:#263544}a{color:#205ea8}li{margin:8px}</style><h1>真人核验确认结果</h1><p>用户本人核验确认，AI根据确认结果代录。200条原文、1000项判断均已填写，5项原边界全部填1。</p><ul><li><a href="${filename}">打开结果Excel</a></li><li><a href="提交说明.txt">提交说明</a></li><li><a href="共同编码手册.txt">共同编码手册</a></li></ul><h2>原文材料</h2><ul>${[...pairByA.keys()].sort().map(id=>`<li><a href="材料/${id}.html">${id}</a></li>`).join('')}</ul></html>`;
await fs.writeFile(path.join(out,'开始阅读.html'),html);
await fs.writeFile(path.join(out,'材料目录.html'),html);
for(const [p,hash] of Object.entries(protectedHashes))insist(createHash('sha256').update(await fs.readFile(p)).digest('hex')===hash,`protected source changed ${p}`);
await fs.writeFile(path.join(support,'build-result.json'),JSON.stringify({output,positive_counts:counts,records:200,judgments:1000,pending:0,confirmed_cases:18,prior_boundaries_confirmed:5,changedRows,protectedHashes,formulaInspection:errors.ndjson},null,2));
console.log(JSON.stringify({output,positive_counts:counts,pending:0,rendered:4,protected_files_unchanged:protectedPaths.length}));
