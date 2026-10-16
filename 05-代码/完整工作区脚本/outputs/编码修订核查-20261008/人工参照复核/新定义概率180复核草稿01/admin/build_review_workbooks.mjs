import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const admin=path.dirname(fileURLToPath(import.meta.url));
const out=path.dirname(admin);
const data=JSON.parse(await fs.readFile(path.join(admin,'builder_payload.json'),'utf8'));
const previews=path.join(admin,'previews'); await fs.mkdir(previews,{recursive:true});
const chunks=s=>Array.from({length:Math.max(1,Math.ceil(s.length/360))},(_,i)=>s.slice(i*360,(i+1)*360));
const col=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const q=s=>String(s).replaceAll('"','""');
const link=(url,label)=>`=HYPERLINK("${q(url)}","${q(label)}")`;
const logs={author:'AI材料整理',native_excel_application_opened:false,workbooks:{}};
const shaManual=data.manual_sha256;

function table(wb,name,headers,rows,widths,title,note){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 const end=rows.length+5,last=col(headers.length);
 s.getRange(`A1:${last}${Math.max(end,8)}`).format.font={name:'Arial',size:11,color:'#18202A'};
 s.getRange(`A1:${last}${Math.max(end,8)}`).format.verticalAlignment='center';
 s.getRange('A2').values=[[title]];s.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#18202A'};
 s.getRange('A3').values=[[note]];s.getRange('A3').format.font={name:'Arial',size:10,color:'#6A4C16'};
 s.getRange(`A5:${last}5`).values=[headers];
 if(rows.length)s.getRange(`A6:${last}${end}`).values=rows;
 for(let i=0;i<widths.length;i++)s.getRange(`${col(i+1)}1:${col(i+1)}${Math.max(end,8)}`).format.columnWidth=widths[i];
 s.getRange(`A5:${last}5`).format={fill:'#243B53',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
 s.getRange('A5:'+last+'5').format.rowHeight=32;
 s.getRange(`A6:${last}${Math.max(end,6)}`).format.wrapText=true;
 s.getRange(`A6:${last}${Math.max(end,6)}`).format.rowHeight=46;
 s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(name==='判读'?2:1);
 if(['判读','材料问题'].includes(name)){
  const t=s.tables.add(`A5:${last}${end}`,true,'Table'+(name==='判读'?'Judgements':'MaterialIssues'));
  t.showFilterButton=true;
  s.getRange(`A5:${last}5`).format={fill:'#243B53',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true};
 }
 return s;
}
function rowHeightFor(s,rows,widths){
 rows.forEach((r,i)=>{
  const lines=Math.max(...r.map((x,j)=>{if(x==null)return 1;return String(x).split('\n').reduce((a,t)=>a+Math.max(1,Math.ceil(t.length/Math.max(6,widths[j]*0.42))),0);}));
  s.getRange(`A${i+6}:${col(r.length)}${i+6}`).format.rowHeight=Math.min(400,Math.max(34,lines*16+12));
 });
}
for(const coder of ['A','B']){
 const pack=data.packages[coder];const wb=Workbook.create();const dir=path.join(out,coder);
 const instructionRows=[
  ['材料状态','草稿：待root材料来源位置与可见版式核查后再发。','尚未发出或填写。'],
  ['复核范围','180个既有概率单位，每单位重新填写S、E、Ec、I、F，共900项。','本包不含挑战材料；不是新抽样。'],
  ['填写顺序','按匿名号阅读“当前材料”和“必要语境”，需要时打开完整HTML。','原文拆格按片段号连续阅读，不得只看第1片。'],
  ['0、1与空白','判定只填0或1；未完成或材料不足时留空。','0表示材料完整但无相应证据，不能表示缺字或缺语境。'],
  ['理由与引文','每维写判读理由、原文引文；依赖语境时注明语境编号及承接关系。','标题、父段的全部维度不自动复制给当前句。'],
  ['材料问题','在“材料问题”记录具体位置、影响维度和待补内容。','受影响判定留空；补料和后续裁定另存。'],
  ['独立提交','两位分别完成并保存，不查看对方此次结果。','历史看过答案的情况仍须按实记录。'],
  ['固定手册','随附共用编码手册.md；本表“固定手册”逐字保留全文。',shaManual],
  ['来源链接','仅列当前材料实际声明的源路径；根路径在原工作环境中可访问。','路径存在/字节SHA不等于像素文字或源位置认证。'],
  ['整理身份','AI代理仅整理材料与空白表格。','既有真人裁定事实与原结果保留；本次未产生真人判定。'],
  ['实际人员姓名/编号',null,'由实际执行者填写'],
  ['专业背景与编码经验',null,'由实际执行者填写'],
  ['是否复核过旧结果/人员关系',null,'由实际执行者填写'],
  ['开始日期',null,'实际开始日期，不按文件生成时间代填'],
  ['提交日期',null,'实际首次提交日期'],
  ['实际使用手册版本/SHA',null,'由实际执行者确认使用后填写'],
  ['实际使用材料包/补料版本',null,'由实际执行者填写'],
  ['是否曾见原AI初判',null,'是/否/未知及接触范围'],
  ['是否曾见旧A/B答案',null,'是/否/未知及接触范围'],
  ['是否曾见机器/LLM结果',null,'是/否/未知及接触范围'],
  ['是否曾见他人意见/目标指标',null,'是/否/未知及接触范围'],
  ['本次是否独立完成',null,'由实际执行者填写；不预设为是'],
  ['培训内容及实际日期',null,'由实际执行者填写'],
  ['实际沟通/讨论时间与范围',null,'由实际执行者填写'],
  ['补料与其他执行情况',null,'由实际执行者填写'],
 ];
 const guide=table(wb,'填写说明',['项目','内容 / 实际填写','说明'],instructionRows,[31,91,65],`新定义人工复核 · ${coder}包`,'黄色空格供实际执行者填写；所有判读答案保持空白。');
 guide.getRange('B16:B30').format.fill='#FFF2CC';rowHeightFor(guide,instructionRows,[31,91,65]);guide.freezePanes.unfreeze();guide.tabColor='#243B53';
 const jr=[];for(const u of pack.units)for(const d of ['S','E','Ec','I','F'])jr.push([u.anonymous_id,d,null,null,null,null,null]);
 const judgement=table(wb,'判读',['匿名编号','维度','判定0/1','判读理由','原文引文','语境编号与承接关系','暂缓/问题单号'],jr,[17,10,11,43,49,43,27],`逐维判读 · ${coder}`,'每单位5行；未完成或材料不足留空，勿以0替代。');
 judgement.getRange('C6:C905').dataValidation={allowBlank:true,rule:{type:'whole',operator:'between',formula1:0,formula2:1},errorAlert:{style:'stop',title:'只接受0或1',message:'填写整数0或1；材料不足或未完成请留空并登记材料问题。'}};
 judgement.getRange('C6:G905').format.fill='#FFF8E3';judgement.getRange('C6:C905').setNumberFormat('0');judgement.getRange('C6:C905').format.horizontalAlignment='center';judgement.getRange('A6:G905').format.rowHeight=58;
 for(let r=10;r<=905;r+=5)judgement.getRange(`A${r}:G${r}`).format.borders={bottom:{style:'thin',color:'#B9C7D5'}};
 const current=[],context=[],problem=[],currentLinks=[],contextLinks=[];
 for(const u of pack.units){
  const g=u.source_only_view;const o=u.text_occurrences.find(v=>v.node_id===null);const links=o?.source_links||[];const src=links.find(z=>z.role==='source_path');
  const cp=chunks(g.text);cp.forEach((text,i)=>{current.push([u.anonymous_id,`${i+1}/${cp.length}`,text,JSON.stringify(g.pages||[]),null,links.map(z=>z.path).join('\n'),'待实际源位置核查']);currentLinks.push({row:current.length+5,html:`完整材料.html#${u.anonymous_id}`,source:src?.uri});});
  for(const node of g.contexts){
   const occ=u.text_occurrences.find(v=>v.node_id===node.context_id);const ls=occ?.source_links||[];const st={kind:node.kind,...node.structure};if(node.headers)st.headers=node.headers;
   const pieces=chunks(node.text||'');pieces.forEach((text,i)=>{context.push([u.anonymous_id,node.context_id,JSON.stringify(st),`${i+1}/${pieces.length}`,text,ls.map(z=>z.path).join('\n'),null,'待实际源位置核查']);contextLinks.push({row:context.length+5,html:`完整材料.html#${node.context_id}`,source:ls.find(z=>z.role==='source_path')?.uri});});
  }
  for(const z of u.unbound_declared_material){context.push([u.anonymous_id,z.item_id,JSON.stringify({role:z.role}), '1/1',z.text,'原声明边界；来源绑定待核',null,'尚未投影/绑定，不作已认证语境']);contextLinks.push({row:context.length+5,html:`完整材料.html#${u.anonymous_id}`});}
  problem.push([u.anonymous_id,null,null,null,null,u.material_notes.length?u.material_notes.map(z=>`${z.issue_id}: ${z.code}`).join('\n'):'所有来源位置仍待核',null]);
 }
 const cur=table(wb,'当前材料',['匿名编号','片段','当前原文','原页码','打开全文','实际声明来源路径','核查状态'],current,[17,9,106,15,16,80,32],`完整当前材料 · ${coder}`,'原文逐字保留；同编号片段按顺序连续阅读。');rowHeightFor(cur,current,[17,9,106,15,16,80,32]);
 for(const l of currentLinks)cur.getRange(`E${l.row}`).values=[['查看全文及源链接']];
 cur.getRange(`E6:E${current.length+5}`).format.font={name:'Arial',size:11,color:'#1859A0'};
 const ctx=table(wb,'必要语境',['匿名编号','发生/节点编号','层级、顺序与表格定位','片段','原文','实际声明来源路径','打开全文','核查状态'],context,[17,21,54,8,106,80,18,32],`必要语境逐发生 · ${coder}`,'保留原顺序、父子关系及表格行列；不将全部语境自动作为当前证据。');rowHeightFor(ctx,context,[17,21,54,8,106,80,18,32]);
 for(const l of contextLinks)ctx.getRange(`G${l.row}`).values=[['查看该语境及源链接']];
 ctx.getRange(`G6:G${context.length+5}`).format.font={name:'Arial',size:11,color:'#1859A0'};
 await fs.writeFile(path.join(admin,`native_hyperlinks_${coder}.json`),JSON.stringify({current:currentLinks.map(l=>({cell:`E${l.row}`,target:l.html})),contexts:contextLinks.map(l=>({cell:`G${l.row}`,target:l.html}))},null,2)+'\n');
 const issues=table(wb,'材料问题',['匿名编号','问题类型','影响维度','位置与具体问题','需要补充的材料','已有接口待核提示','补料后实际处理记录'],problem,[17,23,22,58,50,65,48],`材料问题登记 · ${coder}`,'填写者空栏与既有待核提示分开；受影响判定留空，不强记0。');
 issues.getRange('B6:E185').format.fill='#FFF8E3';issues.getRange('G6:G185').format.fill='#FFF8E3';rowHeightFor(issues,problem,[17,23,22,58,50,65,48]);
 const mr=[];data.manual.split('\n').forEach((line,i)=>chunks(line).forEach((part,j)=>mr.push([i+1,j+1,part])));
 const manual=table(wb,'固定手册',['原行号','续片','固定手册原文'],mr,[11,9,145],'五维共用编码规则 · 固定全文','随附MD字节SHA：'+shaManual);rowHeightFor(manual,mr,[11,9,145]);
 for(const [name,rows] of [['判读',jr],['当前材料',current],['必要语境',context],['材料问题',problem],['固定手册',mr]])for(const r of rows)for(const v of r)if(typeof v==='string'&&v.length>32767)throw Error('Excel cell exceeds maximum: '+name);
 wb.recalculate();
 const key=await wb.inspect({kind:'table',range:'判读!A5:G10',include:'values,formulas',tableMaxRows:6,tableMaxCols:7,maxChars:3000});
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:100},summary:'final formula error scan',maxChars:3000});
 await fs.writeFile(path.join(admin,`inspect_${coder}.ndjson`),key.ndjson+'\n'+errors.ndjson);
 const ranges={'填写说明':'A5:C10','判读':'A5:G10','当前材料':'A5:E7','必要语境':'A5:E7','材料问题':'A5:G8','固定手册':'A5:C10'};
 for(const [name,range] of Object.entries(ranges)){
  const image=await wb.render({sheetName:name,range,scale:1,format:'png'});
  await fs.writeFile(path.join(previews,`${coder}_${name}.png`),new Uint8Array(await image.arrayBuffer()));
 }
 const file=path.join(dir,`编码员${coder}-新定义180条待填-草稿.xlsx`);
 await (await SpreadsheetFile.exportXlsx(wb)).save(file);
 logs.workbooks[coder]={path:file,judgement_rows:jr.length,unit_count:pack.units.length,current_fragment_rows:current.length,context_fragment_rows:context.length,manual_fragment_rows:mr.length,personnel_blank_cells:'填写说明!B16:B30',label_blank_cells:'判读!C6:C905',rendered_sheets:Object.keys(ranges),recalculated:true,inspection_saved:`inspect_${coder}.ndjson`,manual_sha256:shaManual};
 console.log(JSON.stringify({coder,file,judgement_rows:jr.length,current_fragment_rows:current.length,context_fragment_rows:context.length}));
}
await fs.writeFile(path.join(admin,'workbook_build_log.json'),JSON.stringify(logs,null,2)+'\n');
