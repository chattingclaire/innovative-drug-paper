import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
// Loaded only for a real authoring run, never by --self-test.
let Workbook, SpreadsheetFile;
const dir=path.dirname(fileURLToPath(import.meta.url));
// Authoring is deliberately explicit. The caller starts the artifact operation
// once before an actual run; --check only parses this module and performs no I/O.
function parseOptions(args){
 const options={formal:false,challenge:null,challengeRoot:path.join(dir,'R200'),selfTest:false,coders:[]};
 const seen=new Set();
 for(let i=0;i<args.length;i++){
  const arg=args[i];
  if(['--formal','--challenge','--challenge-dir','--self-test'].includes(arg)){
   if(seen.has(arg))throw Error(`Duplicate option: ${arg}`);seen.add(arg);
   if(arg==='--formal')options.formal=true;
   if(arg==='--self-test')options.selfTest=true;
   if(arg==='--challenge'||arg==='--challenge-dir'){
    const value=args[++i];if(!value||value.startsWith('--')||!path.isAbsolute(value))throw Error(`${arg} requires an absolute path`);
    options[arg==='--challenge'?'challenge':'challengeRoot']=value;
   }
  }else if(['A','C'].includes(arg))options.coders.push(arg);
  else throw Error(`Unknown option: ${arg}`);
 }
 if(options.coders.length>1||(options.formal&&options.challenge)||(seen.has('--challenge-dir')&&!options.challenge)||(options.selfTest&&args.length!==1))throw Error('Usage: build_reviews.mjs [--formal | --challenge /abs/completed-R200.json [--challenge-dir /abs/R200]] [A|C]; --self-test');
 if(options.coders.length===0)options.coders=['A','C'];
 return options;
}
const options=parseOptions(process.argv.slice(2));
const formal=options.formal;
const coders=options.coders;
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const requireValue=(condition,message)=>{if(!condition)throw Error(message);};
async function assertNew(file){
 try{await fs.lstat(file);}catch(error){if(error.code==='ENOENT')return;throw error;}
 throw Error(`Refusing to overwrite existing file: ${file}`);
}
async function buildDevelopment(){
const packet=JSON.parse(await fs.readFile(path.join(dir,'开发60-共同无答案材料.json'),'utf8'));
const manifest=JSON.parse(await fs.readFile(path.join(dir,'开发60-盲法与版本清单.json'),'utf8'));
const protocol=await fs.readFile(path.join(dir,'agent-A/五维共用编码协议.md'),'utf8');
const dims=['S','E','Ec','I','F'];
const color={navy:'#17384B',teal:'#126B70',pale:'#E8F4EF',amber:'#FFF0C2',text:'#1F2937',muted:'#E7EEF2'};
const lines=(s,w)=>String(s).split('\n').reduce((n,l)=>n+Math.max(1,Math.ceil([...l].reduce((c,x)=>c+(x.charCodeAt(0)>255?1:.52),0)/w)),0);
function base(s,range){s.showGridLines=false;s.getRange(range).format.font={name:'Arial',size:11,color:color.text};s.getRange(range).format.wrapText=true;s.getRange(range).format.verticalAlignment='top';}
function title(s,last,name,note){s.mergeCells(`A1:${last}1`);s.getRange('A1').values=[[name]];s.getRange(`A1:${last}1`).format={fill:color.navy,font:{name:'Arial',size:17,bold:true,color:'#FFFFFF'},rowHeight:36};s.mergeCells(`A2:${last}2`);s.getRange('A2').values=[[note]];s.getRange(`A2:${last}2`).format.rowHeight=42;}
function header(s,range){s.getRange(range).format={fill:color.teal,font:{bold:true,color:'#FFFFFF'},rowHeight:32};}
const cTypes={paragraph_context:'本单元所在完整段落',nearest_preceding_heading:'邻近标题（未确认父级）',immediately_preceding_paragraph:'前一段（未确认父级）',verified_parent_context:'已核父级',verified_table_context:'已核表格',verified_rule_branch_context:'已核规则分支'};
let contextRows=[];
for(const row of packet.rows){
  contextRows.push([row.id,'来源/页码',`${row.source_title}\n页码：${row.pages?.length?row.pages.join('、'):'输入未提供'}`]);
  for(const [key,value] of Object.entries(row.contexts)){
    for(const v of (Array.isArray(value)?value:[value])){
      const body=typeof v==='string'?v:(v.text??JSON.stringify(v,null,2));
      for(let p=0;p<body.length;p+=600) contextRows.push([row.id,cTypes[key]+(p?`（续${Math.floor(p/600)+1}）`:''),body.slice(p,p+600)]);
    }
  }
}
const manualRows=protocol.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);
for(const coder of coders){
 const result=JSON.parse(await fs.readFile(path.join(dir,`agent-${coder}/result-${coder}.json`),'utf8'));
 if(result.protocol_version!==packet.protocol||!result.protocol_acknowledged)throw Error('Protocol mismatch');
 const idx=new Map(result.rows.map(r=>[r.id,r]));if(idx.size!==60||result.rows.length!==60)throw Error('Result count mismatch');
 const rows=packet.rows.map(r=>{const q=idx.get(r.id);if(!q||dims.some(d=>![0,1,'待定'].includes(q.labels[d])||!q.dimension_reasons[d]))throw Error('Invalid '+r.id);return[r.id,r.text,...dims.map(d=>q.labels[d]),dims.map(d=>`${d}：${q.dimension_reasons[d]}`).join('\n')+`\n证据：${q.evidence}\n综合说明：${q.rationale}`,q.material_issue];});
 const w=Workbook.create(); const s=w.worksheets.add('独立盲评');const c=w.worksheets.add('原文语境');const m=w.worksheets.add('共同手册');
 base(s,'A1:I64');title(s,'I',`新增60条独立盲评｜AI评审 ${coder}`,`${packet.protocol}｜${result.completed_at}\n开发校准；1=涉及，0=不涉及，待定=证据不足。每条依据与原始独立提交一致。`);
 s.getRange('A4:I4').values=[['编号','完整分析单元','S安全','E有效','Ec经济','I创新','F公平','逐维判定依据与证据','材料问题']];header(s,'A4:I4');s.getRange('A5:I64').values=rows;
 s.getRange('A:A').format.columnWidth=16;s.getRange('B:B').format.columnWidth=56;s.getRange('C:G').format.columnWidth=9;s.getRange('H:H').format.columnWidth=80;s.getRange('I:I').format.columnWidth=32;
 s.getRange('C5:G64').format.horizontalAlignment='center';s.getRange('C5:G64').format.font={bold:true,size:12};
 s.getRange('C5:G64').dataValidation={rule:{type:'list',values:['0','1','待定']}};
 s.getRange('C5:G64').conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:color.pale,font:{color:'#155B42',bold:true}}});
 s.getRange('C5:G64').conditionalFormats.add('containsText',{text:'待定',format:{fill:color.amber,font:{color:'#754D00'}}});
 for(let i=0;i<rows.length;i++){
   const ht=Math.max(lines(rows[i][1],31),lines(rows[i][7],46),lines(rows[i][8],18))*15+14;
   if(ht>409)throw Error(`Row too high, redesign required ${coder}/${i}: ${ht}`);
   s.getRange(`A${i+5}:I${i+5}`).format.rowHeight=Math.max(78,ht);
   if(i%2===1){s.getRange(`A${i+5}:B${i+5}`).format.fill='#F5F8FA';s.getRange(`H${i+5}:I${i+5}`).format.fill='#F5F8FA';}
 }
 s.freezePanes.freezeRows(4);s.freezePanes.freezeColumns(2);s.tables.add('A4:I64',true,`Blind${coder}`);
 base(c,`A1:C${contextRows.length+4}`);title(c,'C','同版原文与上下文','Source：开发60-共同无答案材料.json｜输入SHA-256：'+manifest.packet_sha256+'\n只编码独立盲评页的单元；位置相邻不自动确认父级，不继承上级全部标签。');
 c.getRange('A4:C4').values=[['编号','上下文类型','来源原文/上下文（完整保留）']];header(c,'A4:C4');c.getRange(`A5:C${contextRows.length+4}`).values=contextRows;
 c.getRange('A:A').format.columnWidth=16;c.getRange('B:B').format.columnWidth=29;c.getRange('C:C').format.columnWidth=116;
 for(let i=0;i<contextRows.length;i++)c.getRange(`A${i+5}:C${i+5}`).format.rowHeight=Math.max(38,lines(contextRows[i][2],65)*15+14);
 c.freezePanes.freezeRows(4);c.tables.add(`A4:C${contextRows.length+4}`,true,`Contexts${coder}`);
 base(m,`A1:A${manualRows.length+4}`);m.getRange('A:A').format.columnWidth=160;
 m.getRange('A1').values=[['共同编码手册与执行协议']];m.getRange('A1').format={fill:color.navy,font:{size:17,bold:true,color:'#FFFFFF'},rowHeight:36};
 m.getRange('A2').values=[['Source：五维共用编码协议.md｜SHA-256：'+manifest.protocol_sha256+'\nA/C采用同版文字。此文件是AI按人工编码流程提交的开发结果，不是正式真人信度证明。']];m.getRange('A2').format.rowHeight=48;
 m.getRange(`A4:A${manualRows.length+3}`).values=manualRows.map(x=>[x]);
 for(let i=0;i<manualRows.length;i++)m.getRange(`A${i+4}`).format.rowHeight=Math.max(27,lines(manualRows[i],90)*15+12);
 m.freezePanes.freezeRows(2);
 w.recalculate();
 const inspection=await w.inspect({kind:'table',range:'独立盲评!A4:I7',include:'values,formulas',tableMaxRows:4,tableMaxCols:9,maxChars:2000});await fs.writeFile(path.join(dir,`xlsx-inspection-${coder}.ndjson`),inspection.ndjson);
 const error=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Final spreadsheet error scan',maxChars:800});console.log(coder,error.ndjson);
 const output=path.join(dir,`扩充盲评60-${coder}-AI评审.xlsx`);await(await SpreadsheetFile.exportXlsx(w)).save(output);
 for(const [name,sheetName,range] of [['labels','独立盲评','A1:G7'],['reasons','独立盲评','H4:I7'],['end','独立盲评','A62:I64'],['contexts','原文语境','A1:C7'],['manual','共同手册','A1:A9']]){
   const b=await w.render({sheetName,range,scale:1,format:'png'});await fs.writeFile(path.join(dir,`preview-${coder}-${name}.png`),new Uint8Array(await b.arrayBuffer()));
 }
 console.log(JSON.stringify({coder,output,records:rows.length,contextRows:contextRows.length,manualParagraphs:manualRows.length}));
}
}

const formalDims=['S','E','Ec','I','F'];
const formalColor={navy:'#17384B',teal:'#126B70',pale:'#E8F4EF',amber:'#FFF0C2',text:'#1F2937'};
const displayLines=(s,w)=>String(s).split('\n').reduce((n,l)=>n+Math.max(1,Math.ceil([...l].reduce((c,x)=>c+(x.charCodeAt(0)>255?1:.52),0)/w)),0);
const formalOutput=coder=>path.join(dir,`正式盲评600-${coder}-AI评审.xlsx`);
const formalPrefix=coder=>`formal600-${coder}`;
const previewNames=['labels','reasons','end','contexts','contexts-end','manual'];
const filePaths=coder=>({
 workbook:formalOutput(coder),
 inspection:path.join(dir,`${formalPrefix(coder)}-xlsx-inspection.ndjson`),
 errors:path.join(dir,`${formalPrefix(coder)}-xlsx-errors.ndjson`),
 checks:path.join(dir,`${formalPrefix(coder)}-input-checks.json`),
 ...Object.fromEntries(previewNames.map(name=>[name,path.join(dir,`${formalPrefix(coder)}-preview-${name}.png`)])),
});
const challengeOutput=coder=>path.join(dir,`补充挑战200-${coder}-AI评审.xlsx`);
const challengeFilePaths=coder=>({
 workbook:challengeOutput(coder),
 inspection:path.join(dir,`challenge200-${coder}-xlsx-inspection.ndjson`),
 errors:path.join(dir,`challenge200-${coder}-xlsx-errors.ndjson`),
 checks:path.join(dir,`challenge200-${coder}-input-checks.json`),
 ...Object.fromEntries(previewNames.map(name=>[name,path.join(dir,`challenge200-${coder}-preview-${name}.png`)])),
});
const pending='待定';
const own=(obj,key)=>Object.prototype.hasOwnProperty.call(obj,key);
const isObject=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
function exactDimensions(value,name){
 requireValue(isObject(value)&&Object.keys(value).length===5&&formalDims.every(d=>own(value,d)),`${name}: five dimensions required`);
}
function nonempty(value,name){requireValue(typeof value==='string'&&value.trim().length>0,`${name}: nonempty string required`);}
function uniqueIndex(rows,name){
 requireValue(Array.isArray(rows),`${name}: rows array required`);
 const result=new Map();
 for(const row of rows){
  requireValue(isObject(row),`${name}: row object required`);nonempty(row.id,`${name}.id`);
  requireValue(!result.has(row.id),`${name}: duplicate ID ${row.id}`);result.set(row.id,row);
 }
 return result;
}
function validateFormalJudgment(row,where){
 exactDimensions(row.labels,`${where}.labels`);exactDimensions(row.dimension_reasons,`${where}.dimension_reasons`);
 for(const d of formalDims){requireValue(row.labels[d]===0||row.labels[d]===1||row.labels[d]===pending,`${where}/${d}: invalid label`);nonempty(row.dimension_reasons[d],`${where}/${d} reason`);}
 for(const field of ['evidence','rationale','material_issue','fairness_subtypes','innovation_subtypes','safety_quality_basis','input_assessment'])requireValue(own(row,field),`${where}: missing ${field}`);
 nonempty(row.evidence,`${where}.evidence`);nonempty(row.rationale,`${where}.rationale`);
 for(const [d,field,allowed] of [
  ['F','fairness_subtypes',['access','affordability','clinical_management','dimension_information']],
  ['I','innovation_subtypes',['attribute','research_support','qualification_advantage']],
 ]){
  const values=row[field];
  requireValue(Array.isArray(values)&&values.every(x=>typeof x==='string'&&allowed.includes(x))&&new Set(values).size===values.length,`${where}: invalid/duplicate ${field}`);
  requireValue((values.length>0)===(row.labels[d]===1),`${where}: ${field} inconsistent with ${d}`);
 }
 const qualityAllowed=row.labels.S===0?['no_quality_basis']:row.labels.S===pending?['undetermined']:['quality_only','quality_and_other','no_quality_basis'];
 requireValue(qualityAllowed.includes(row.safety_quality_basis),`${where}: invalid S quality basis`);
 requireValue(isObject(row.input_assessment),`${where}: assessment object required`);
 requireValue(['sufficient','context_insufficient','text_problem'].includes(row.input_assessment.status),`${where}: invalid assessment status`);
 nonempty(row.input_assessment.basis,`${where}.input_assessment.basis`);
 if(row.input_assessment.status!=='sufficient')requireValue(formalDims.every(d=>row.labels[d]===pending),`${where}: insufficient material must remain wholly pending`);
}

// Splitting retains every Unicode character and line break. It is display-only;
// concatenating blocks recreates the original string, without a length cap loss.
function displayChunks(text,width=65,maxHeight=409,padding=14,maxCharacters=600){
 requireValue(typeof text==='string','Display chunk input must be text');
 const chunks=[];let current='',completedLines=0,lineWidth=0,characters=0;
 for(const character of text){
  let nextCompleted=completedLines,nextWidth=lineWidth;
  if(character==='\n'){nextCompleted+=Math.max(1,Math.ceil(lineWidth/width));nextWidth=0;}
  else nextWidth+=character.charCodeAt(0)>255?1:.52;
  const height=(nextCompleted+Math.max(1,Math.ceil(nextWidth/width)))*15+padding;
  if(current&&(characters>=maxCharacters||height>maxHeight)){
   chunks.push(current);current='';completedLines=0;lineWidth=0;characters=0;
   nextCompleted=character==='\n'?1:0;nextWidth=character==='\n'?0:(character.charCodeAt(0)>255?1:.52);
  }
  current+=character;characters++;completedLines=nextCompleted;lineWidth=nextWidth;
 }
 if(current||chunks.length===0)chunks.push(current);
 requireValue(chunks.join('')===text,'Display chunk reconstruction mismatch');
 for(const chunk of chunks)requireValue(displayLines(chunk,width)*15+padding<=maxHeight,'Chunk needs layout adjustment; no truncation performed');
 return chunks;
}
const pointerEscape=text=>String(text).replaceAll('~','~0').replaceAll('/','~1');
function appendCompleteFields(target,id,value,pointer){
 if(Array.isArray(value)&&value.length){value.forEach((v,i)=>appendCompleteFields(target,id,v,`${pointer}/${i}`));return;}
 if(isObject(value)&&Object.keys(value).length){for(const [key,item] of Object.entries(value))appendCompleteFields(target,id,item,`${pointer}/${pointerEscape(key)}`);return;}
 const type=value===null?'null':Array.isArray(value)?'array':typeof value;
 const body=typeof value==='string'?value:JSON.stringify(value);
 requireValue(typeof body==='string',`Unserializable source field: ${id}/${pointer}`);
 const chunks=displayChunks(body);
 chunks.forEach((chunk,i)=>target.push([id,`${pointer} [${type}]${chunks.length>1?` (${i+1}/${chunks.length})`:''}`,chunk]));
}
const textValue=value=>typeof value==='string'?value:JSON.stringify(value);
function formalMainRow(material,result){
 const reasons=formalDims.map(d=>`${d}：${result.dimension_reasons[d]}`).join('\n')+`\n证据：${result.evidence}\n综合说明：${result.rationale}`;
 const issues=`材料问题：${textValue(result.material_issue)}\n材料核验：${textValue(result.input_assessment)}\nF子类型：${textValue(result.fairness_subtypes)}\nI子类型：${textValue(result.innovation_subtypes)}\nS质量依据：${result.safety_quality_basis}`;
 return[material.id,material.text,...formalDims.map(d=>result.labels[d]),reasons,issues];
}
function checkedHeight(cells,widths,padding,minimum,where){
 const ht=Math.max(...cells.map((cell,i)=>displayLines(cell,widths[i])))*15+padding;
 requireValue(Number.isFinite(ht)&&ht<=409,`需调整版式，未截断内容：${where}，预计行高 ${ht} > 409`);
 for(const cell of cells)requireValue(typeof cell!=='string'||cell.length<=32767,`需调整分块，未截断内容：${where} exceeds Excel cell text limit`);
 return Math.max(minimum,ht);
}
// Preserve source timestamps literally: the artifact engine otherwise infers
// ISO strings as dates, converts time zones and exports serial numbers.
function matrixValues(rows){return rows.map(row=>row.map(value=>typeof value==='string'&&(value.startsWith('=')||/^\d{4}-\d{2}-\d{2}(?:T|$)/.test(value))?`'${value}`:value));}

// Challenge preparation is separated from authoring so synthetic byte snapshots
// can exercise every content/binding check without filesystem study inputs.
function canonical(value){
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 if(isObject(value))return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
 return JSON.stringify(value);
}
function sameValue(actual,expected,where){requireValue(canonical(actual)===canonical(expected),`${where}: values differ`);}
function hashValue(value,where){requireValue(typeof value==='string'&&/^[0-9a-f]{64}$/.test(value),`${where}: lowercase SHA-256 required`);return value;}
function exactKeys(value,expected,where){requireValue(isObject(value),`${where}: object required`);sameValue(Object.keys(value).sort(),[...expected].sort(),`${where} keys`);}
function challengeArchive(report){
 requireValue(isObject(report)&&isObject(report.archive),'Completed R200 report/archive required');
 const n=report.sample_n,archive=report.archive;
 requireValue(Number.isInteger(n)&&n>=0&&n<=200,'R200 actual n must be an integer in 0..200');
 requireValue(report.status===(n?'completed_challenge_descriptive_ID_join_not_validation_pass':'challenge_no_observations'),'R200 report is not complete');
 for(const key of ['population_inference','population_weights_used','confidence_intervals_computed','reference_generated'])requireValue(report[key]===false,`R200 report ${key} must be false`);
 requireValue(archive.reference_created_by_consensus_or_imputation===false,'R200 archive may not generate a reference');
 const freeze=archive.freeze_manifest_original,seal=archive.release_seal_original,mapping=archive.sampling_manifest_original;
 requireValue(isObject(freeze)&&freeze.status==='frozen_for_reference_label_holdout'&&isObject(freeze.files),'R200 archived final freeze required');
 const version=freeze.protocol_version;nonempty(version,'R200 frozen protocol version');
 const snapshots=archive.input_snapshot_hashes;
 requireValue(isObject(snapshots)&&isObject(snapshots.frozen)&&isObject(snapshots.released)&&isObject(snapshots.submissions),'R200 input snapshot hashes required');
 for(const name of ['freeze','seal','challenge_sampler','postprocessor'])hashValue(snapshots[name],`R200 ${name} hash`);
 exactKeys(snapshots.frozen,Object.keys(freeze.files),'R200 frozen hash inventory');
 requireValue(isObject(archive.filesystem_snapshot_manifest)&&Object.keys(archive.filesystem_snapshot_manifest).length>0,'Finalized R200 filesystem snapshot manifest required');
 for(const [filename,digest] of Object.entries(archive.filesystem_snapshot_manifest)){requireValue(path.isAbsolute(filename),'R200 snapshot path must be absolute');hashValue(digest,filename);}
 for(const [name,entry] of Object.entries(freeze.files)){
  requireValue(isObject(entry)&&typeof entry.path==='string'&&path.isAbsolute(entry.path),`R200 frozen ${name}: absolute path required`);
  hashValue(entry.sha256,`R200 frozen ${name}`);
  requireValue(snapshots.frozen[name]===entry.sha256&&archive.filesystem_snapshot_manifest[entry.path]===entry.sha256,`R200 frozen binding mismatch: ${name}`);
 }
 for(const name of ['protocol','dictionary','dictionary_predictions','R200_plan','holdout_results'])requireValue(own(freeze.files,name),`R200 required frozen binding missing: ${name}`);
 sameValue(archive.registered_R200_rule_binding,freeze.files.R200_plan,'R200 registered rule binding');
 requireValue(isObject(seal)&&seal.n===n&&Number.isInteger(seal.remaining_pool_N)&&seal.remaining_pool_N>=0&&n===Math.min(200,seal.remaining_pool_N),'R200 seal/sample size mismatch');
 requireValue(seal.status===(n?'drawn_challenge_not_representative':'no_remaining_candidates')&&seal.release_status===(n?'ready_for_blind_review':'no_packets_created'),'R200 release state mismatch');
 requireValue(seal.seed===2026092604&&seal.freeze_manifest_sha256===snapshots.freeze&&seal.sampler_sha256===snapshots.challenge_sampler&&seal.machine_parser_sha256===freeze.files.holdout_results.sha256,'R200 seed/freeze/sampler/parser binding mismatch');
 hashValue(seal.H600_results_sha256,'R200 recorded trigger-input hash');
 requireValue(isObject(mapping)&&isObject(mapping.plan),'R200 sampling manifest required');
 for(const key of ['status','n','remaining_pool_N','seed','targets','freeze_manifest_sha256','sampler_sha256','machine_parser_sha256','H600_results_sha256'])requireValue(own(mapping.plan,key),`R200 mapping plan missing ${key}`);
 for(const [key,value] of Object.entries(mapping.plan))sameValue(seal[key],value,`R200 seal/plan ${key}`);
 const mapIndex=uniqueIndex(mapping.rows,'R200 mapping'),ids=Array.from({length:n},(_,i)=>`R200-${String(i+1).padStart(4,'0')}`);
 sameValue([...mapIndex.keys()],ids,'R200 display IDs/order');
 const reviewIds=new Set();
 for(const row of mapping.rows){
  nonempty(row.review_id,'R200 original review ID');requireValue(!reviewIds.has(row.review_id),'Duplicate R200 original review ID');reviewIds.add(row.review_id);
  hashValue(row.unit_text_sha256,`${row.id} source text`);
  requireValue(row.inclusion_probability===null&&!['stratum','N_h','n_h','weight','pi'].some(k=>own(row,k)),'R200 must not borrow survey weights/strata');
 }
 const batches=Math.ceil(n/25),materials=[],results=[],manuals=n?['agent-A/五维共用编码协议.md','agent-C/五维共用编码协议.md']:[];
 for(const coder of ['A','C'])for(let batch=1;batch<=batches;batch++){
  const suffix=String(batch).padStart(2,'0');materials.push(`agent-${coder}/材料-${suffix}.json`);results.push(`agent-${coder}/结果-${suffix}.json`);
 }
 const released=['抽样清单-研究者.json',...manuals,...materials];
 exactKeys(seal.output_files,released,'R200 sealed files');sameValue(snapshots.released,seal.output_files,'R200 released hash snapshot');
 for(const [name,digest] of Object.entries(seal.output_files))hashValue(digest,name);
 exactKeys(archive.packet_manifest,materials,'R200 packet manifest');
 exactKeys(archive.raw_coder_submissions,results,'R200 original independent submissions');
 exactKeys(archive.original_submission_manifest,results,'R200 original submission manifest');
 exactKeys(snapshots.submissions,results,'R200 result hash snapshot');
 requireValue(isObject(archive.input_inventory),'R200 finalized input inventory required');
 sameValue(archive.input_inventory.materials,[...materials].sort(),'R200 material inventory');sameValue(archive.input_inventory.results,[...results].sort(),'R200 result inventory');
 const normalized=uniqueIndex(archive.normalized_rows_without_generated_reference,'R200 normalized archive');
 sameValue([...normalized.keys()],ids,'R200 normalized IDs/order');
 for(const row of normalized.values()){
  requireValue(row.review_id===mapIndex.get(row.id).review_id&&!own(row,'reference')&&!own(row,'consensus'),'R200 normalized mapping/reference mismatch');
  for(const coder of ['A','C','dictionary']){
   exactDimensions(row[coder],`${row.id}/${coder}`);
   for(const d of formalDims)requireValue([0,1,pending].includes(row[coder][d]),`${row.id}/${coder}/${d}: invalid archived label`);
  }
 }
 return{n,archive,freeze,seal,mapping,mapIndex,ids,normalized,version,batches,materials,results,manuals,released};
}
function assembleChallengeInputs(report,releasedBytes,resultBytes,sealBytes){
 const head=challengeArchive(report),{n,archive,freeze,seal,mapping,mapIndex,ids,normalized,version,batches,materials,results,released}=head;
 exactKeys(releasedBytes,released,'R200 actual released bytes');exactKeys(resultBytes,results,'R200 actual result bytes');
 requireValue(sha(sealBytes)===archive.input_snapshot_hashes.seal,'R200 actual release seal hash changed');
 sameValue(JSON.parse(sealBytes.toString('utf8')),seal,'R200 actual release seal');
 for(const [name,bytes] of Object.entries(releasedBytes))requireValue(Buffer.isBuffer(bytes)&&sha(bytes)===seal.output_files[name],`R200 released file hash changed: ${name}`);
 sameValue(JSON.parse(releasedBytes['抽样清单-研究者.json'].toString('utf8')),mapping,'R200 actual sampling manifest');
 const bundles=[];
 for(const coder of (n?['A','C']:[])){
  const protocolBytes=releasedBytes[`agent-${coder}/五维共用编码协议.md`];
  requireValue(sha(protocolBytes)===freeze.files.protocol.sha256&&protocolBytes.equals(releasedBytes['agent-A/五维共用编码协议.md']),'R200 actual protocol differs from frozen/shared manual');
  const allMaterials=[],allResults=[],contextRows=[],submissions=[],packetHashes=[];
  for(let batch=1;batch<=batches;batch++){
   const suffix=String(batch).padStart(2,'0'),pn=`agent-${coder}/材料-${suffix}.json`,rn=`agent-${coder}/结果-${suffix}.json`;
   const bytes=releasedBytes[pn],packetSha=sha(bytes),packet=JSON.parse(bytes.toString('utf8')),packetRecord=archive.packet_manifest[pn];
   requireValue(bytes.equals(releasedBytes[`agent-A/材料-${suffix}.json`]),'A/C actual R200 packet bytes differ');
   requireValue(packet.protocol_version===version&&packet.purpose==='challenge_AI_independent_not_representative'&&packet.batch===batch&&packet.total_batches===batches,`${pn}: version/purpose/batch mismatch`);
   const materialIndex=uniqueIndex(packet.rows,pn),expected=ids.slice((batch-1)*25,batch*25);
   sameValue([...materialIndex.keys()],expected,`${pn} ordered IDs`);
   requireValue(isObject(packetRecord)&&packetRecord.sha256===packetSha&&packetRecord.batch===batch,`${pn}: packet archive binding mismatch`);
   sameValue(packetRecord.ids,expected,`${pn}: packet archive IDs`);exactKeys(packetRecord.unit_text_sha256,expected,`${pn}: packet text hashes`);
   for(const row of packet.rows){
    requireValue(typeof row.text==='string'&&isObject(row.contexts)&&isObject(row.input_assessment),`${pn}/${row.id}: complete material fields required`);
    const digest=sha(Buffer.from(row.text,'utf8'));
    requireValue(digest===mapIndex.get(row.id).unit_text_sha256&&digest===packetRecord.unit_text_sha256[row.id],`${pn}/${row.id}: source text hash mismatch`);
   }
   const submission=archive.raw_coder_submissions[rn],record=archive.original_submission_manifest[rn],actualBytes=resultBytes[rn];
   requireValue(Buffer.isBuffer(actualBytes)&&isObject(record),`${rn}: original result bytes/manifest required`);
   const resultSha=sha(actualBytes);
   requireValue(resultSha===record.sha256&&resultSha===archive.input_snapshot_hashes.submissions[rn],`${rn}: original result hash changed`);
   sameValue(JSON.parse(actualBytes.toString('utf8')),submission,`${rn}: actual result/archive`);
   requireValue(isObject(submission)&&submission.coder===coder&&submission.protocol_version===version&&submission.protocol_acknowledged===true&&submission.input_packet_sha256===packetSha,`${rn}: coder/protocol/packet mismatch`);
   requireValue(record.coder===coder&&record.input_packet_sha256===packetSha,`${rn}: submission manifest binding mismatch`);
   for(const [key,value] of [['batch',batch],['total_batches',batches]])if(own(submission,key))requireValue(submission[key]===value,`${rn}: ${key} mismatch`);
   requireValue((typeof submission.identity==='string'&&submission.identity.trim())||(isObject(submission.identity)&&Object.keys(submission.identity).length),`${rn}: explicit identity required`);
   nonempty(submission.completed_at,`${rn}.completed_at`);requireValue(/[T ]\d{2}:\d{2}/.test(submission.completed_at)&&Number.isFinite(Date.parse(submission.completed_at)),`${rn}: ISO timestamp with time required`);
   requireValue(own(submission,'rule_questions'),`${rn}: rule questions metadata missing`);
   const resultIndex=uniqueIndex(submission.rows,rn);
   sameValue([...resultIndex.keys()].sort(),[...expected].sort(),`${rn}: complete batch ID set`);sameValue(record.ids,[...resultIndex.keys()],`${rn}: archived submission ID order`);
   for(const row of submission.rows){validateFormalJudgment(row,`${rn}/${row.id}`);sameValue(row.labels,normalized.get(row.id)[coder],`${rn}/${row.id}: normalized/original labels`);}
   allMaterials.push(...packet.rows);allResults.push(...submission.rows);packetHashes.push(packetSha);
   const {rows:packetRows,...packetMetadata}=packet;const {rows:resultRows,...submissionMetadata}=submission;
   appendCompleteFields(contextRows,`批次${suffix}`,{file:pn,sha256:packetSha,metadata:packetMetadata},'材料批次');
   appendCompleteFields(contextRows,`批次${suffix}`,{file:rn,sha256:resultSha,metadata:submissionMetadata},'独立提交批次');
   for(const row of packet.rows){appendCompleteFields(contextRows,row.id,row,'材料');appendCompleteFields(contextRows,row.id,resultIndex.get(row.id),'原始独立提交');}
   submissions.push({batch,file:rn,sha256:resultSha,completed_at:submission.completed_at,input_packet_sha256:packetSha});
  }
  const materialIndex=uniqueIndex(allMaterials,`${coder} R200 all materials`),resultIndex=uniqueIndex(allResults,`${coder} R200 all results`);
  sameValue([...materialIndex.keys()],ids,`${coder} R200 complete material set`);sameValue([...resultIndex.keys()].sort(),[...ids].sort(),`${coder} R200 complete original submission set`);
  const rows=allMaterials.map(row=>formalMainRow(row,resultIndex.get(row.id)));
  const rowHeights=rows.map((row,i)=>checkedHeight([row[1],row[7],row[8]],[31,46,18],14,78,`${coder}/挑战独立盲评/${row[0]}/row ${i+5}`));
  const contextHeights=contextRows.map((row,i)=>checkedHeight(row,[10,28,65],14,38,`${coder}/挑战原文语境/row ${i+5}`));
  const manualRows=displayChunks(protocolBytes.toString('utf8'),90,409,12,1200);
  const manualHeights=manualRows.map((text,i)=>checkedHeight([text],[90],12,27,`${coder}/挑战共同手册/row ${i+4}`));
  requireValue(contextRows.length+4<=1048576&&manualRows.length+3<=1048576,'Challenge worksheet row limit exceeded; redesign required');
  bundles.push({coder,version,protocolSha:freeze.files.protocol.sha256,rows,rowHeights,contextRows,contextHeights,manualRows,manualHeights,submissions,packetHashes});
 }
 return{bundles,sampleN:n,batches,sealSha:archive.input_snapshot_hashes.seal,freezeSha:archive.input_snapshot_hashes.freeze};
}
async function loadChallengeInputs(){
 const root=options.challengeRoot,tracked=new Map(),inventories=new Map();
 const read=async file=>{const bytes=await fs.readFile(file),digest=sha(bytes);requireValue(!tracked.has(file)||tracked.get(file)===digest,`Input changed while reading: ${file}`);tracked.set(file,digest);return bytes;};
 const reportBytes=await read(options.challenge),report=JSON.parse(reportBytes.toString('utf8')),head=challengeArchive(report);
 const rootReal=await fs.realpath(root);
 const readInside=async relative=>{const file=path.join(root,relative),resolved=await fs.realpath(file);requireValue(resolved.startsWith(rootReal+path.sep),`R200 input escapes root: ${relative}`);return read(file);};
 const sealBytes=await readInside('封存信息.json'),released={},results={};
 for(const relative of head.released)released[relative]=await readInside(relative);
 for(const relative of head.results)results[relative]=await readInside(relative);
 // Both independent coders must be complete even when only one output is requested.
 const directories=(await fs.readdir(root,{withFileTypes:true})).filter(x=>x.name.startsWith('agent-'));
 const actualMaterials=[],actualResults=[];
 for(const entry of directories){
  requireValue(entry.isDirectory(),'R200 agent folders must be directories');const folder=path.join(root,entry.name),files=await fs.readdir(folder);
  const inventory={materials:files.filter(x=>/^材料-.*\.json$/.test(x)).sort(),results:files.filter(x=>/^结果-.*\.json$/.test(x)).sort()};
  inventories.set(folder,inventory);actualMaterials.push(...inventory.materials.map(name=>`${entry.name}/${name}`));actualResults.push(...inventory.results.map(name=>`${entry.name}/${name}`));
 }
 sameValue(actualMaterials.sort(),[...head.materials].sort(),'R200 actual full material inventory');sameValue(actualResults.sort(),[...head.results].sort(),'R200 actual full result inventory');
 const snapshot=assembleChallengeInputs(report,released,results,sealBytes);
 return{...snapshot,bundles:snapshot.bundles.filter(b=>coders.includes(b.coder)),tracked,inventories,reportSha:sha(reportBytes),reportPath:options.challenge,challengeRoot:root};
}

async function loadFormalInputs(){
 const root=path.join(dir,'H600');
 const tracked=new Map();
 const read=async file=>{const bytes=await fs.readFile(file);tracked.set(file,sha(bytes));return bytes;};
 const sealPath=path.join(root,'封存信息.json');
 const seal=JSON.parse((await read(sealPath)).toString('utf8'));
 requireValue(seal.release_status==='ready_for_blind_review'&&seal.n===600&&isObject(seal.output_files),'Formal H600 release seal required');
 const freezePath=path.join(dir,'最终冻结清单.json');
 const freezeBytes=await read(freezePath);const freeze=JSON.parse(freezeBytes.toString('utf8'));
 requireValue(sha(freezeBytes)===seal.freeze_manifest_sha256&&freeze.status==='frozen_for_reference_label_holdout','Frozen manifest/release mismatch');
 const version=freeze.protocol_version;nonempty(version,'Frozen protocol version');
 const frozenProtocolSha=freeze.files?.protocol?.sha256;nonempty(frozenProtocolSha,'Frozen protocol SHA-256');
 const readReleased=async relative=>{
  requireValue(typeof seal.output_files[relative]==='string',`Missing released file hash: ${relative}`);
  const bytes=await read(path.join(root,relative));requireValue(sha(bytes)===seal.output_files[relative],`Released file changed: ${relative}`);return bytes;
 };
 const bundles=[];const inventories=new Map();
 let sharedPackets=null,sharedProtocol=null;
 for(const coder of coders){
  const agentDir=path.join(root,`agent-${coder}`);
  const files=await fs.readdir(agentDir);
  const actualMaterial=files.filter(x=>/^材料-.*\.json$/.test(x)).sort();
  const actualResults=files.filter(x=>/^结果-.*\.json$/.test(x)).sort();
  const expectedMaterial=Array.from({length:24},(_,i)=>`材料-${String(i+1).padStart(2,'0')}.json`);
  const expectedResults=Array.from({length:24},(_,i)=>`结果-${String(i+1).padStart(2,'0')}.json`);
  requireValue(JSON.stringify(actualMaterial)===JSON.stringify(expectedMaterial)&&JSON.stringify(actualResults)===JSON.stringify(expectedResults),`${coder}: all and only 24 material/result batches are required`);
  inventories.set(agentDir,{materials:actualMaterial,results:actualResults});
  const protocolBytes=await readReleased(`agent-${coder}/五维共用编码协议.md`);
  requireValue(sha(protocolBytes)===frozenProtocolSha,`${coder}: frozen protocol hash mismatch`);
  if(sharedProtocol!==null)requireValue(sharedProtocol.equals(protocolBytes),'A/C protocols differ');else sharedProtocol=protocolBytes;
  const allMaterials=[],allResults=[],contextRows=[],submissions=[],packetHashes=[];
  for(let batch=1;batch<=24;batch++){
   const suffix=String(batch).padStart(2,'0'),materialName=`agent-${coder}/材料-${suffix}.json`,resultName=`agent-${coder}/结果-${suffix}.json`;
   const materialBytes=await readReleased(materialName),packetSha=sha(materialBytes);
   const material=JSON.parse(materialBytes.toString('utf8'));
   requireValue(material.protocol_version===version&&material.batch===batch&&material.total_batches===24&&material.purpose==='reference_label_holdout_AI_independent',`${materialName}: version/batch mismatch`);
   const materialIndex=uniqueIndex(material.rows,materialName);requireValue(materialIndex.size===25,`${materialName}: 25 records required`);
   for(const row of material.rows){requireValue(typeof row.text==='string',`${materialName}/${row.id}: complete text required`);requireValue(isObject(row.contexts)&&isObject(row.input_assessment),`${materialName}/${row.id}: context/assessment required`);}
   const resultBytes=await read(path.join(root,resultName));const result=JSON.parse(resultBytes.toString('utf8'));
   requireValue(result.coder===coder&&result.protocol_version===version&&result.protocol_acknowledged===true&&result.input_packet_sha256===packetSha,`${resultName}: coder/protocol/packet hash mismatch`);
   if(own(result,'batch'))requireValue(result.batch===batch,`${resultName}: crossed batch`);
   if(own(result,'total_batches'))requireValue(result.total_batches===24,`${resultName}: wrong batch total`);
   nonempty(result.completed_at,`${resultName}.completed_at`);requireValue(own(result,'identity')&&own(result,'rule_questions'),`${resultName}: submission metadata missing`);
   const resultIndex=uniqueIndex(result.rows,resultName);
   requireValue(resultIndex.size===25&&[...resultIndex.keys()].every(id=>materialIndex.has(id)),`${resultName}: missing/extra/crossed IDs`);
   for(const row of result.rows)validateFormalJudgment(row,`${resultName}/${row.id}`);
   allMaterials.push(...material.rows);allResults.push(...result.rows);packetHashes.push(packetSha);
   const {rows:materialRows,...materialMetadata}=material;const {rows:resultRows,...resultMetadata}=result;
   const batchId=`批次${suffix}`;
   appendCompleteFields(contextRows,batchId,{file:materialName,sha256:packetSha,metadata:materialMetadata},'材料批次');
   appendCompleteFields(contextRows,batchId,{file:resultName,sha256:sha(resultBytes),metadata:resultMetadata},'独立提交批次');
   for(const row of material.rows){
    // Recursion includes verified_supplemental_context/contexts, content_role,
    // content_role_basis, source pages and every other present nested field.
    appendCompleteFields(contextRows,row.id,row,'材料');
    appendCompleteFields(contextRows,row.id,resultIndex.get(row.id),'原始独立提交');
   }
   submissions.push({batch,file:resultName,sha256:sha(resultBytes),completed_at:result.completed_at,input_packet_sha256:packetSha});
  }
  const materialIndex=uniqueIndex(allMaterials,`${coder} all materials`),resultIndex=uniqueIndex(allResults,`${coder} all results`);
  requireValue(materialIndex.size===600&&resultIndex.size===600&&[...materialIndex.keys()].every(id=>resultIndex.has(id)),`${coder}: exactly 600 unique matching IDs required`);
  if(sharedPackets!==null)requireValue(JSON.stringify(sharedPackets)===JSON.stringify(packetHashes),'A/C packet bytes/order differ');else sharedPackets=packetHashes;
  const rows=allMaterials.map(row=>formalMainRow(row,resultIndex.get(row.id)));
  const rowHeights=rows.map((row,i)=>checkedHeight([row[1],row[7],row[8]],[31,46,18],14,78,`${coder}/独立盲评/${row[0]}/row ${i+5}`));
  const contextHeights=contextRows.map((row,i)=>checkedHeight(row,[10,28,65],14,38,`${coder}/原文语境/row ${i+5}`));
  const protocol=protocolBytes.toString('utf8');const manualRows=displayChunks(protocol,90,409,12,1200);
  const manualHeights=manualRows.map((text,i)=>checkedHeight([text],[90],12,27,`${coder}/共同手册/row ${i+4}`));
  requireValue(contextRows.length+4<=1048576&&manualRows.length+3<=1048576,'Worksheet row limit exceeded; redesign required');
  bundles.push({coder,version,protocolSha:frozenProtocolSha,rows,rowHeights,contextRows,contextHeights,manualRows,manualHeights,submissions,packetHashes});
 }
 return{bundles,tracked,inventories,sealSha:tracked.get(sealPath),freezeSha:sha(freezeBytes)};
}
async function verifyFormalSnapshot(snapshot){
 for(const [file,digest] of snapshot.tracked)requireValue(sha(await fs.readFile(file))===digest,`Input changed during workbook preparation: ${file}`);
 for(const [directory,inventory] of snapshot.inventories){
  const files=await fs.readdir(directory);
  requireValue(JSON.stringify(files.filter(x=>/^材料-.*\.json$/.test(x)).sort())===JSON.stringify(inventory.materials)&&JSON.stringify(files.filter(x=>/^结果-.*\.json$/.test(x)).sort())===JSON.stringify(inventory.results),`Batch inventory changed: ${directory}`);
 }
}
function formalBase(sheet,range){sheet.showGridLines=false;sheet.getRange(range).format.font={name:'Arial',size:11,color:formalColor.text};sheet.getRange(range).format.wrapText=true;sheet.getRange(range).format.verticalAlignment='top';}
function formalTitle(sheet,last,name,note){sheet.mergeCells(`A1:${last}1`);sheet.getRange('A1').values=[[name]];sheet.getRange(`A1:${last}1`).format={fill:formalColor.navy,font:{name:'Arial',size:17,bold:true,color:'#FFFFFF'},rowHeight:36};sheet.mergeCells(`A2:${last}2`);sheet.getRange('A2').values=[[note]];sheet.getRange(`A2:${last}2`).format.rowHeight=48;}
function formalHeader(sheet,range){sheet.getRange(range).format={fill:formalColor.teal,font:{bold:true,color:'#FFFFFF'},rowHeight:32};}
async function saveNewWorkbook(workbook,destination){
 const partial=`${destination}.partial`;
 const reservation=await fs.open(partial,'wx');await reservation.close();
 const output=await SpreadsheetFile.exportXlsx(workbook);await output.save(partial);
 await fs.link(partial,destination);await fs.unlink(partial); // link refuses an existing destination atomically.
}
async function renderReviewed(snapshot,challengeMode=false){
 // Every required coder is validated and laid out before Workbook.create().
 const mode=challengeMode?'challenge200':'formal600',batches=challengeMode?snapshot.batches:24;
 for(const bundle of snapshot.bundles){
  const {coder,rows,rowHeights,contextRows,contextHeights,manualRows,manualHeights}=bundle;
  const paths=challengeMode?challengeFilePaths(coder):filePaths(coder),last=rows.length+4,contextLast=contextRows.length+4,manualLast=manualRows.length+3;
  const tableSuffix=challengeMode?`Challenge200${coder}`:`Formal600${coder}`;
  const w=Workbook.create(),s=w.worksheets.add('独立盲评'),c=w.worksheets.add('原文语境'),m=w.worksheets.add('共同手册');
  formalBase(s,`A1:I${last}`);formalTitle(s,'I',challengeMode?`补充挑战集：实际 ${rows.length} 条独立盲评 AI评审 ${coder}`:`正式600条独立盲评 AI评审 ${coder}`,challengeMode?`${bundle.version}\n定向挑战集，实际 n=${rows.length}；仅描述本集合。1=涉及，0=不涉及，待定保留。首次独立提交。`:`${bundle.version}\n参考标签留出。1=涉及，0=不涉及，待定=尚无充分判定依据。保留首次独立提交。`);
  s.getRange('A4:I4').values=[['编号','完整分析单元','S安全','E有效','Ec经济','I创新','F公平','逐维判定依据与证据','材料问题及子类型/质量依据']];formalHeader(s,'A4:I4');s.getRange(`A5:I${last}`).values=matrixValues(rows);
  s.getRange('A:A').format.columnWidth=16;s.getRange('B:B').format.columnWidth=56;s.getRange('C:G').format.columnWidth=9;s.getRange('H:H').format.columnWidth=80;s.getRange('I:I').format.columnWidth=32;
  s.getRange(`C5:G${last}`).format.horizontalAlignment='center';s.getRange(`C5:G${last}`).format.font={bold:true,size:12};
  s.getRange(`C5:G${last}`).dataValidation={rule:{type:'list',values:['0','1','待定']}};
  s.getRange(`C5:G${last}`).conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:formalColor.pale,font:{color:'#155B42',bold:true}}});
  s.getRange(`C5:G${last}`).conditionalFormats.add('containsText',{text:'待定',format:{fill:formalColor.amber,font:{color:'#754D00'}}});
  rows.forEach((row,i)=>{s.getRange(`A${i+5}:I${i+5}`).format.rowHeight=rowHeights[i];if(i%2===1){s.getRange(`A${i+5}:B${i+5}`).format.fill='#F5F8FA';s.getRange(`H${i+5}:I${i+5}`).format.fill='#F5F8FA';}});
  s.freezePanes.freezeRows(4);s.freezePanes.freezeColumns(2);s.tables.add(`A4:I${last}`,true,`Blind${tableSuffix}`);
  formalBase(c,`A1:C${contextLast}`);formalTitle(c,'C',challengeMode?`补充挑战原文、语境与独立提交：实际 ${rows.length} 条`:'正式留出原文、语境与独立提交',challengeMode?`Source：R200/agent-${coder} 材料/结果，共 ${batches} 批，实际 n=${rows.length}\n按字段路径保留全部原文及核验元数据。续块按序拼接；材料与原始提交均不改写。`:`Source：H600/agent-${coder} 材料/结果01–24批\n按字段路径保留全部内容及核验元数据。续块按序拼接；材料与原始提交均不改写。`);
  c.getRange('A4:C4').values=[['编号/批次','原字段路径、类型与分块序号','完整文本、来源及核验元数据']];formalHeader(c,'A4:C4');c.getRange(`A5:C${contextLast}`).values=matrixValues(contextRows);
  c.getRange('A:A').format.columnWidth=16;c.getRange('B:B').format.columnWidth=50;c.getRange('C:C').format.columnWidth=116;
  contextRows.forEach((row,i)=>{c.getRange(`A${i+5}:C${i+5}`).format.rowHeight=contextHeights[i];});c.freezePanes.freezeRows(4);c.tables.add(`A4:C${contextLast}`,true,`Contexts${tableSuffix}`);
  formalBase(m,`A1:A${manualLast}`);m.getRange('A:A').format.columnWidth=160;
  m.getRange('A1').values=[[challengeMode?`挑战集共同编码手册与执行协议：实际 ${rows.length} 条`:'共同编码手册与执行协议']];m.getRange('A1').format={fill:formalColor.navy,font:{size:17,bold:true,color:'#FFFFFF'},rowHeight:36};
  m.getRange('A2').values=[[`Source：五维共用编码协议.md。SHA-256：${bundle.protocolSha}\n按原顺序分块保留完整协议。执行者为AI，未将其改称真人专家。`]];m.getRange('A2').format.rowHeight=48;
  m.getRange(`A4:A${manualLast}`).values=matrixValues(manualRows.map(text=>[text]));manualRows.forEach((text,i)=>{m.getRange(`A${i+4}`).format.rowHeight=manualHeights[i];});m.freezePanes.freezeRows(2);
  w.recalculate();
  const inspectionRanges=[['独立盲评',`A4:I${Math.min(7,last)}`],['独立盲评',`A${Math.max(4,last-2)}:I${last}`],['原文语境',`A4:C7`],['原文语境',`A${Math.max(4,contextLast-2)}:C${contextLast}`],['共同手册',`A1:A${Math.min(7,manualLast)}`]];
  const inspections=[];for(const [sheetName,range] of inspectionRanges){const view=await w.inspect({kind:'table',range:`${sheetName}!${range}`,include:'values,formulas',tableMaxRows:7,tableMaxCols:9,maxChars:2200});inspections.push(view.ndjson);}
  const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:challengeMode?'Challenge workbook formula error scan':'Formal workbook formula error scan',maxChars:1600});
  const previewRanges=[['labels','独立盲评',`A1:I${Math.min(7,last)}`],['reasons','独立盲评',`H4:I${Math.min(7,last)}`],['end','独立盲评',`A${Math.max(4,last-2)}:I${last}`],['contexts','原文语境','A1:C7'],['contexts-end','原文语境',`A${Math.max(4,contextLast-2)}:C${contextLast}`],['manual','共同手册',`A1:A${Math.min(6,manualLast)}`]];
  const previewBytes=[];for(const [name,sheetName,range] of previewRanges){const image=await w.render({sheetName,range,scale:1,format:'png'});previewBytes.push([paths[name],new Uint8Array(await image.arrayBuffer())]);}
  await verifyFormalSnapshot(snapshot);
  for(const file of Object.values(paths))await assertNew(file);await assertNew(`${paths.workbook}.partial`);
  await fs.writeFile(paths.inspection,inspections.join('\n'),{flag:'wx'});await fs.writeFile(paths.errors,errors.ndjson,{flag:'wx'});
  await fs.writeFile(paths.checks,JSON.stringify({mode,coder,records:rows.length,batches,protocol_version:bundle.version,protocol_sha256:bundle.protocolSha,freeze_sha256:snapshot.freezeSha,release_seal_sha256:snapshot.sealSha,packet_sha256:bundle.packetHashes,submissions:bundle.submissions,contextRows:contextRows.length,manualBlocks:manualRows.length,maxMainRowHeight:rowHeights.reduce((a,b)=>Math.max(a,b),0),maxContextRowHeight:contextHeights.reduce((a,b)=>Math.max(a,b),0),...(challengeMode?{challenge_report_sha256:snapshot.reportSha,challenge_report_path:snapshot.reportPath,challenge_root:snapshot.challengeRoot,population_inference:false,population_weights_used:false,confidence_intervals_computed:false,original_submissions_preserved:true}:{}),no_truncation:true,no_label_defaults:true,visual_review_status:'renders_written_requires_human_or_agent_visual_review'},null,2),{flag:'wx'});
  for(const [file,bytes] of previewBytes)await fs.writeFile(file,bytes,{flag:'wx'});
  await saveNewWorkbook(w,paths.workbook);
  console.log(JSON.stringify({mode,coder,output:paths.workbook,records:rows.length,contextRows:contextRows.length,manualBlocks:manualRows.length}));
 }
}

// All fixtures below are invented text/labels and exist only in memory.
function syntheticChallenge(n=26){
 const encode=value=>Buffer.from(JSON.stringify(value),'utf8');
 const manual=Buffer.from(('Synthetic common protocol.\n中文手册\n').repeat(55),'utf8');
 const files=Object.fromEntries(['protocol','dictionary','dictionary_predictions','R200_plan','holdout_results'].map(name=>[name,{path:`/synthetic/${name}`,sha256:name==='protocol'?sha(manual):sha(Buffer.from(name))}]));
 const freeze={status:'frozen_for_reference_label_holdout',protocol_version:'synthetic-v1',files};
 const samplerSha=sha(Buffer.from('synthetic sampler')),plan={status:n?'drawn_challenge_not_representative':'no_remaining_candidates',n,remaining_pool_N:n,seed:2026092604,targets:['S'],freeze_manifest_sha256:sha(encode(freeze)),sampler_sha256:samplerSha,machine_parser_sha256:files.holdout_results.sha256,H600_results_sha256:sha(Buffer.from('synthetic trigger only'))};
 const texts=Array.from({length:n},(_,i)=>`Synthetic unit ${i+1}. 合成原文。`);
 const mapping={plan,rows:texts.map((text,i)=>({id:`R200-${String(i+1).padStart(4,'0')}`,review_id:`synthetic-${i+1}`,unit_text_sha256:sha(Buffer.from(text)),inclusion_probability:null}))};
 const released={'抽样清单-研究者.json':encode(mapping)},results={},raw={},packets={},submissions={},normalized=mapping.rows.map(r=>({id:r.id,review_id:r.review_id,dictionary:Object.fromEntries(formalDims.map(d=>[d,0]))}));
 const batches=Math.ceil(n/25),longContext=('合成上下文😀\n').repeat(150);
 for(const coder of (n?['A','C']:[])){
  released[`agent-${coder}/五维共用编码协议.md`]=manual;
  for(let batch=1;batch<=batches;batch++){
   const suffix=String(batch).padStart(2,'0'),pn=`agent-${coder}/材料-${suffix}.json`,rn=`agent-${coder}/结果-${suffix}.json`;
   const rows=mapping.rows.slice((batch-1)*25,batch*25).map((r,j)=>({id:r.id,text:texts[(batch-1)*25+j],source_title:'Synthetic title',pages:[1,2],contexts:{verified_supplemental_context:{contexts:[{text:longContext,pages:[2],verified:true}],content_role:'context',content_role_basis:'synthetic verified basis'}},input_assessment:{status:'sufficient',basis:'synthetic input'},context_usage:{note:'Synthetic only'}}));
   const packet={protocol_version:freeze.protocol_version,purpose:'challenge_AI_independent_not_representative',batch,total_batches:batches,rows};
   released[pn]=encode(packet);const packetSha=sha(released[pn]);
   packets[pn]={sha256:packetSha,batch,ids:rows.map(r=>r.id),unit_text_sha256:Object.fromEntries(rows.map(r=>[r.id,sha(Buffer.from(r.text))]))};
   const resultRows=rows.map((r,j)=>{
    const index=(batch-1)*25+j,labels=Object.fromEntries(formalDims.map(d=>[d,index===0?1:index===1?pending:index===2&&d==='S'?pending:0]));
    normalized[index][coder]={...labels};
    return{id:r.id,labels,dimension_reasons:Object.fromEntries(formalDims.map(d=>[d,'Synthetic reason.'])),evidence:'Synthetic evidence.',rationale:'Synthetic rationale.',material_issue:index===1?'synthetic context issue':'none',fairness_subtypes:labels.F===1?['access']:[],innovation_subtypes:labels.I===1?['attribute']:[],safety_quality_basis:labels.S===pending?'undetermined':labels.S===1?'quality_only':'no_quality_basis',input_assessment:{status:index===1?'context_insufficient':'sufficient',basis:'Synthetic assessment basis.'}};
   });
   const submission={coder,identity:{kind:'synthetic AI'},protocol_version:freeze.protocol_version,protocol_acknowledged:true,completed_at:'2026-09-26T00:00:00Z',input_packet_sha256:packetSha,batch,total_batches:batches,rows:resultRows,rule_questions:[]};
   results[rn]=encode(submission);raw[rn]=submission;submissions[rn]={sha256:sha(results[rn]),coder,input_packet_sha256:packetSha,ids:resultRows.map(r=>r.id)};
  }
 }
 const seal={...plan,release_status:n?'ready_for_blind_review':'no_packets_created',output_files:Object.fromEntries(Object.entries(released).map(([name,bytes])=>[name,sha(bytes)]))},sealBytes=encode(seal);
 const report={status:n?'completed_challenge_descriptive_ID_join_not_validation_pass':'challenge_no_observations',sample_n:n,population_inference:false,population_weights_used:false,confidence_intervals_computed:false,reference_generated:false,archive:{freeze_manifest_original:freeze,release_seal_original:seal,sampling_manifest_original:mapping,raw_coder_submissions:raw,packet_manifest:packets,original_submission_manifest:submissions,normalized_rows_without_generated_reference:normalized,input_snapshot_hashes:{freeze:plan.freeze_manifest_sha256,seal:sha(sealBytes),challenge_sampler:samplerSha,postprocessor:sha(Buffer.from('synthetic postprocessor')),frozen:Object.fromEntries(Object.entries(files).map(([key,entry])=>[key,entry.sha256])),released:{...seal.output_files},submissions:Object.fromEntries(Object.entries(submissions).map(([key,entry])=>[key,entry.sha256]))},registered_R200_rule_binding:files.R200_plan,reference_created_by_consensus_or_imputation:false,filesystem_snapshot_manifest:Object.fromEntries(Object.values(files).map(entry=>[entry.path,entry.sha256])),input_inventory:{materials:Object.keys(packets).sort(),results:Object.keys(results).sort()}}};
 return{report,released,results,sealBytes,longContext,manual};
}
function challengeSelfTest(){
 let checks=0,rejections=0;
 const run=fixture=>assembleChallengeInputs(fixture.report,fixture.released,fixture.results,fixture.sealBytes);
 const test=(condition,message)=>{requireValue(condition,`Synthetic QA: ${message}`);checks++;};
 const reject=(name,mutation,needle)=>{
  const fixture=syntheticChallenge();mutation(fixture);
  let caught;try{run(fixture);}catch(error){caught=error;}
  test(Boolean(caught)&&(!needle||String(caught.message).includes(needle)),`${name} must reject${needle?' for '+needle:''}; ${caught?.message??'accepted'}`);rejections++;
 };
 const resignResult=(fixture,mutation)=>{
  const name='agent-A/结果-01.json',archive=fixture.report.archive,submission=archive.raw_coder_submissions[name];mutation(submission);
  fixture.results[name]=Buffer.from(JSON.stringify(submission));const digest=sha(fixture.results[name]);archive.original_submission_manifest[name].sha256=digest;archive.input_snapshot_hashes.submissions[name]=digest;
 };
 const fixture=syntheticChallenge(),snapshot=run(fixture);
 test(snapshot.sampleN===26&&snapshot.batches===2&&snapshot.bundles.length===2&&snapshot.bundles.every(b=>b.rows.length===26),'26 observations / two complete coders / 25+1 batches');
 const bundle=snapshot.bundles[0],prefix='材料/contexts/verified_supplemental_context/contexts/0/text [string]';
 test(bundle.contextRows.filter(r=>r[0]==='R200-0001'&&r[1].startsWith(prefix)).map(r=>r[2]).join('')===fixture.longContext,'long nested context reconstructs exactly');
 test(bundle.manualRows.join('')===fixture.manual.toString('utf8')&&Math.max(...bundle.contextHeights,...bundle.manualHeights)<=409,'complete manual/context blocks within row limit');
 test(bundle.rows[1].slice(2,7).every(x=>x===pending)&&bundle.rows[2][2]===pending&&bundle.rows[2][3]===0,'material and concept pending labels are retained');
 test(bundle.rows[0][8].includes('access')&&bundle.rows[0][8].includes('attribute')&&bundle.rows[0][8].includes('quality_only')&&bundle.contextRows.some(r=>r[1].includes('content_role_basis')),'subtypes, quality, metadata retained');
 test(run(syntheticChallenge(1)).bundles.every(b=>b.rows.length===1),'n=1 supported without fixed 200-row ranges');
 const zero=run(syntheticChallenge(0));test(zero.sampleN===0&&zero.bundles.length===0,'n=0 creates no workbook bundle');
 test(run(syntheticChallenge(200)).bundles.every(b=>b.rows.length===200),'n=200 complete eight batches');
 reject('incomplete report',f=>{f.report.status='running';},'not complete');
 reject('missing original submission',f=>{delete f.report.archive.raw_coder_submissions['agent-C/结果-02.json'];},'original independent submissions');
 reject('missing actual batch',f=>{delete f.released['agent-C/材料-02.json'];},'actual released bytes');
 reject('changed actual material',f=>{f.released['agent-A/材料-01.json']=Buffer.from('changed');},'released file hash changed');
 reject('changed result bytes',f=>{f.results['agent-A/结果-01.json']=Buffer.from('{}');},'original result hash changed');
 reject('changed packet binding',f=>resignResult(f,s=>{s.input_packet_sha256='0'.repeat(64);}), 'coder/protocol/packet');
 reject('wrong protocol version',f=>resignResult(f,s=>{s.protocol_version='wrong';}), 'coder/protocol/packet');
 reject('duplicate submission ID',f=>resignResult(f,s=>{s.rows[1].id=s.rows[0].id;}),'duplicate ID');
 reject('crossed batch',f=>resignResult(f,s=>{s.batch=2;}),'batch mismatch');
 reject('missing reason',f=>resignResult(f,s=>{s.rows[0].dimension_reasons.S='';}),'nonempty string');
 reject('boolean label',f=>resignResult(f,s=>{s.rows[0].labels.S=true;}),'invalid label');
 reject('missing subtype',f=>resignResult(f,s=>{s.rows[0].fairness_subtypes=[];}),'inconsistent with F');
 reject('wrong quality flag',f=>resignResult(f,s=>{s.rows[1].safety_quality_basis='no_quality_basis';}),'invalid S quality');
 reject('material pending conflict',f=>resignResult(f,s=>{s.rows[3].input_assessment.status='text_problem';}),'wholly pending');
 reject('normalized archive differs',f=>{f.report.archive.normalized_rows_without_generated_reference[0].A.S=0;},'normalized/original labels');
 reject('frozen rule binding differs',f=>{f.report.archive.registered_R200_rule_binding={path:'/synthetic/other',sha256:'0'.repeat(64)};},'registered rule binding');
 reject('sampler version differs',f=>{f.report.archive.input_snapshot_hashes.challenge_sampler='0'.repeat(64);},'sampler/parser');
 reject('source text hash differs',f=>{f.report.archive.packet_manifest['agent-A/材料-01.json'].unit_text_sha256['R200-0001']='0'.repeat(64);},'source text hash');
 reject('archive-only replacement evidence',f=>{f.report.archive.raw_coder_submissions['agent-A/结果-01.json'].rows[0].evidence='changed';},'actual result/archive');
 reject('excessive main row height',f=>resignResult(f,s=>{s.rows[0].dimension_reasons.S='Long original reason.\n'.repeat(50);}),'需调整版式');
 reject('survey weight claim',f=>{f.report.population_weights_used=true;},'must be false');
 test(canonical(parseOptions(['--formal','C']))===canonical({formal:true,challenge:null,challengeRoot:path.join(dir,'R200'),selfTest:false,coders:['C']}),'formal CLI stays compatible');
 test(parseOptions([]).coders.join(',')==='A,C'&&parseOptions(['--challenge','/synthetic/result.json']).challenge==='/synthetic/result.json','development and challenge CLI routes');
 test(path.basename(formalOutput('A'))==='正式盲评600-A-AI评审.xlsx'&&path.basename(challengeOutput('C'))==='补充挑战200-C-AI评审.xlsx'&&challengeFilePaths('A').checks.endsWith('challenge200-A-input-checks.json'),'output/check paths do not collide');
 console.log(JSON.stringify({status:'passed',mode:'synthetic_only_no_authoring',checks,rejected_counterexamples:rejections,sizes_checked:[0,1,26,200],artifact_library_imported:false,study_files_read:false,files_written:false}));
}

// No mode runs during `node --check build_reviews.mjs`. Self-tests never import
// the artifact library, touch study inputs, create workbooks or write outputs.
if(options.selfTest){
 challengeSelfTest();
}else{
 ({Workbook,SpreadsheetFile}=await import('@oai/artifact-tool'));
 if(options.challenge){
  const snapshot=await loadChallengeInputs();
  if(snapshot.sampleN===0){await verifyFormalSnapshot(snapshot);console.log(JSON.stringify({mode:'challenge200',records:0,status:'no_observations_no_workbooks_created'}));}
  else{
   for(const coder of coders){for(const file of Object.values(challengeFilePaths(coder)))await assertNew(file);await assertNew(`${challengeOutput(coder)}.partial`);}
   await renderReviewed(snapshot,true);
  }
 }else if(formal){
  for(const coder of coders){for(const file of Object.values(filePaths(coder)))await assertNew(file);await assertNew(`${formalOutput(coder)}.partial`);}
  await renderReviewed(await loadFormalInputs());
 }else{
  for(const coder of coders)await assertNew(path.join(dir,`扩充盲评60-${coder}-AI评审.xlsx`));
  await buildDevelopment();
 }
}
