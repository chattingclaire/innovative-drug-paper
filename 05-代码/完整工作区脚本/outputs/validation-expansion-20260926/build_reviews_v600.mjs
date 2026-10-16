/** V600 display export only. Never codes, adjudicates, or recomputes statistics.
 * Actual usage: --results /abs/completed-paired.json --freeze /abs/freeze.json
 *               --holdout /abs/V600 [A|C]
 * Preparation: --self-test [--qa-output /abs/new-QA.json]
 * Both coders must be complete before either workbook can be exported.
 * The caller marks the artifact operation immediately before a real authoring
 * command. Self-test does not import artifact-tool or create a workbook.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const OUTPUT=path.join(HERE,'V600工作簿交付');
const RUNTIME='/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const DIMS=['S','E','Ec','I','F'], PENDING='待定';
const DOCS={protocol:'五维共用编码协议.md',reviewer_instructions:'评审任务说明.md',protocol_clarifications:'共同执行澄清.md'};
const COLOR={navy:'#17384B',teal:'#126B70',text:'#1F2937',pale:'#E8F4EF',amber:'#FFF0C2'};
const sha=value=>createHash('sha256').update(value).digest('hex');
const requireValue=(ok,message)=>{if(!ok)throw Error(message);};
const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const own=(value,key)=>Object.prototype.hasOwnProperty.call(value,key);
const canonical=value=>Array.isArray(value)?'['+value.map(canonical).join(',')+']':object(value)?'{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}':JSON.stringify(value);
const same=(a,b,message)=>requireValue(canonical(a)===canonical(b),message);
const encode=value=>Buffer.from(JSON.stringify(value,null,2)+'\n');
const text=bytes=>new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
function nonempty(value,name){requireValue(typeof value==='string'&&value.trim().length>0,name+': nonempty string required');}
function hash(value,name){requireValue(typeof value==='string'&&/^[0-9a-f]{64}$/.test(value),name+': SHA-256 required');return value;}
function keys(value,expected,name){requireValue(object(value),name+': object required');same(Object.keys(value).sort(),[...expected].sort(),name+': key inventory mismatch');}
function unique(rows,name){requireValue(Array.isArray(rows),name+': rows required');const index=new Map();for(const row of rows){requireValue(object(row),name+': row object required');nonempty(row.id,name+'.id');requireValue(!index.has(row.id),name+': duplicate ID');index.set(row.id,row);}return index;}

// Strict JSON parsing keeps duplicate keys and overflowing numbers from being
// silently accepted. No input values are included in parse errors.
function json(bytes){
 const source=text(bytes);let i=0;
 const ws=()=>{while(/[\t\n\r ]/.test(source[i]??'x'))i++;};
 const string=()=>{const start=i++;while(i<source.length){if(source[i]==='\\'){i+=2;continue;}if(source[i++]==='"')return JSON.parse(source.slice(start,i));}throw Error('Unterminated JSON string');};
 function value(){ws();const c=source[i];
  if(c==='"')return string();
  if(c==='{'||c==='['){const dict=c==='{',out=dict?Object.create(null):[];i++;ws();if(source[i]===(dict?'}':']')){i++;return out;}while(true){let key;if(dict){requireValue(source[i]==='"','JSON object key required');key=string();requireValue(!own(out,key),'Duplicate JSON key');ws();requireValue(source[i++]===':','JSON colon required');}const item=value();if(dict)out[key]=item;else out.push(item);ws();const end=source[i++];if(end===(dict?'}':']'))return out;requireValue(end===',','JSON separator required');ws();}}
  for(const [token,result] of [['true',true],['false',false],['null',null]])if(source.startsWith(token,i)){i+=token.length;return result;}
  const match=source.slice(i).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);requireValue(match,'Invalid JSON value');i+=match[0].length;const number=Number(match[0]);requireValue(Number.isFinite(number)&&(!Number.isInteger(number)||Number.isSafeInteger(number)),'Nonfinite/unsafe JSON number');return number;
 }
 const result=value();ws();requireValue(i===source.length&&object(result),'JSON object/trailing content error');return result;
}

function parseOptions(args){
 const o={coders:[],selfTest:false};const seen=new Set();
 for(let i=0;i<args.length;i++){const a=args[i];if(['--results','--freeze','--holdout','--qa-output'].includes(a)){requireValue(!seen.has(a),'Duplicate option');seen.add(a);const v=args[++i];requireValue(typeof v==='string'&&path.isAbsolute(v),a+' requires an absolute path');o[a.slice(2).replace('qa-output','qaOutput')]=v;}else if(a==='--self-test'){requireValue(!o.selfTest,'Duplicate self-test option');o.selfTest=true;}else if(['A','C'].includes(a))o.coders.push(a);else throw Error('Unknown option');}
 requireValue(o.coders.length<=1,'Choose at most one coder');
 if(o.selfTest)requireValue(!o.results&&!o.freeze&&!o.holdout&&!o.coders.length,'Self-test accepts no study inputs');
 else requireValue(o.results&&o.freeze&&o.holdout&&!o.qaOutput,'Explicit --results --freeze --holdout required');
 if(!o.coders.length)o.coders=['A','C'];return o;
}

function dimensions(value,name){keys(value,DIMS,name);}
function judgment(row){
 dimensions(row.labels,'labels');dimensions(row.dimension_reasons,'dimension_reasons');
 for(const d of DIMS){requireValue(row.labels[d]===0||row.labels[d]===1||row.labels[d]===PENDING,'Invalid original label');nonempty(row.dimension_reasons[d],'dimension reason');}
 for(const name of ['evidence','rationale','material_issue'])nonempty(row[name],name);
 for(const [d,name,allowed] of [['F','fairness_subtypes',['access','affordability','clinical_management','dimension_information']],['I','innovation_subtypes',['attribute','research_support','qualification_advantage']]]){
  const a=row[name];requireValue(Array.isArray(a)&&a.every(x=>allowed.includes(x))&&new Set(a).size===a.length,'Invalid subtype list');requireValue(Boolean(a.length)===(row.labels[d]===1),'Subtype/original label mismatch');
 }
 const quality=row.labels.S===0?['no_quality_basis']:row.labels.S===PENDING?['undetermined']:['quality_only','quality_and_other','no_quality_basis'];requireValue(quality.includes(row.safety_quality_basis),'Quality basis/original label mismatch');
 requireValue(object(row.input_assessment)&&['sufficient','context_insufficient','text_problem'].includes(row.input_assessment.status),'Input assessment required');nonempty(row.input_assessment.basis,'assessment basis');
 if(row.input_assessment.status!=='sufficient')requireValue(DIMS.every(d=>row.labels[d]===PENDING),'Insufficient original submission must remain pending');
}

function archiveHead(report,freezeBytes,sealBytes){
 requireValue(report.status==='completed_frozen_paired_ID_join_not_validation_pass'&&report.phase==='V600','Completed paired V600 report required');
 const archive=report.archive,stats=report.paired_statistics;requireValue(object(archive)&&object(stats)&&stats.reference_generated===false&&archive.reference_created_by_consensus_or_imputation===false,'Original independent archive required');
 const freeze=json(freezeBytes),seal=json(sealBytes),snap=archive.input_snapshot_hashes;
 requireValue(object(snap)&&sha(freezeBytes)===snap.freeze&&sha(sealBytes)===snap.seal,'Actual freeze/seal byte hash mismatch');
 same(freeze,archive.freeze_manifest_original,'Archived/actual freeze differ');same(seal,archive.release_seal_original,'Archived/actual seal differ');
 requireValue(freeze.status==='frozen_for_paired_reference_label_holdout'&&freeze.phase==='V600'&&freeze.sample_budget===600&&freeze.sampling_seed===2026092605&&freeze.bootstrap_seed===2026092606,'Unexpected paired frozen design');
 nonempty(freeze.protocol_version,'protocol version');requireValue(object(freeze.files),'Frozen file manifest required');
 for(const name of ['protocol','reviewer_instructions','protocol_clarifications','results_bridge','legacy_results_helpers','sampler','baseline_predictions','candidate_predictions'])requireValue(own(freeze.files,name),'Missing frozen binding');
 const fileHashes={};for(const [name,entry] of Object.entries(freeze.files)){requireValue(object(entry)&&path.isAbsolute(entry.path),'Absolute frozen source path required');fileHashes[name]=hash(entry.sha256,'frozen file');}
 same(snap.frozen,fileHashes,'Frozen archive hash inventory differs');same(seal.input_hashes,fileHashes,'Seal/freeze hash inventory differs');
 const fsManifest=archive.filesystem_snapshot_manifest;requireValue(object(fsManifest)&&Object.keys(fsManifest).length,'Finalized filesystem snapshot manifest required');
 for(const [name,entry] of Object.entries(freeze.files))requireValue(fsManifest[entry.path]===entry.sha256,'Frozen file is not bound to finalized report');
 const n=seal.n,N=seal.N_star;requireValue(Number.isInteger(n)&&n>0&&Number.isInteger(N)&&N>=n&&n===Math.min(freeze.sample_budget,N),'Complete frozen actual n required');
 requireValue(seal.phase==='V600'&&seal.status==='drawn'&&seal.release_status==='ready_for_blind_review'&&seal.seed===freeze.sampling_seed&&seal.freeze_manifest_sha256===snap.freeze,'Unexpected release seal');
 requireValue(stats.sample_n===n&&stats.population_N===N,'Completed report/sample size mismatch');
 const mapping=archive.sampling_manifest_original;requireValue(object(mapping)&&object(mapping.plan),'Archived mapping required');
 for(const [k,v] of Object.entries(mapping.plan))same(seal[k],v,'Seal/mapping plan mismatch');
 const ids=Array.from({length:n},(_,i)=>`V600-${String(i+1).padStart(4,'0')}`),index=unique(mapping.rows,'mapping');same([...index.keys()],ids,'Complete ordered display IDs required');
 const originalIds=new Set();for(const row of mapping.rows){nonempty(row.review_id,'review ID');requireValue(!originalIds.has(row.review_id),'Duplicate original review ID');originalIds.add(row.review_id);hash(row.unit_text_sha256,'source text');}
 requireValue(archive.frame_validation?.fixed_seed_sample_identities_reproduced_in_memory_only===true,'Completed frame verification missing');
 const batches=Math.ceil(n/25),materials=[],results=[],manuals=[];
 for(const coder of ['A','C']){for(const filename of Object.values(DOCS))manuals.push(`agent-${coder}/${filename}`);for(let b=1;b<=batches;b++){const suffix=String(b).padStart(2,'0');materials.push(`agent-${coder}/材料-${suffix}.json`);results.push(`agent-${coder}/结果-${suffix}.json`);}}
 const released=['抽样清单-研究者.json',...materials,...manuals];keys(seal.output_files,released,'Sealed release');same(snap.released,seal.output_files,'Released archive hash inventory differs');
 for(const [name,digest] of Object.entries(seal.output_files))hash(digest,name);
 keys(archive.raw_coder_submissions,results,'Original submissions');keys(archive.original_submission_manifest,results,'Original submission manifest');keys(snap.submissions,results,'Submission hash inventory');keys(archive.packet_manifest,materials,'Packet manifest');
 same(archive.input_inventory,{materials:[...materials].sort(),results:[...results].sort()},'Finalized batch inventory differs');
 return {archive,freeze,seal,n,N,batches,index,ids,materials,results,released,freezeSha:snap.freeze,sealSha:snap.seal};
}

const lineCount=(s,width)=>String(s).split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil([...line].reduce((t,c)=>t+(c.codePointAt(0)>255?1:.52),0)/width)),0);
function chunks(source,width=65,padding=14,maxCharacters=600){
 requireValue(typeof source==='string','Chunk source must be a string');const output=[];let part='',completed=0,lineWidth=0,count=0;
 for(const c of source){let nextCompleted=completed,nextWidth=lineWidth;if(c==='\n'){nextCompleted+=Math.max(1,Math.ceil(lineWidth/width));nextWidth=0;}else nextWidth+=c.codePointAt(0)>255?1:.52;
  if(part&&(count>=maxCharacters||(nextCompleted+Math.max(1,Math.ceil(nextWidth/width)))*15+padding>409)){output.push(part);part='';completed=0;lineWidth=0;count=0;nextCompleted=c==='\n'?1:0;nextWidth=c==='\n'?0:(c.codePointAt(0)>255?1:.52);}
  part+=c;count++;completed=nextCompleted;lineWidth=nextWidth;
 }if(part||!output.length)output.push(part);requireValue(output.join('')===source,'Character reconstruction failed');for(const part of output)requireValue(lineCount(part,width)*15+padding<=409&&part.length<=32767,'Display block too large; no text truncated');return output;
}
function height(row,widths,minimum=38){const h=Math.max(...row.map((v,i)=>lineCount(v??'',widths[i])))*15+14;requireValue(h<=409&&row.every(v=>typeof v!=='string'||v.length<=32767),'Display row exceeds Excel limits; no text truncated');return Math.max(minimum,h);}
const escapePointer=value=>value.replaceAll('~','~0').replaceAll('/','~1');
function flatten(target,id,value,pointer){
 if(Array.isArray(value)&&value.length){value.forEach((v,i)=>flatten(target,id,v,`${pointer}/${i}`));return;}
 if(object(value)&&Object.keys(value).length){for(const [k,v] of Object.entries(value))flatten(target,id,v,`${pointer}/${escapePointer(k)}`);return;}
 const kind=value===null?'null':Array.isArray(value)?'array':typeof value,body=typeof value==='string'?value:JSON.stringify(value);requireValue(typeof body==='string','Unsupported source field');target.push({id,pointer,kind,body});
}
function fieldRows(leaves){const rows=[];for(const leaf of leaves){const parts=chunks(leaf.body);parts.forEach((body,i)=>rows.push([leaf.id,leaf.pointer,leaf.kind,i+1,parts.length,body]));}return rows;}
function reconstruct(rows,leaves){
 const groups=new Map();for(const [id,pointer,kind,index,total,part] of rows){const key=JSON.stringify([id,pointer,kind]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push({index,total,part});}
 requireValue(groups.size===leaves.length,'Missing/duplicate original fields');for(const leaf of leaves){const list=groups.get(JSON.stringify([leaf.id,leaf.pointer,leaf.kind]));requireValue(list&&list.every((x,i)=>x.index===i+1&&x.total===list.length)&&list.map(x=>x.part).join('')===leaf.body,'Original field reconstruction failed');}
}
const protectedText=value=>typeof value==='string'&&(/^[='+@]/.test(value)||/^-?\d/.test(value)||/^(?:true|false|null)$/.test(value)||/^#(?:REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!|SPILL!|CALC!)/.test(value));
const matrixValues=rows=>rows.map(row=>row.map(value=>protectedText(value)?`'${value}`:value));
function mainRows(material,result){
 const reasons=DIMS.map(d=>`${d}：${result.dimension_reasons[d]}`).join('\n')+`\n证据：${result.evidence}\n综合说明：${result.rationale}`;
 const issues=`材料问题：${result.material_issue}\n材料核验：${JSON.stringify(result.input_assessment)}\nF子类型：${JSON.stringify(result.fairness_subtypes)}\nI子类型：${JSON.stringify(result.innovation_subtypes)}\nS质量依据：${result.safety_quality_basis}`;
 const body=chunks(material.text,31),why=chunks(reasons,46),extra=chunks(issues,28),count=Math.max(body.length,why.length,extra.length),rows=[];
 for(let i=0;i<count;i++)rows.push([material.id,`块 ${i+1}/${count}`,body[i]??'',...DIMS.map(d=>i===0?result.labels[d]:null),why[i]??'',extra[i]??'']);
 requireValue(rows.map(x=>x[2]).join('')===material.text&&rows.map(x=>x[8]).join('')===reasons&&rows.map(x=>x[9]).join('')===issues,'Main display reconstruction failed');return rows;
}
function documentRows(name,body){return chunks(body,90,14,1200).map((part,i,all)=>[name,`块 ${i+1}/${all.length}`,part]);}

function assemble(report,freezeBytes,sealBytes,released,resultBytes){
 const head=archiveHead(report,freezeBytes,sealBytes),{archive,freeze,seal,n,ids,index,batches}=head;
 keys(released,head.released,'Actual released byte inventory');keys(resultBytes,head.results,'Actual result byte inventory');
 for(const [name,bytes] of Object.entries(released))requireValue(Buffer.isBuffer(bytes)&&sha(bytes)===seal.output_files[name],'Sealed file byte hash changed');
 same(json(released['抽样清单-研究者.json']),archive.sampling_manifest_original,'Actual/archived mapping differs');
 const bundles=[];
 for(const coder of ['A','C']){
  const documents={};for(const [key,name] of Object.entries(DOCS)){const raw=released[`agent-${coder}/${name}`];requireValue(sha(raw)===freeze.files[key].sha256&&raw.equals(released[`agent-A/${name}`]),'Shared document differs from frozen version');documents[key]=text(raw);}
  const leaves=[],allMaterials=[],allResults=[],submissions=[];
  for(let batch=1;batch<=batches;batch++){
   const suffix=String(batch).padStart(2,'0'),pn=`agent-${coder}/材料-${suffix}.json`,rn=`agent-${coder}/结果-${suffix}.json`,packetBytes=released[pn],packet=json(packetBytes),packetSha=sha(packetBytes),packetRecord=archive.packet_manifest[pn];
   requireValue(packetBytes.equals(released[`agent-A/材料-${suffix}.json`]),'A/C sealed packets differ');requireValue(packet.protocol_version===freeze.protocol_version&&packet.purpose==='reference_label_holdout_AI_independent'&&packet.batch===batch&&packet.total_batches===batches,'Packet version/batch mismatch');
   const expected=ids.slice((batch-1)*25,batch*25),materialIndex=unique(packet.rows,'Packet');same([...materialIndex.keys()],expected,'Packet complete ordered IDs required');
   requireValue(packetRecord.sha256===packetSha&&packetRecord.batch===batch,'Archived packet binding mismatch');same(packetRecord.ids,expected,'Archived packet IDs differ');
   for(const row of packet.rows)requireValue(typeof row.text==='string'&&object(row.contexts)&&object(row.input_assessment)&&sha(Buffer.from(row.text))===index.get(row.id).unit_text_sha256,'Material source/context/hash missing or changed');
   const submission=archive.raw_coder_submissions[rn],manifest=archive.original_submission_manifest[rn],raw=resultBytes[rn],digest=sha(raw);
   requireValue(Buffer.isBuffer(raw)&&digest===manifest.sha256&&digest===archive.input_snapshot_hashes.submissions[rn],'First independent submission bytes changed');same(json(raw),submission,'Current submission cannot replace archived original');
   requireValue(submission.coder===coder&&submission.protocol_version===freeze.protocol_version&&submission.protocol_acknowledged===true&&submission.input_packet_sha256===packetSha,'Submission coder/protocol/packet mismatch');
   requireValue(object(submission.identity)&&submission.identity.kind==='AI','Original AI identity required');nonempty(submission.identity.name,'identity.name');nonempty(submission.completed_at,'completed_at');requireValue(/[T ]\d{2}:\d{2}/.test(submission.completed_at)&&Number.isFinite(Date.parse(submission.completed_at)),'ISO completed timestamp required');requireValue(own(submission,'rule_questions'),'Rule question metadata required');
   for(const [k,v] of [['batch',batch],['total_batches',batches]])if(own(submission,k))requireValue(Number.isInteger(submission[k])&&submission[k]===v,'Submission batch headers mismatch');
   const resultIndex=unique(submission.rows,'Original submission');same([...resultIndex.keys()].sort(),[...expected].sort(),'Missing/extra original submitted ID');same(manifest.ids,[...resultIndex.keys()],'Archived original ID order differs');requireValue(manifest.coder===coder&&manifest.input_packet_sha256===packetSha,'Original submission manifest mismatch');
   for(const row of submission.rows)judgment(row);
   allMaterials.push(...packet.rows);allResults.push(...submission.rows);
   const {rows:pRows,...pMeta}=packet,{rows:rRows,...rMeta}=submission;
   flatten(leaves,`批次${suffix}`,{file:pn,sha256:packetSha,metadata:pMeta},'材料批次');flatten(leaves,`批次${suffix}`,{file:rn,sha256:digest,metadata:rMeta},'独立提交批次');
   for(const row of packet.rows){flatten(leaves,row.id,row,'材料');flatten(leaves,row.id,resultIndex.get(row.id),'原始独立提交');}
   submissions.push({batch,file:rn,sha256:digest,input_packet_sha256:packetSha});
  }
  const materialIndex=unique(allMaterials,'All materials'),resultIndex=unique(allResults,'All original submissions');same([...materialIndex.keys()],ids,'Incomplete coder materials');same([...resultIndex.keys()].sort(),[...ids].sort(),'Incomplete coder original submissions');
  const rows=allMaterials.flatMap(m=>mainRows(m,resultIndex.get(m.id))),contexts=fieldRows(leaves);reconstruct(contexts,leaves);
  const manualRows=[...documentRows(DOCS.protocol,documents.protocol),...documentRows(DOCS.protocol_clarifications,documents.protocol_clarifications)];
  const instructions=[...documentRows('工作簿说明',`本文件呈现 AI 评审 ${coder} 的原始独立提交。共 ${n} 个分析单元；分块续行仅承载文本，不新增分析单元，标签仅在首块显示。原字段及空数组、空对象和时间字符串均完整保留。工作簿不重新编码，不形成共识标签。`),...documentRows(DOCS.reviewer_instructions,documents.reviewer_instructions)];
  for(const [key,doc] of Object.entries(documents)){const output=(key==='reviewer_instructions'?instructions:manualRows).filter(r=>r[0]===DOCS[key]).map(r=>r[2]).join('');requireValue(output===doc,'Shared document reconstruction failed');}
  const rowHeights=rows.map(r=>height(r,[10,8,31,5,5,5,5,5,46,28],78)),contextHeights=contexts.map(r=>height(r,[10,36,8,4,4,65])),manualHeights=manualRows.map(r=>height(r,[28,10,90])),instructionHeights=instructions.map(r=>height(r,[28,10,90]));
  requireValue([rows,contexts,manualRows,instructions].every(a=>a.length+4<=1048576),'Excel row limit reached; nothing truncated');
  bundles.push({coder,n,version:freeze.protocol_version,rows,rowHeights,contexts,contextHeights,leaves,manualRows,manualHeights,instructions,instructionHeights,submissions,documents});
 }
 return {...head,bundles};
}

async function inventories(root){const materials=[],results=[];for(const item of await fs.readdir(root,{withFileTypes:true})){if(!item.name.startsWith('agent-'))continue;requireValue(item.isDirectory(),'Agent input must be a directory');for(const name of await fs.readdir(path.join(root,item.name))){if(/^材料-.*\.json$/.test(name))materials.push(`${item.name}/${name}`);if(/^结果-.*\.json$/.test(name))results.push(`${item.name}/${name}`);}}return {materials:materials.sort(),results:results.sort()};}
async function load(o){
 const tracked=new Map();const read=async file=>{const raw=await fs.readFile(file),digest=sha(raw);requireValue(!tracked.has(file)||tracked.get(file)===digest,'Input changed during read');tracked.set(file,digest);return raw;};
 const reportBytes=await read(o.results),freezeBytes=await read(o.freeze),report=json(reportBytes),root=await fs.realpath(o.holdout);
 const inside=async relative=>{const p=path.join(o.holdout,relative),real=await fs.realpath(p);requireValue(real.startsWith(root+path.sep),'Holdout input escapes explicit root');return read(p);};
 const sealBytes=await inside('封存信息.json'),head=archiveHead(report,freezeBytes,sealBytes),released={},results={};
 for(const name of head.released)released[name]=await inside(name);for(const name of head.results)results[name]=await inside(name);
 const inventory=await inventories(o.holdout);same(inventory,report.archive.input_inventory,'Actual completed inventory changed');
 for(const [file,digest] of tracked)if(file!==o.results)requireValue(head.archive.filesystem_snapshot_manifest[file]===digest,'Current input path/hash not in completed archive');
 const result=assemble(report,freezeBytes,sealBytes,released,results);
 return {...result,bundles:result.bundles.filter(b=>o.coders.includes(b.coder)),tracked,inventory,holdout:o.holdout,reportSha:sha(reportBytes),reportPath:o.results};
}
async function unchanged(snapshot){for(const [file,digest] of snapshot.tracked)requireValue(sha(await fs.readFile(file))===digest,'Input changed during export');same(await inventories(snapshot.holdout),snapshot.inventory,'Input batch inventory changed during export');}
async function assertNew(file){try{await fs.lstat(file);}catch(e){if(e.code==='ENOENT')return;throw e;}throw Error('Refusing existing output: '+path.basename(file));}
function paths(coder){const prefix=path.join(OUTPUT,`v600-${coder}`);return {workbook:path.join(OUTPUT,`新增验证600-${coder}-AI评审.xlsx`),qa:prefix+'-raw-QA.json',inspection:prefix+'-inspection.ndjson',errors:prefix+'-errors.ndjson',previews:Object.fromEntries(['labels','reasons','end','contexts','contexts-end','manual','clarifications','instructions'].map(n=>[n,prefix+'-'+n+'.png']))};}

const RAW_QA=String.raw`
import sys,json,re,hashlib,zipfile,io,xml.etree.ElementTree as ET
import openpyxl
p=sys.argv[1]; expected=json.load(sys.stdin)
with open(p,'rb') as f: workbook_bytes=f.read()
w=openpyxl.load_workbook(io.BytesIO(workbook_bytes),read_only=True,data_only=False)
assert w.sheetnames==[s['name'] for s in expected['sheets']], 'Sheet inventory differs'
def same(actual, value):
 if value in ('',None) and actual is None:return True
 if isinstance(value,str):return actual==value or actual=="'"+value
 return actual==value and (isinstance(actual,bool)==isinstance(value,bool))
for spec in expected['sheets']:
 s=w[spec['name']];s.calculate_dimension(force=True)
 assert s.max_row==len(spec['matrix']) and s.max_column==len(spec['matrix'][0]),'Worksheet extent differs'
 for cells,values in zip(s.iter_rows(),spec['matrix']):
  for cell,value in zip(cells,values):
   assert cell.data_type not in ('f','e') and same(cell.value,value),'Exported cell/value/type differs'
context=w['原文语境']; observed={}
context_plan=next(s['matrix'][4:] for s in expected['sheets'] if s['name']=='原文语境')
for cells,wanted in zip(context.iter_rows(min_row=5),context_plan):
 # Every exported cell was already matched above, including an allowed text
 # escape. Use the verified original key so a literal type marker such as
 # 'null' cannot turn into a different lookup key merely due to Excel escaping.
 vals=[c.value for c in cells];key=tuple(wanted[:3]);observed.setdefault(key,[]).append(vals[3:])
assert len(observed)==len(expected['leaves']),'Original field count differs'
for leaf in expected['leaves']:
 chunks=observed[(leaf['id'],leaf['pointer'],leaf['kind'])];body=''
 for i,(index,total,part) in enumerate(chunks):
  assert index==i+1 and total==len(chunks),'Chunk order differs'
  part='' if part is None else part
  if not leaf['body'][len(body):].startswith(part):
   assert part.startswith("'") and leaf['body'][len(body):].startswith(part[1:]),'Text escaping differs'
   part=part[1:]
  body+=part
 assert body==leaf['body'],'Original field reconstruction differs'
w.close();native={};ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as z:
 for i,spec in enumerate(expected['sheets'],1):
  tree=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
  heights=[float(r.attrib['ht']) for r in tree.findall('.//s:row',ns) if 'ht' in r.attrib]
  assert heights and max(heights)<=409,'Row height exceeds limit'
  pane=tree.find('.//s:pane',ns);assert pane is not None and pane.attrib.get('state') in ('frozen','frozenSplit'),'Frozen panes absent'
  native[spec['name']]={'max_row_height':max(heights),'pane':pane.attrib}
print(json.dumps({'status':'exported_values_and_original_fields_verified','workbook_sha256':hashlib.sha256(workbook_bytes).hexdigest(),'original_field_count':len(expected['leaves']),'all_cells_match_display_plan':True,'all_original_fields_reconstructed':True,'formula_or_error_cells':0,'native_layout':native},ensure_ascii=False))
`;
async function rawQA(file,payload){return new Promise((resolve,reject)=>{const p=spawn(path.join(RUNTIME,'python/bin/python3'),['-c',RAW_QA,file],{stdio:['pipe','pipe','pipe']});let out='',err='';p.stdout.on('data',x=>out+=x);p.stderr.on('data',x=>err+=x);p.on('error',reject);p.on('close',code=>code===0?resolve(json(Buffer.from(out))):reject(Error('Read-only exported XLSX QA failed: '+err.slice(0,1200))));p.stdin.end(JSON.stringify(payload));});}
function sheetSpec(name,title,note,headers,data,heights,widths,displayWidths){const columns=headers.length;return {name,title,note,headers,data,heights,widths,displayWidths,matrix:[[title,...Array(columns-1).fill(null)],[note,...Array(columns-1).fill(null)],Array(columns).fill(null),headers,...data]};}
function specifications(bundle){return [
 sheetSpec('独立盲评',`新增验证 ${bundle.n} 条 AI评审 ${bundle.coder}`,`${bundle.version}\n同一编号的续行仅承接完整原文、理由及附加字段，不新增编码单元；五维标签只在首行。样本量 n=${bundle.n}，不等于显示行数。`,['编号','文本块','完整分析单元','S安全','E有效','Ec经济','I创新','F公平','逐维依据与证据','材料问题及附加字段'],bundle.rows,bundle.rowHeights,[16,12,56,9,9,9,9,9,80,48],[10,8,31,5,5,5,5,5,46,28]),
 sheetSpec('原文语境','原文、核验语境及原始提交全字段','材料与原始独立提交逐字段保留。相同编号与字段路径的分块按顺序拼接；不传播上下文标签。',['编号/批次','原字段路径','类型','块序','总块数','完整内容'],bundle.contexts,bundle.contextHeights,[16,64,14,8,10,116],[10,36,8,4,4,65]),
 sheetSpec('共同手册','共同手册与本轮共同澄清','两份冻结文件均按原顺序完整分块；原文及空白不改写。',['冻结文件','文本块','完整原文'],bundle.manualRows,bundle.manualHeights,[46,16,160],[28,10,90]),
 sheetSpec('执行说明','本轮评审任务说明','评审任务说明来自本轮冻结共同材料。AI 按人工流程编码，未将其改称真人评审。',['说明来源','文本块','完整说明'],bundle.instructions,bundle.instructionHeights,[46,16,160],[28,10,90])
];}

async function author(snapshot){
 // The caller has marked the artifact operation before invoking real authoring.
 await fs.mkdir(OUTPUT,{recursive:true});for(const b of snapshot.bundles){const p=paths(b.coder);for(const f of [p.workbook,p.workbook+'.partial',p.qa,p.inspection,p.errors,...Object.values(p.previews)])await assertNew(f);}
 const link=path.join(HERE,'node_modules');try{const stat=await fs.lstat(link);requireValue(stat.isSymbolicLink()&&await fs.realpath(link)===path.join(RUNTIME,'node/node_modules'),'Use only the bundled runtime node_modules symlink');}catch(e){if(e.code==='ENOENT')await fs.symlink(path.join(RUNTIME,'node/node_modules'),link,'dir');else throw e;}
 const {Workbook,SpreadsheetFile}=await import('@oai/artifact-tool');
 for(const bundle of snapshot.bundles){const p=paths(bundle.coder),specs=specifications(bundle),w=Workbook.create();
  for(const spec of specs){const s=w.worksheets.add(spec.name),last=spec.matrix.length,lastCol=String.fromCharCode(64+spec.headers.length);s.showGridLines=false;const all=s.getRange(`A1:${lastCol}${last}`);all.format.font={name:'Arial',size:11,color:COLOR.text};all.format.wrapText=true;all.format.verticalAlignment='top';all.values=matrixValues(spec.matrix);
   s.mergeCells(`A1:${lastCol}1`);s.mergeCells(`A2:${lastCol}2`);s.getRange(`A1:${lastCol}1`).format={fill:COLOR.navy,font:{name:'Arial',size:17,bold:true,color:'#FFFFFF'},rowHeight:36};s.getRange(`A2:${lastCol}2`).format.rowHeight=48;s.getRange(`A4:${lastCol}4`).format={fill:COLOR.teal,font:{bold:true,color:'#FFFFFF'},rowHeight:32};
   spec.widths.forEach((width,i)=>s.getRange(`${String.fromCharCode(65+i)}:${String.fromCharCode(65+i)}`).format.columnWidth=width);spec.heights.forEach((h,i)=>s.getRange(`A${i+5}:${lastCol}${i+5}`).format.rowHeight=h);s.freezePanes.freezeRows(4);s.freezePanes.freezeColumns(spec.name==='独立盲评'?2:1);s.tables.add(`A4:${lastCol}${last}`,true,`V600${bundle.coder}${specs.indexOf(spec)+1}`);
   if(spec.name==='独立盲评'){const labels=s.getRange(`D5:H${last}`);labels.format.horizontalAlignment='center';labels.format.font={bold:true,size:12};labels.dataValidation={rule:{type:'list',values:['0','1',PENDING]}};labels.conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:COLOR.pale,font:{color:'#155B42',bold:true}}});labels.conditionalFormats.add('containsText',{text:PENDING,format:{fill:COLOR.amber,font:{color:'#754D00'}}});}
  }
  w.recalculate();const inspections=[];for(const spec of specs){const lastCol=String.fromCharCode(64+spec.headers.length);for(const range of [`A4:${lastCol}${Math.min(7,spec.matrix.length)}`,`A${Math.max(4,spec.matrix.length-2)}:${lastCol}${spec.matrix.length}`])inspections.push((await w.inspect({kind:'table',range:`${spec.name}!${range}`,include:'values,formulas',tableMaxRows:7,tableMaxCols:10,maxChars:2500})).ndjson);}
  const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'V600 display export error scan',maxChars:3000});
  const mainLast=specs[0].matrix.length,contextLast=specs[1].matrix.length,clarifyStart=5+bundle.manualRows.findIndex(r=>r[0]===DOCS.protocol_clarifications);
  const previews=[['labels','独立盲评','A1:H7'],['reasons','独立盲评','I4:J7'],['end','独立盲评',`A${Math.max(4,mainLast-2)}:J${mainLast}`],['contexts','原文语境','A1:F7'],['contexts-end','原文语境',`A${Math.max(4,contextLast-2)}:F${contextLast}`],['manual','共同手册','A1:C7'],['clarifications','共同手册',`A${clarifyStart}:C${Math.min(clarifyStart+2,specs[2].matrix.length)}`],['instructions','执行说明','A1:C7']];
  const pictures=[];for(const [name,sheetName,range] of previews){const image=await w.render({sheetName,range,scale:1,format:'png'});pictures.push([p.previews[name],new Uint8Array(await image.arrayBuffer())]);}
  await unchanged(snapshot);for(const f of [p.workbook,p.workbook+'.partial',p.qa,p.inspection,p.errors,...Object.values(p.previews)])await assertNew(f);
  const partial=p.workbook+'.partial',reservation=await fs.open(partial,'wx');await reservation.close();await(await SpreadsheetFile.exportXlsx(w)).save(partial);
  const qa=await rawQA(partial,{sheets:specs.map(s=>({name:s.name,matrix:s.matrix})),leaves:bundle.leaves});await unchanged(snapshot);
  const checks={...qa,phase:'V600',coder:bundle.coder,analysis_units:bundle.n,main_display_rows:bundle.rows.length,shared_documents:Object.fromEntries(Object.keys(DOCS).map(k=>[k,snapshot.freeze.files[k].sha256])),freeze_sha256:snapshot.freezeSha,seal_sha256:snapshot.sealSha,completed_results_sha256:snapshot.reportSha,read_input_hashes:Object.fromEntries(snapshot.tracked),archived_frozen_file_hashes:snapshot.archive.input_snapshot_hashes.frozen,submissions:bundle.submissions,builder_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url))),no_recoding:true,no_truncation:true,visual_review_status:'Previews written; agent visual inspection still required'};
  await fs.writeFile(p.qa,encode(checks),{flag:'wx'});await fs.writeFile(p.inspection,inspections.join('\n'),{flag:'wx'});await fs.writeFile(p.errors,errors.ndjson,{flag:'wx'});for(const [file,bytes] of pictures)await fs.writeFile(file,bytes,{flag:'wx'});await fs.link(partial,p.workbook);await fs.unlink(partial);
  console.log(JSON.stringify({coder:bundle.coder,output:p.workbook,analysis_units:bundle.n,display_rows:bundle.rows.length,raw_QA:p.qa,visual_review_required:true}));
 }
}

// Invented in-memory fixtures only. No artifact-tool import or filesystem study I/O.
function synthetic(n=26){
 const frozen={};for(const key of ['protocol','reviewer_instructions','protocol_clarifications','results_bridge','legacy_results_helpers','sampler','baseline_predictions','candidate_predictions'])frozen[key]=Buffer.from(`FICTIONAL ${key}\n2026-09-26T00:00:00+08:00\n=literal\n`);
 const freeze={status:'frozen_for_paired_reference_label_holdout',phase:'V600',sample_budget:600,sampling_seed:2026092605,bootstrap_seed:2026092606,protocol_version:'FICTIONAL-v1',files:Object.fromEntries(Object.entries(frozen).map(([k,v])=>[k,{path:'/synthetic/frozen/'+k,sha256:sha(v)}]))},freezeBytes=encode(freeze),ids=Array.from({length:n},(_,i)=>`V600-${String(i+1).padStart(4,'0')}`),materials=ids.map((id,i)=>({id,text:i===0?'虚构😀原文\n'.repeat(260):'FICTIONAL '+i,source_title:'FICTIONAL SOURCE',pages:[1],contexts:{verified_object_scope:[{text:'FICTIONAL OBJECT QUOTE',kind:'negotiated_drug_renewal',source_hash_field:'unit_source_sha256',required_branch_text:'规则二简易续约',locator:{physical_pages:[2]}}],verified_rule_branch_context:{text:'规则二 简易续约'},empty:[],emptyObject:{},literal:'=original',time:'2026-09-26T23:15:30+08:00',apostrophe:"'original",pointerName:{'a/b~c':'完整字段'}},input_assessment:{status:'not_assessed'}}));
 const plan={phase:'V600',status:'drawn',seed:2026092605,n,N_star:n,freeze_manifest_sha256:sha(freezeBytes),input_hashes:Object.fromEntries(Object.entries(freeze.files).map(([k,v])=>[k,v.sha256]))},mapping={plan,rows:materials.map((m,i)=>({id:m.id,review_id:'FICTION-'+i,unit_text_sha256:sha(Buffer.from(m.text))}))};
 const released={'抽样清单-研究者.json':encode(mapping)},results={},raw={},manifests={},packets={},batches=Math.ceil(n/25);
 for(const coder of ['A','C']){for(const [key,name] of Object.entries(DOCS))released[`agent-${coder}/${name}`]=frozen[key];for(let batch=1;batch<=batches;batch++){const suffix=String(batch).padStart(2,'0'),pn=`agent-${coder}/材料-${suffix}.json`,rn=`agent-${coder}/结果-${suffix}.json`,rows=materials.slice((batch-1)*25,batch*25),packet={protocol_version:freeze.protocol_version,purpose:'reference_label_holdout_AI_independent',batch,total_batches:batches,rows};released[pn]=encode(packet);packets[pn]={sha256:sha(released[pn]),ids:rows.map(r=>r.id),batch};const judgments=rows.map((m,i)=>({id:m.id,labels:Object.fromEntries(DIMS.map(d=>[d,i===1&&coder==='C'?PENDING:0])),dimension_reasons:Object.fromEntries(DIMS.map(d=>[d,i===0?'虚构依据\n'.repeat(110):'FICTIONAL REASON'])),evidence:'=FICTIONAL EVIDENCE',rationale:'FICTIONAL RATIONALE',material_issue:'none',fairness_subtypes:[],innovation_subtypes:[],safety_quality_basis:i===1&&coder==='C'?'undetermined':'no_quality_basis',input_assessment:{status:'sufficient',basis:'FICTIONAL ASSESSMENT'}}));raw[rn]={coder,identity:{kind:'AI',name:'FICTIONAL '+coder},protocol_version:freeze.protocol_version,protocol_acknowledged:true,completed_at:'2026-09-26T23:15:30+08:00',input_packet_sha256:sha(released[pn]),batch,total_batches:batches,rule_questions:[],rows:judgments.reverse()};results[rn]=encode(raw[rn]);manifests[rn]={sha256:sha(results[rn]),coder,ids:raw[rn].rows.map(r=>r.id),input_packet_sha256:sha(released[pn])};}}
 const seal={...plan,release_status:'ready_for_blind_review',output_files:Object.fromEntries(Object.entries(released).map(([k,v])=>[k,sha(v)]))},sealBytes=encode(seal),archive={freeze_manifest_original:freeze,release_seal_original:seal,sampling_manifest_original:mapping,raw_coder_submissions:raw,original_submission_manifest:manifests,packet_manifest:packets,reference_created_by_consensus_or_imputation:false,frame_validation:{fixed_seed_sample_identities_reproduced_in_memory_only:true},input_snapshot_hashes:{freeze:sha(freezeBytes),seal:sha(sealBytes),frozen:plan.input_hashes,released:seal.output_files,submissions:Object.fromEntries(Object.entries(results).map(([k,v])=>[k,sha(v)]))},input_inventory:{materials:Object.keys(packets).sort(),results:Object.keys(results).sort()},filesystem_snapshot_manifest:Object.fromEntries(Object.values(freeze.files).map(x=>[x.path,x.sha256]))};
 return {report:{status:'completed_frozen_paired_ID_join_not_validation_pass',phase:'V600',paired_statistics:{sample_n:n,population_N:plan.N_star,reference_generated:false},archive},freezeBytes,sealBytes,released,results};
}
function selfTest(){
 const fixture=synthetic(),call=f=>assemble(f.report,f.freezeBytes,f.sealBytes,f.released,f.results),before=canonical(fixture.report),prepared=call(fixture);requireValue(prepared.bundles.length===2&&prepared.bundles.every(b=>b.n===26&&b.rows.length>26),'Synthetic complete join/layout failed');same(canonical(fixture.report),before,'Preparation mutated original archive');const rejected=[];
 const reject=(name,mutate)=>{const f=synthetic();mutate(f);try{call(f);}catch{rejected.push(name);return;}throw Error('Invalid synthetic case accepted: '+name);};
 reject('incomplete_C_even_for_A_export',f=>delete f.results['agent-C/结果-02.json']);reject('changed_original_result_bytes',f=>f.results['agent-A/结果-01.json']=Buffer.concat([f.results['agent-A/结果-01.json'],Buffer.from(' ')]));reject('altered_archive_label',f=>f.report.archive.raw_coder_submissions['agent-A/结果-01.json'].rows[0].labels.S=1);reject('changed_sealed_packet',f=>f.released['agent-A/材料-01.json']=Buffer.from('{}'));reject('missing_clarification_document',f=>delete f.released['agent-C/共同执行澄清.md']);reject('wrong_completed_n',f=>f.report.paired_statistics.sample_n=25);reject('not_completed',f=>f.report.status='running');reject('freeze_hash_changed',f=>f.freezeBytes=Buffer.concat([f.freezeBytes,Buffer.from(' ')]));
 const small=call(synthetic(1));requireValue(small.n===1&&small.batches===1,'Frozen actual n not supported');
 const full=call(synthetic(600));requireValue(full.n===600&&full.batches===24&&full.bundles.every(b=>b.submissions.length===24),'Complete 600/24-batch preparation failed');
 const positive=synthetic(),positiveName='agent-A/结果-01.json',positiveDocument=positive.report.archive.raw_coder_submissions[positiveName],positiveRow=positiveDocument.rows[0];
 positiveRow.labels=Object.fromEntries(DIMS.map(d=>[d,1]));positiveRow.fairness_subtypes=['access','affordability'];positiveRow.innovation_subtypes=['attribute','research_support'];positiveRow.safety_quality_basis='quality_and_other';
 positive.results[positiveName]=encode(positiveDocument);positive.report.archive.original_submission_manifest[positiveName].sha256=sha(positive.results[positiveName]);positive.report.archive.input_snapshot_hashes.submissions[positiveName]=sha(positive.results[positiveName]);
 positive.report.archive.normalized_rows_without_generated_reference='IGNORED SYNTHETIC NON-SOURCE';positive.report.archive.selected_machine_records_by_version_and_blind_id='IGNORED SYNTHETIC NON-SOURCE';
 const positivePrepared=call(positive).bundles.find(b=>b.coder==='A');same(positivePrepared.rows.find(r=>r[0]===positiveRow.id&&r[1].startsWith('块 1/')).slice(3,8),[1,1,1,1,1],'Original positive labels changed');requireValue(positivePrepared.leaves.some(l=>l.id===positiveRow.id&&l.pointer.endsWith('/fairness_subtypes/1')&&l.body==='affordability'),'Nonempty subtype lost');
 for(const source of ['😀'.repeat(35000),'\n'.repeat(1500),"'original",'2026-09-26T23:15:30+08:00','=SUM(A1:A2)','00123','1/3','\r\n原始空白\t'])requireValue(chunks(source).join('')===source,'Unicode/whitespace reconstruction failed');
 for(const b of prepared.bundles){reconstruct(b.contexts,b.leaves);requireValue(b.leaves.some(x=>x.pointer.includes('verified_object_scope'))&&b.leaves.some(x=>x.pointer.includes('a~1b~0c')),'Nested field/pointer lost');for(const spec of specifications(b))requireValue(spec.matrix.length===spec.data.length+4,'Sheet plan dimensions wrong');}
 for(const raw of ['{"x":1,"x":2}','{"x":1e999}','{"x":NaN}']){try{json(Buffer.from(raw));}catch{continue;}throw Error('Unsafe JSON accepted');}
 same(matrixValues([['2026-09-26T23:15:30+08:00','=literal',0,null]]),[["'2026-09-26T23:15:30+08:00","'=literal",0,null]],'Literal text/date protection differs');
 requireValue(paths('A').workbook===path.join(OUTPUT,'新增验证600-A-AI评审.xlsx')&&paths('C').workbook===path.join(OUTPUT,'新增验证600-C-AI评审.xlsx'),'Isolated output filenames differ');
 return {status:'passed_pure_synthetic_V600_workbook_preparation',checks:{both_original_coders_complete:true,full_600_and_24_batches_per_coder:true,ID_join_with_reversed_submission_order:true,original_archive_unmodified:true,actual_frozen_n_supported:true,positive_labels_and_nonempty_subtypes_preserved:true,all_nested_fields_and_empty_containers_preserved:true,unicode_long_text_and_whitespace_reconstructed:true,long_main_text_reasons_and_metadata_split_without_truncation:true,all_three_shared_documents_bound_and_preserved:true,literal_dates_formula_like_text_and_numeric_strings_protected:true,no_normalized_or_machine_labels_used:true,four_sheet_display_plan:true,isolated_output_filenames:true,rejected_cases:rejected},workbook_created:false,artifact_tool_imported:false,real_V600_inputs_read:false,limitations:['Only in-memory synthetic preparation was tested. Artifact rendering/export and read-only XLSX round-trip QA run only after completed real data is authorized.','Hash binding confirms archive/input correspondence; it does not establish semantic correctness or independent blinding.']};
}

async function main(){const options=parseOptions(process.argv.slice(2));if(options.selfTest){const qa={...selfTest(),builder_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url)))};if(options.qaOutput){await assertNew(options.qaOutput);await fs.writeFile(options.qaOutput,encode(qa),{flag:'wx'});}console.log(JSON.stringify(qa));return;}const snapshot=await load(options);await unchanged(snapshot);await author(snapshot);}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
