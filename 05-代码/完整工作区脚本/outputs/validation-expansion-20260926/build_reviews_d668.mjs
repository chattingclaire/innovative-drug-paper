/** D668 display export only. Never codes, adjudicates, or recomputes statistics.
 * Actual usage: --results /abs/completed-paired.json --freeze /abs/freeze.json
 *               --holdout /abs/D668 --receipts /abs/first-receipts
 *               --expected-freeze-sha256 <independently supplied SHA-256>
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
const OUTPUT=path.join(HERE,'D668工作簿交付');
const RUNTIME='/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const DIMS=['S','E','Ec','I','F'], PENDING='待定';
const GROUPS=['NMPA','NHSA','NHC','GOV'], DN={NMPA:1077,NHSA:1662,NHC:329,GOV:325},Dn={NMPA:133,NHSA:222,NHC:148,GOV:165};
const FROZEN_KEYS=['corpus','adapter','classification','exposure','protocol','protocol_clarifications','sample_helpers','legacy_results_helpers','results_bridge','v600_sampler','v600_freeze','v600_sampling_manifest','v600_seal','reviewer_instructions','analysis_plan','sampler','statistics','admin_receiver','analysis_bridge','r600_source_manifest'];
const STAT_COUNTS={department_status_estimates:120,department_potential_positive_estimates:40,overall_status_estimates:30,overall_potential_positive_estimates:10,coder_pairwise_differences:60,common_robust_directions:30,stratum_coder_dimension_counts:290};
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
 const o={selfTest:false};const seen=new Set();
 for(let i=0;i<args.length;i++){const a=args[i];requireValue(!seen.has(a),'Duplicate option');seen.add(a);
  if(['--results','--freeze','--holdout','--receipts','--qa-output'].includes(a)){const v=args[++i];requireValue(typeof v==='string'&&path.isAbsolute(v),a+' requires an absolute path');o[a.slice(2).replace('qa-output','qaOutput')]=v;}
  else if(a==='--expected-freeze-sha256')o.expectedFreezeSha=hash(args[++i],'Expected freeze');
  else if(a==='--self-test')o.selfTest=true;else throw Error('Unknown option');}
 if(o.selfTest)requireValue(!o.results&&!o.freeze&&!o.holdout&&!o.receipts&&!o.expectedFreezeSha,'Self-test accepts no study inputs');
 else requireValue(o.results&&o.freeze&&o.holdout&&o.receipts&&o.expectedFreezeSha&&!o.qaOutput,'Explicit completed results, freeze, holdout, receipts and expected freeze hash required');
 return o;
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

function archiveHead(report,freezeBytes,sealBytes,options){
 requireValue(report.status==='completed_supplementary_AI_content_analysis_not_human_validation'&&report.phase==='R600_plus_D668','Completed new-schema D668 content-analysis report required');
 requireValue(options?.synthetic===true?report.synthetic_test===true:report.synthetic_test!==true,'Synthetic/actual preparation boundary mismatch');
 const archive=report.archive,stats=report.statistics,meta=stats?.metadata;requireValue(object(archive)&&object(meta)&&archive.no_machine_predictions_or_consensus_used===true,'Original independent archive required');
 requireValue(meta.unique_sample_units===1268&&meta.ai_codings_per_unit===2&&meta.schema_version==='d668-v1'&&meta.family_size===580,'Complete R600+D668 statistics metadata required');
 requireValue(meta.method_version==='D668-HT-exact-hypergeometric-bonferroni-v1','Frozen statistics method metadata required');same(meta.output_row_counts,STAT_COUNTS,'Completed output count declaration mismatch');
 for(const [name,count] of Object.entries(STAT_COUNTS))requireValue(Array.isArray(stats[name])&&stats[name].length===count,'Complete statistical archive tables required');
 requireValue(meta.analysis_kind===(options?.synthetic?'SYNTHETIC_SOFTWARE_TEST_ONLY':'OBSERVED_CODING_DESIGN_ANALYSIS'),'Completed analysis kind mismatch');
 const freeze=json(freezeBytes),seal=json(sealBytes),snap=archive.input_snapshot_hashes,freezeSha=sha(freezeBytes),sealSha=sha(sealBytes);
 requireValue(freezeSha===hash(options?.expectedFreezeSha,'Expected freeze')&&object(snap)&&Object.values(snap).includes(freezeSha)&&Object.values(snap).includes(sealSha),'Actual freeze/seal byte hash mismatch');
 same(freeze,archive.freeze_original,'Archived/actual freeze differ');same(seal,archive.release_seal_original,'Archived/actual seal differ');
 requireValue(freeze.status==='frozen_for_D668_supplementary_AI_content_analysis'&&freeze.phase==='D668'&&freeze.purpose==='supplementary_AI_content_analysis'&&freeze.sample_budget===668&&freeze.sampling_seed===2026092607,'Unexpected D668 frozen design');
 same(freeze.department_N,DN,'Frozen D population differs');same(freeze.department_n,Dn,'Frozen D allocation differs');
 nonempty(freeze.protocol_version,'protocol version');keys(freeze.files,FROZEN_KEYS,'D668 20 frozen files');
 const fileHashes={};for(const [name,entry] of Object.entries(freeze.files)){requireValue(object(entry)&&path.isAbsolute(entry.path),'Absolute frozen source path required');fileHashes[name]=hash(entry.sha256,'frozen file');requireValue(snap[entry.path]===entry.sha256,'Frozen input not bound to completed archive');}
 same(seal.input_hashes,fileHashes,'Seal/freeze hash inventory differs');
 const n=seal.n,N=seal.N_star;requireValue(n===668&&N===3393&&seal.U_N===4924&&seal.R_N===1531,'Fixed D668 population/allocation required');
 requireValue(seal.phase==='D668'&&seal.status==='drawn'&&seal.purpose==='supplementary_AI_content_analysis'&&seal.release_status==='ready_for_blind_review'&&seal.seed===freeze.sampling_seed&&seal.freeze_manifest_sha256===freezeSha,'Unexpected D668 release seal');
 for(const group of GROUPS){const h=seal.strata[group];requireValue(h?.N_h===DN[group]&&h?.n_h===Dn[group]&&Math.abs(h.pi-Dn[group]/DN[group])<1e-12&&Math.abs(h.weight-DN[group]/Dn[group])<1e-12,'Sealed stratum N/n/weights differ');}
 const mapping=archive.D_mapping_original;requireValue(object(mapping)&&object(mapping.plan),'Archived D mapping required');
 for(const [k,v] of Object.entries(mapping.plan))same(seal[k],v,'Seal/mapping plan mismatch');
 const ids=Array.from({length:n},(_,i)=>`D668-${String(i+1).padStart(4,'0')}`),index=unique(mapping.rows,'D mapping');same([...index.keys()],ids,'Complete ordered D display IDs required');
 const originalIds=new Set(),counts=Object.fromEntries(GROUPS.map(g=>[g,0]));
 for(const row of mapping.rows){nonempty(row.review_id,'global review ID');requireValue(!originalIds.has(row.review_id),'Duplicate global review ID');originalIds.add(row.review_id);hash(row.unit_text_sha256,'source text');const g=row.group;requireValue(GROUPS.includes(g)&&row.stratum===g&&row.N_h===DN[g]&&row.n_h===Dn[g]&&Math.abs(row.pi-Dn[g]/DN[g])<1e-12&&Math.abs(row.weight-DN[g]/Dn[g])<1e-12,'Mapping D stratum/weight mismatch');counts[g]++;}
 same(counts,Dn,'Mapping per-department sample count differs');
 const joins=archive.ID_join_provenance;requireValue(Array.isArray(joins)&&joins.length===1268&&new Set(joins.map(r=>r.review_id)).size===1268,'Complete unique global ID provenance required');
 const djoins=new Map(joins.filter(r=>r.phase==='D').map(r=>[r.blind_id,r]));requireValue(djoins.size===668,'D ID join count differs');
 for(const row of mapping.rows){const j=djoins.get(row.id);requireValue(j&&j.review_id===row.review_id&&j.stratum_id==='D|'+row.group&&j.unit_text_sha256===row.unit_text_sha256,'Global/blind ID join differs');}
 const batches=27,materials=[],results=[],manuals=[];
 for(const coder of ['A','C']){for(const filename of Object.values(DOCS))manuals.push(`agent-${coder}/${filename}`);for(let b=1;b<=batches;b++){const suffix=String(b).padStart(2,'0');materials.push(`agent-${coder}/材料-${suffix}.json`);results.push(`agent-${coder}/结果-${suffix}.json`);}}
 const released=['抽样清单-研究者.json',...materials,...manuals];keys(seal.output_files,released,'Sealed D release');
 for(const [name,digest] of Object.entries(seal.output_files))hash(digest,name);
 keys(archive.raw_coder_submissions,['R','D'],'Original submission phases');keys(archive.original_submission_manifest,['R','D'],'Submission manifest phases');
 keys(archive.raw_coder_submissions.D,results,'All 54 D originals');keys(archive.original_submission_manifest.D,results,'All 54 D manifest entries');
 const rNames=['A','C'].flatMap(c=>Array.from({length:24},(_,i)=>`agent-${c}/结果-${String(i+1).padStart(2,'0')}.json`));
 keys(archive.raw_coder_submissions.R,rNames,'All 48 R originals');keys(archive.original_submission_manifest.R,rNames,'All 48 R manifest entries');
 return {archive,freeze,seal,n,N,batches,index,ids,materials,results,released,freezeSha,sealSha,expectedInventory:{materials:[...materials].sort(),results:[...results].sort()}};
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
 if(Array.isArray(value)&&value.length){target.push({id,pointer,kind:'array',body:'[]'});value.forEach((v,i)=>flatten(target,id,v,`${pointer}/${i}`));return;}
 if(object(value)&&Object.keys(value).length){target.push({id,pointer,kind:'object',body:'{}'});for(const [k,v] of Object.entries(value))flatten(target,id,v,`${pointer}/${escapePointer(k)}`);return;}
 const kind=value===null?'null':Array.isArray(value)?'array':typeof value,body=typeof value==='string'?value:JSON.stringify(value);requireValue(typeof body==='string','Unsupported source field');target.push({id,pointer,kind,body});
}
function restore(leaves,id,root){
 const selected=leaves.filter(l=>l.id===id&&(l.pointer===root||l.pointer.startsWith(root+'/')));requireValue(selected.length&&selected[0].pointer===root,'Root marker missing');
 const values=new Map();for(const leaf of selected){const value=leaf.kind==='string'?leaf.body:JSON.parse(leaf.body);values.set(leaf.pointer,value);if(leaf.pointer===root)continue;const slash=leaf.pointer.lastIndexOf('/'),parent=values.get(leaf.pointer.slice(0,slash)),key=leaf.pointer.slice(slash+1).replaceAll('~1','/').replaceAll('~0','~');requireValue(parent&&typeof parent==='object','Parent container marker missing');Object.defineProperty(parent,key,{value,enumerable:true,writable:true,configurable:true});}
 return values.get(root);
}
function fieldRows(leaves){const rows=[];for(const leaf of leaves){const parts=chunks(leaf.body);parts.forEach((body,i)=>rows.push([leaf.id,leaf.pointer,leaf.kind,i+1,parts.length,body]));}return rows;}
function reconstruct(rows,leaves){
 const groups=new Map();for(const [id,pointer,kind,index,total,part] of rows){const key=JSON.stringify([id,pointer,kind]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push({index,total,part});}
 requireValue(groups.size===leaves.length,'Missing/duplicate original fields');for(const leaf of leaves){const list=groups.get(JSON.stringify([leaf.id,leaf.pointer,leaf.kind]));requireValue(list&&list.every((x,i)=>x.index===i+1&&x.total===list.length)&&list.map(x=>x.part).join('')===leaf.body,'Original field reconstruction failed');}
}
const protectedText=value=>typeof value==='string'&&(/^[=+'@\-]/.test(value)||/^\d/.test(value)||/^(?:true|false|null)$/.test(value)||/^#(?:REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!|SPILL!|CALC!)/.test(value));
const matrixValues=rows=>rows.map(row=>row.map(value=>protectedText(value)?`'${value}`:value));
function mainRows(material,result){
 const reasons=DIMS.map(d=>`${d}：${result.dimension_reasons[d]}`).join('\n')+`\n证据：${result.evidence}\n综合说明：${result.rationale}`;
 const issues=`材料问题：${result.material_issue}\n材料核验：${JSON.stringify(result.input_assessment)}\nF子类型：${JSON.stringify(result.fairness_subtypes)}\nI子类型：${JSON.stringify(result.innovation_subtypes)}\nS质量依据：${result.safety_quality_basis}`;
 const body=chunks(material.text,31),why=chunks(reasons,46),extra=chunks(issues,28),count=Math.max(body.length,why.length,extra.length),rows=[];
 for(let i=0;i<count;i++)rows.push([material.id,`块 ${i+1}/${count}`,body[i]??'',...DIMS.map(d=>i===0?result.labels[d]:null),why[i]??'',extra[i]??'']);
 requireValue(rows.map(x=>x[2]).join('')===material.text&&rows.map(x=>x[8]).join('')===reasons&&rows.map(x=>x[9]).join('')===issues,'Main display reconstruction failed');return rows;
}
function documentRows(name,body){return chunks(body,90,14,1200).map((part,i,all)=>[name,`块 ${i+1}/${all.length}`,part]);}

function assemble(report,freezeBytes,sealBytes,released,resultBytes,receiptInputs,options){
 const head=archiveHead(report,freezeBytes,sealBytes,options),{archive,freeze,seal,n,ids,index,batches}=head;
 keys(released,head.released,'Actual released byte inventory');keys(resultBytes,head.results,'Actual result byte inventory');
 keys(receiptInputs.originals,head.results,'First-receipt raw byte inventory');keys(receiptInputs.records,head.results,'First-receipt record inventory');
 const binding=json(receiptInputs.binding);same(binding,{status:'immutable_administrative_receipts',phase:'D668',freeze_sha256:head.freezeSha,seal_sha256:head.sealSha,holdout:freeze.release_directory,receiver_sha256:freeze.files.admin_receiver.sha256},'First-receipt binding differs');
 for(const [name,bytes] of Object.entries(released))requireValue(Buffer.isBuffer(bytes)&&sha(bytes)===seal.output_files[name],'Sealed file byte hash changed');
 same(json(released['抽样清单-研究者.json']),archive.D_mapping_original,'Actual/archived D mapping differs');
 const bundles=[];
 for(const coder of ['A','C']){
  const documents={};for(const [key,name] of Object.entries(DOCS)){const raw=released[`agent-${coder}/${name}`];requireValue(sha(raw)===freeze.files[key].sha256&&raw.equals(released[`agent-A/${name}`]),'Shared document differs from frozen version');documents[key]=text(raw);}
  const leaves=[],rawRoots=[],rawDocuments=[],allMaterials=[],allResults=[],submissions=[];
  const remember=(id,value,pointer)=>{const start=leaves.length;flatten(leaves,id,value,pointer);rawRoots.push({id,pointer,value,start,end:leaves.length});};
  remember('交付来源',{phase:'D668',analysis_units:668,source_result_sha256:hash(options.reportSha,'Completed result'),freeze_sha256:head.freezeSha,seal_sha256:head.sealSha,source_role:'first AI submissions only; no recoding or consensus'},'归档绑定');
  for(let batch=1;batch<=batches;batch++){
   const suffix=String(batch).padStart(2,'0'),pn=`agent-${coder}/材料-${suffix}.json`,rn=`agent-${coder}/结果-${suffix}.json`,packetBytes=released[pn],packet=json(packetBytes),packetSha=sha(packetBytes);
   keys(packet,['protocol_version','purpose','batch','total_batches','rows'],'D668 material packet schema');
   requireValue(packetBytes.equals(released[`agent-A/材料-${suffix}.json`]),'A/C sealed packets differ');requireValue(packet.protocol_version===freeze.protocol_version&&packet.purpose==='supplementary_AI_content_analysis'&&packet.batch===batch&&packet.total_batches===batches,'D packet version/purpose/batch mismatch');
   const expected=ids.slice((batch-1)*25,batch*25),materialIndex=unique(packet.rows,'Packet');same([...materialIndex.keys()],expected,'Packet complete ordered IDs required');
   requireValue(archive.input_snapshot_hashes[path.join(freeze.release_directory,pn)]===packetSha,'Archived packet hash binding mismatch');
   for(const row of packet.rows){keys(row,['id','text','source_title','pages','contexts','input_assessment','context_usage'],'D668 material row schema');requireValue(typeof row.text==='string'&&object(row.contexts)&&object(row.input_assessment)&&typeof row.source_title==='string'&&Array.isArray(row.pages)&&typeof row.context_usage==='string'&&sha(Buffer.from(row.text))===index.get(row.id).unit_text_sha256,'Material source/context/hash missing or changed');}
   const submission=archive.raw_coder_submissions.D[rn],manifest=archive.original_submission_manifest.D[rn],raw=resultBytes[rn],digest=sha(raw),first=receiptInputs.originals[rn],record=json(receiptInputs.records[rn]);
   requireValue(Buffer.isBuffer(raw)&&digest===manifest.sha256&&raw.length===manifest.byte_count&&digest===archive.input_snapshot_hashes[path.join(freeze.release_directory,rn)]&&raw.equals(first),'First independent D submission bytes changed');same(json(raw),submission,'Current submission cannot replace archived original');
   requireValue(record.file===rn&&record.sha256===digest&&record.byte_count===raw.length,'First-receipt record differs');same(record.binding,binding,'Per-file receipt binding differs');
   requireValue(submission.coder===coder&&submission.protocol_version===freeze.protocol_version&&submission.protocol_acknowledged===true&&submission.input_packet_sha256===packetSha,'Submission coder/protocol/packet mismatch');
   requireValue(object(submission.identity)&&submission.identity.kind==='AI','Original AI identity required');nonempty(submission.identity.name,'identity.name');nonempty(submission.completed_at,'completed_at');requireValue(/[T ]\d{2}:\d{2}/.test(submission.completed_at)&&Number.isFinite(Date.parse(submission.completed_at)),'ISO completed timestamp required');requireValue(own(submission,'rule_questions'),'Rule question metadata required');
   requireValue(/(?:Z|[+-]\d{2}:\d{2})$/.test(submission.completed_at),'Original completion timezone required');
   for(const [k,v] of [['batch',batch],['total_batches',batches]])requireValue(Number.isInteger(submission[k])&&submission[k]===v,'Submission batch headers mismatch');
   const resultIndex=unique(submission.rows,'Original submission');same([...resultIndex.keys()].sort(),[...expected].sort(),'Missing/extra original submitted ID');
   for(const row of submission.rows)judgment(row);
   allMaterials.push(...packet.rows);allResults.push(...submission.rows);
   const {rows:pRows,...pMeta}=packet,{rows:rRows,...rMeta}=submission;
   remember(`批次${suffix}`,{file:pn,sha256:packetSha,metadata:pMeta,row_id_order:packet.rows.map(r=>r.id)},'材料批次');remember(`批次${suffix}`,{file:rn,sha256:digest,byte_count:raw.length,metadata:rMeta,row_id_order:submission.rows.map(r=>r.id),first_receipt:record},'独立提交批次');
   for(const row of packet.rows){remember(row.id,row,'材料');remember(row.id,resultIndex.get(row.id),'原始独立提交');remember(row.id,index.get(row.id),'研究者抽样映射');}
   submissions.push({batch,file:rn,sha256:digest,first_receipt_sha256:sha(first),receipt_record_sha256:sha(receiptInputs.records[rn]),byte_count:raw.length,input_packet_sha256:packetSha});
   rawDocuments.push({batchId:`批次${suffix}`,packet,submission});
  }
  const materialIndex=unique(allMaterials,'All materials'),resultIndex=unique(allResults,'All original submissions');same([...materialIndex.keys()],ids,'Incomplete coder materials');same([...resultIndex.keys()].sort(),[...ids].sort(),'Incomplete coder original submissions');
  const rows=allMaterials.flatMap(m=>mainRows(m,resultIndex.get(m.id))),contexts=fieldRows(leaves);reconstruct(contexts,leaves);
  const restoredRoots=new Map();for(const root of rawRoots){const restored=restore(leaves.slice(root.start,root.end),root.id,root.pointer);same(restored,root.value,'Complete original JSON object reconstruction differs');restoredRoots.set(JSON.stringify([root.id,root.pointer]),restored);}
  for(const source of rawDocuments)for(const [batchPointer,rowPointer,key] of [['材料批次','材料','packet'],['独立提交批次','原始独立提交','submission']]){const meta=restoredRoots.get(JSON.stringify([source.batchId,batchPointer]));const rebuilt={...meta.metadata,rows:meta.row_id_order.map(id=>restoredRoots.get(JSON.stringify([id,rowPointer])))};same(rebuilt,source[key],'Full original document/row order reconstruction differs');}
  const manualRows=[...documentRows(DOCS.protocol,documents.protocol),...documentRows(DOCS.protocol_clarifications,documents.protocol_clarifications)];
  const instructions=[...documentRows('工作簿说明',`本文件呈现 AI 评审 ${coder} 对 D668 的首次原始独立提交。共 ${n} 个分析单元，单位不等于文件篇数。分块续行仅承载文本，不新增分析单元；标签只在首块显示。显示行数为${rows.length}。这是补充内容分析，不是新的未见样本验证。执行主体为AI，不是真人专家。原字段及空数组、空对象、null和时间字符串均完整保留；容器类型行用于完整JSON重构。工作簿不重新编码，不形成共识标签。`),...documentRows(DOCS.reviewer_instructions,documents.reviewer_instructions)];
  for(const [key,doc] of Object.entries(documents)){const output=(key==='reviewer_instructions'?instructions:manualRows).filter(r=>r[0]===DOCS[key]).map(r=>r[2]).join('');requireValue(output===doc,'Shared document reconstruction failed');}
  const rowHeights=rows.map(r=>height(r,[10,8,31,5,5,5,5,5,46,28],78)),contextHeights=contexts.map(r=>height(r,[10,36,8,4,4,65])),manualHeights=manualRows.map(r=>height(r,[28,10,90])),instructionHeights=instructions.map(r=>height(r,[28,10,90]));
  requireValue([rows,contexts,manualRows,instructions].every(a=>a.length+4<=1048576),'Excel row limit reached; nothing truncated');
  bundles.push({coder,n,version:freeze.protocol_version,rows,rowHeights,contexts,contextHeights,leaves,rawRoots,rawDocumentCount:rawDocuments.length*2,manualRows,manualHeights,instructions,instructionHeights,submissions,documents});
 }
 return {...head,bundles};
}

async function inventories(root){const materials=[],results=[];for(const item of await fs.readdir(root,{withFileTypes:true})){if(!item.name.startsWith('agent-'))continue;requireValue(item.isDirectory(),'Agent input must be a directory');for(const name of await fs.readdir(path.join(root,item.name))){if(/^材料-.*\.json$/.test(name))materials.push(`${item.name}/${name}`);if(/^结果-.*\.json$/.test(name))results.push(`${item.name}/${name}`);}}return {materials:materials.sort(),results:results.sort()};}
async function load(o){
 const tracked=new Map();const read=async file=>{const stat=await fs.lstat(file);requireValue(stat.isFile()&&!stat.isSymbolicLink(),'Regular input file required');const raw=await fs.readFile(file),digest=sha(raw);requireValue(!tracked.has(file)||tracked.get(file)===digest,'Input changed during read');tracked.set(file,digest);return raw;};
 const reportBytes=await read(o.results),freezeBytes=await read(o.freeze),report=json(reportBytes),root=await fs.realpath(o.holdout);
 requireValue(root===o.holdout&&json(freezeBytes).release_directory===root,'Explicit D release path differs from freeze');
 const inside=async relative=>{const p=path.join(o.holdout,relative),real=await fs.realpath(p);requireValue(real.startsWith(root+path.sep),'Holdout input escapes explicit root');return read(p);};
 const sourceOptions={expectedFreezeSha:o.expectedFreezeSha,reportSha:sha(reportBytes)},sealBytes=await inside('封存信息.json'),head=archiveHead(report,freezeBytes,sealBytes,sourceOptions),released={},results={};
 for(const name of head.released)released[name]=await inside(name);for(const name of head.results)results[name]=await inside(name);
 const receiptRoot=await fs.realpath(o.receipts);requireValue(receiptRoot===o.receipts&&receiptRoot!==root&&!receiptRoot.startsWith(root+path.sep)&&!root.startsWith(receiptRoot+path.sep),'Separate explicit first-receipt directory required');
 const receiptRead=async relative=>{const p=path.join(receiptRoot,relative),real=await fs.realpath(p);requireValue(real.startsWith(receiptRoot+path.sep),'Receipt input escapes explicit root');return read(p);};
 const receiptInputs={binding:await receiptRead('接收绑定.json'),originals:{},records:{}};
 for(const name of head.results){receiptInputs.originals[name]=await receiptRead(name);receiptInputs.records[name]=await receiptRead('receipt-records/'+name);}
 const inventory=await inventories(o.holdout);same(inventory,head.expectedInventory,'Actual complete D batch inventory changed');
 const receiptInventory=await inventories(receiptRoot),recordInventory=await inventories(path.join(receiptRoot,'receipt-records'));
 same(receiptInventory,{materials:[],results:head.expectedInventory.results},'First-receipt inventory incomplete');same(recordInventory,receiptInventory,'First-receipt record inventory incomplete');
 for(const [file,digest] of tracked)if(file!==o.results)requireValue(head.archive.input_snapshot_hashes[file]===digest,'Current input path/hash not in completed D archive');
 const result=assemble(report,freezeBytes,sealBytes,released,results,receiptInputs,sourceOptions);
 return {...result,tracked,inventory,receiptInventory,recordInventory,receipts:receiptRoot,holdout:o.holdout,reportSha:sha(reportBytes),reportPath:o.results};
}
async function unchanged(snapshot){for(const [file,digest] of snapshot.tracked)requireValue(sha(await fs.readFile(file))===digest,'Input changed during export');same(await inventories(snapshot.holdout),snapshot.inventory,'Input batch inventory changed during export');same(await inventories(snapshot.receipts),snapshot.receiptInventory,'Receipt inventory changed');same(await inventories(path.join(snapshot.receipts,'receipt-records')),snapshot.recordInventory,'Receipt records changed');}
async function assertNew(file){try{await fs.lstat(file);}catch(e){if(e.code==='ENOENT')return;throw e;}throw Error('Refusing existing output: '+path.basename(file));}
function paths(coder){const prefix=path.join(OUTPUT,`d668-${coder}`);return {workbook:path.join(OUTPUT,`补充内容编码668-${coder}-AI评审.xlsx`),qa:prefix+'-raw-QA.json',inspection:prefix+'-inspection.ndjson',errors:prefix+'-errors.ndjson',previews:Object.fromEntries(['labels','reasons','end','contexts','contexts-end','manual','clarifications','instructions'].map(n=>[n,prefix+'-'+n+'.png']))};}

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
 sheetSpec('独立盲评',`补充内容编码 ${bundle.n} 个分析单元 AI评审 ${bundle.coder}`,`${bundle.version}\n首次独立AI提交。分析单元 n=${bundle.n}；显示行数=${bundle.rows.length}。五维标签只在首块显示。补充内容分析，不是新验证。`,['编号','文本块','完整分析单元','S安全','E有效','Ec经济','I创新','F公平','逐维依据与证据','材料问题及附加字段'],bundle.rows,bundle.rowHeights,[16,12,56,9,9,9,9,9,80,48],[10,8,31,5,5,5,5,5,46,28]),
 sheetSpec('原文语境','原文、核验语境及原始提交全字段','材料与原始独立提交逐字段保留。相同编号与字段路径的分块按顺序拼接；不传播上下文标签。',['编号/批次','原字段路径','类型','块序','总块数','完整内容'],bundle.contexts,bundle.contextHeights,[16,64,14,8,10,116],[10,36,8,4,4,65]),
 sheetSpec('共同手册','共同手册与本轮共同澄清','两份冻结文件均按原顺序完整分块；原文及空白不改写。',['冻结文件','文本块','完整原文'],bundle.manualRows,bundle.manualHeights,[46,16,160],[28,10,90]),
 sheetSpec('执行说明','本轮评审任务说明','评审任务说明来自本轮冻结共同材料。AI 按人工流程编码，未将其改称真人评审。',['说明来源','文本块','完整说明'],bundle.instructions,bundle.instructionHeights,[46,16,160],[28,10,90])
];}
function previewPlan(bundle,specs){
 const mainLast=specs[0].matrix.length,contextLast=specs[1].matrix.length,clarifyStart=5+bundle.manualRows.findIndex(r=>r[0]===DOCS.protocol_clarifications);
 return [['labels','独立盲评','A1:J7'],['reasons','独立盲评','I4:J7'],['end','独立盲评',`A${Math.max(4,mainLast-2)}:J${mainLast}`],['contexts','原文语境','A1:F7'],['contexts-end','原文语境',`A${Math.max(4,contextLast-2)}:F${contextLast}`],['manual','共同手册','A1:C7'],['clarifications','共同手册',`A${clarifyStart}:C${Math.min(clarifyStart+2,specs[2].matrix.length)}`],['instructions','执行说明','A1:C7']];
}

async function author(snapshot){
 // The caller has marked the artifact operation before invoking real authoring.
 await fs.mkdir(OUTPUT,{recursive:true});for(const b of snapshot.bundles){const p=paths(b.coder);for(const f of [p.workbook,p.workbook+'.partial',p.qa,p.inspection,p.errors,...Object.values(p.previews)])await assertNew(f);}
 const link=path.join(HERE,'node_modules');try{const stat=await fs.lstat(link);requireValue(stat.isSymbolicLink()&&await fs.realpath(link)===path.join(RUNTIME,'node/node_modules'),'Use only the bundled runtime node_modules symlink');}catch(e){if(e.code==='ENOENT')await fs.symlink(path.join(RUNTIME,'node/node_modules'),link,'dir');else throw e;}
 const {Workbook,SpreadsheetFile}=await import('@oai/artifact-tool');
 for(const bundle of snapshot.bundles){const p=paths(bundle.coder),specs=specifications(bundle),w=Workbook.create();
  for(const spec of specs){const s=w.worksheets.add(spec.name),last=spec.matrix.length,lastCol=String.fromCharCode(64+spec.headers.length);s.showGridLines=false;const all=s.getRange(`A1:${lastCol}${last}`);all.format.font={name:'Arial',size:11,color:COLOR.text};all.format.wrapText=true;all.format.verticalAlignment='top';all.values=matrixValues(spec.matrix);
   s.mergeCells(`A1:${lastCol}1`);s.mergeCells(`A2:${lastCol}2`);s.getRange(`A1:${lastCol}1`).format={fill:COLOR.navy,font:{name:'Arial',size:17,bold:true,color:'#FFFFFF'},rowHeight:36};s.getRange(`A2:${lastCol}2`).format.rowHeight=48;s.getRange(`A4:${lastCol}4`).format={fill:COLOR.teal,font:{bold:true,color:'#FFFFFF'},rowHeight:32};
   spec.widths.forEach((width,i)=>s.getRange(`${String.fromCharCode(65+i)}:${String.fromCharCode(65+i)}`).format.columnWidth=width);spec.heights.forEach((h,i)=>s.getRange(`A${i+5}:${lastCol}${i+5}`).format.rowHeight=h);s.freezePanes.freezeRows(4);s.freezePanes.freezeColumns(spec.name==='独立盲评'?2:1);s.tables.add(`A4:${lastCol}${last}`,true,`D668${bundle.coder}${specs.indexOf(spec)+1}`);
   if(spec.name==='独立盲评'){const labels=s.getRange(`D5:H${last}`);labels.format.horizontalAlignment='center';labels.format.font={bold:true,size:12};labels.dataValidation={rule:{type:'list',values:['0','1',PENDING]}};labels.conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:COLOR.pale,font:{color:'#155B42',bold:true}}});labels.conditionalFormats.add('containsText',{text:PENDING,format:{fill:COLOR.amber,font:{color:'#754D00'}}});}
  }
  w.recalculate();const inspections=[];for(const spec of specs){const lastCol=String.fromCharCode(64+spec.headers.length);for(const range of [`A4:${lastCol}${Math.min(7,spec.matrix.length)}`,`A${Math.max(4,spec.matrix.length-2)}:${lastCol}${spec.matrix.length}`])inspections.push((await w.inspect({kind:'table',range:`${spec.name}!${range}`,include:'values,formulas',tableMaxRows:7,tableMaxCols:10,maxChars:2500})).ndjson);}
  const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'D668 display export error scan',maxChars:3000});
  const previews=previewPlan(bundle,specs);
  const pictures=[];for(const [name,sheetName,range] of previews){const image=await w.render({sheetName,range,scale:1,format:'png'});pictures.push([p.previews[name],new Uint8Array(await image.arrayBuffer())]);}
  await unchanged(snapshot);for(const f of [p.workbook,p.workbook+'.partial',p.qa,p.inspection,p.errors,...Object.values(p.previews)])await assertNew(f);
  const partial=p.workbook+'.partial',reservation=await fs.open(partial,'wx');await reservation.close();await(await SpreadsheetFile.exportXlsx(w)).save(partial);
  const qa=await rawQA(partial,{sheets:specs.map(s=>({name:s.name,matrix:s.matrix})),leaves:bundle.leaves});await unchanged(snapshot);
  const checks={...qa,phase:'D668',coder:bundle.coder,analysis_units:bundle.n,main_display_rows:bundle.rows.length,original_JSON_roots_reconstructed:bundle.rawRoots.length,complete_material_and_submission_documents_reconstructed:bundle.rawDocumentCount,shared_documents:Object.fromEntries(Object.keys(DOCS).map(k=>[k,snapshot.freeze.files[k].sha256])),freeze_sha256:snapshot.freezeSha,seal_sha256:snapshot.sealSha,completed_results_sha256:snapshot.reportSha,read_input_hashes:Object.fromEntries(snapshot.tracked),archived_frozen_file_hashes:Object.fromEntries(Object.entries(snapshot.freeze.files).map(([k,v])=>[k,v.sha256])),submissions:bundle.submissions,builder_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url))),no_recoding:true,no_truncation:true,visual_review_status:'Previews written; agent visual inspection still required'};
  await fs.writeFile(p.qa,encode(checks),{flag:'wx'});await fs.writeFile(p.inspection,inspections.join('\n'),{flag:'wx'});await fs.writeFile(p.errors,errors.ndjson,{flag:'wx'});for(const [file,bytes] of pictures)await fs.writeFile(file,bytes,{flag:'wx'});await fs.link(partial,p.workbook);await fs.unlink(partial);
  console.log(JSON.stringify({coder:bundle.coder,output:p.workbook,analysis_units:bundle.n,display_rows:bundle.rows.length,raw_QA:p.qa,visual_review_required:true}));
 }
}

// Invented in-memory D668 fixtures only; no real material/label files, no authoring.
function synthetic(){
 const n=668,batches=27,root='/SYNTHETIC_ONLY/D668',receiptRoot='/SYNTHETIC_ONLY/first-receipts';
 const frozen=Object.fromEntries(FROZEN_KEYS.map(k=>[k,Buffer.from('SYNTHETIC '+k+'\n2026-09-26T00:00:00+08:00\n=literal\n')]));
 const freeze={status:'frozen_for_D668_supplementary_AI_content_analysis',phase:'D668',purpose:'supplementary_AI_content_analysis',sample_budget:n,sampling_seed:2026092607,department_N:DN,department_n:Dn,protocol_version:'SYNTHETIC-ONLY-D668-v1',release_directory:root,files:Object.fromEntries(Object.entries(frozen).map(([k,v])=>[k,{path:'/SYNTHETIC_ONLY/frozen/'+k,sha256:sha(v)}]))};
 const freezeBytes=encode(freeze),ids=Array.from({length:n},(_,i)=>'D668-'+String(i+1).padStart(4,'0'));
 const groupList=GROUPS.flatMap(g=>Array(Dn[g]).fill(g));
 const materials=ids.map((id,i)=>({id,text:i===0?'合成😀完整原文\n'.repeat(280):'SYNTHETIC TEXT '+i,source_title:'SYNTHETIC SOURCE',pages:[1],contexts:{verified_object_scope:[{text:'SYNTHETIC CONTEXT',kind:'test'}],empty:[],emptyObject:{},nil:null,boolean:false,numeric:1.5,numericObject:{'0':'object key'},literal:'=original',negativeLiteral:'-original',time:'2026-09-26T23:15:30+08:00',apostrophe:"'original",pointerName:{'a/b~c':'完整字段'},nested:[{list:[true,null,'00123']}],proto:JSON.parse('{"__proto__":{"literal":true}}')},input_assessment:{status:'not_assessed'},context_usage:'SYNTHETIC ONLY'}));
 const strata=Object.fromEntries(GROUPS.map(g=>[g,{N_h:DN[g],n_h:Dn[g],pi:Dn[g]/DN[g],weight:DN[g]/Dn[g]}]));
 const plan={phase:'D668',status:'drawn',purpose:'supplementary_AI_content_analysis',seed:2026092607,n,N_star:3393,U_N:4924,R_N:1531,strata,freeze_manifest_sha256:sha(freezeBytes),input_hashes:Object.fromEntries(Object.entries(freeze.files).map(([k,v])=>[k,v.sha256]))};
 const mapping={plan,rows:materials.map((m,i)=>({id:m.id,review_id:'SYNTHETIC-D-GLOBAL-'+i,group:groupList[i],stratum:groupList[i],...strata[groupList[i]],unit_text_sha256:sha(Buffer.from(m.text)),source_entry:'SYNTHETIC-SOURCE',record_sha256:sha(Buffer.from('SYNTHETIC-'+i))}))};
 const released={'抽样清单-研究者.json':encode(mapping)},results={},raw={R:{},D:{}},manifests={R:{},D:{}},tracked=Object.fromEntries(Object.values(freeze.files).map(x=>[x.path,x.sha256]));
 tracked['/SYNTHETIC_ONLY/freeze.json']=sha(freezeBytes);
 for(const coder of ['A','C']){
  for(const [key,name] of Object.entries(DOCS))released['agent-'+coder+'/'+name]=frozen[key];
  for(let b=1;b<=24;b++){const name='agent-'+coder+'/结果-'+String(b).padStart(2,'0')+'.json';raw.R[name]={coder,rows:Array.from({length:25},(_,j)=>({id:'SYNTHETIC-R-'+((b-1)*25+j),labels:Object.fromEntries(DIMS.map(d=>[d,0]))}))};const bytes=encode(raw.R[name]);manifests.R[name]={sha256:sha(bytes),byte_count:bytes.length};}
  for(let batch=1;batch<=batches;batch++){const suffix=String(batch).padStart(2,'0'),pn='agent-'+coder+'/材料-'+suffix+'.json',rn='agent-'+coder+'/结果-'+suffix+'.json',rows=materials.slice((batch-1)*25,batch*25),packet={protocol_version:freeze.protocol_version,purpose:'supplementary_AI_content_analysis',batch,total_batches:batches,rows};released[pn]=encode(packet);
   const judgments=rows.map((m,i)=>({id:m.id,labels:Object.fromEntries(DIMS.map(d=>[d,i===1&&coder==='C'?PENDING:0])),dimension_reasons:Object.fromEntries(DIMS.map(d=>[d,i===0&&batch===1?'合成理由\n'.repeat(120):'SYNTHETIC REASON'])),evidence:'=SYNTHETIC EVIDENCE',rationale:'SYNTHETIC RATIONALE',material_issue:'无',fairness_subtypes:[],innovation_subtypes:[],safety_quality_basis:i===1&&coder==='C'?'undetermined':'no_quality_basis',input_assessment:{status:'sufficient',basis:'SYNTHETIC ASSESSMENT'},additional_original_field:{nil:null,emptyObject:{},when:'2026-09-26T23:15:30+08:00'}}));
   raw.D[rn]={coder,identity:{kind:'AI',name:'SYNTHETIC '+coder},protocol_version:freeze.protocol_version,protocol_acknowledged:true,completed_at:'2026-09-26T23:15:30+08:00',input_packet_sha256:sha(released[pn]),batch,total_batches:batches,rule_questions:[],rows:judgments.reverse()};
   results[rn]=encode(raw.D[rn]);manifests.D[rn]={sha256:sha(results[rn]),byte_count:results[rn].length};tracked[path.join(root,rn)]=sha(results[rn]);
  }
 }
 const seal={...plan,release_status:'ready_for_blind_review',output_files:Object.fromEntries(Object.entries(released).map(([k,v])=>[k,sha(v)]))},sealBytes=encode(seal);
 for(const [name,bytes] of Object.entries(released))tracked[path.join(root,name)]=sha(bytes);tracked[path.join(root,'封存信息.json')]=sha(sealBytes);
 const binding={status:'immutable_administrative_receipts',phase:'D668',freeze_sha256:sha(freezeBytes),seal_sha256:sha(sealBytes),holdout:root,receiver_sha256:freeze.files.admin_receiver.sha256},receiptInputs={binding:encode(binding),originals:{},records:{}};
 tracked[path.join(receiptRoot,'接收绑定.json')]=sha(receiptInputs.binding);
 for(const [name,bytes] of Object.entries(results)){receiptInputs.originals[name]=Buffer.from(bytes);receiptInputs.records[name]=encode({file:name,sha256:sha(bytes),byte_count:bytes.length,binding,recorded_at:'2026-09-26T23:15:30+08:00'});tracked[path.join(receiptRoot,name)]=sha(bytes);tracked[path.join(receiptRoot,'receipt-records',name)]=sha(receiptInputs.records[name]);}
 const joins=[...Array.from({length:600},(_,i)=>({phase:'R',blind_id:'SYNTHETIC-R-'+i,review_id:'SYNTHETIC-R-GLOBAL-'+i,stratum_id:'R|SYNTHETIC',unit_text_sha256:sha(Buffer.from('SYNTHETIC'))})),...mapping.rows.map(r=>({phase:'D',blind_id:r.id,review_id:r.review_id,stratum_id:'D|'+r.group,unit_text_sha256:r.unit_text_sha256}))];
 const archive={freeze_original:freeze,release_seal_original:seal,D_mapping_original:mapping,ID_join_provenance:joins,raw_coder_submissions:raw,original_submission_manifest:manifests,input_snapshot_hashes:tracked,no_machine_predictions_or_consensus_used:true};
 const report={status:'completed_supplementary_AI_content_analysis_not_human_validation',phase:'R600_plus_D668',synthetic_test:true,statistics:{metadata:{unique_sample_units:1268,ai_codings_per_unit:2,schema_version:'d668-v1',family_size:580,method_version:'D668-HT-exact-hypergeometric-bonferroni-v1',output_row_counts:STAT_COUNTS,analysis_kind:'SYNTHETIC_SOFTWARE_TEST_ONLY'},...Object.fromEntries(Object.entries(STAT_COUNTS).map(([k,n])=>[k,Array.from({length:n},()=>({synthetic_stub:true}))]))},archive};
 return {report,freezeBytes,sealBytes,released,results,receiptInputs,receiptRoot};
}
function rebindSyntheticOriginal(f,name){
 const raw=encode(f.report.archive.raw_coder_submissions.D[name]),digest=sha(raw),binding=json(f.receiptInputs.binding),root=f.report.archive.freeze_original.release_directory;
 f.results[name]=raw;f.receiptInputs.originals[name]=Buffer.from(raw);f.report.archive.original_submission_manifest.D[name]={sha256:digest,byte_count:raw.length};
 f.receiptInputs.records[name]=encode({file:name,sha256:digest,byte_count:raw.length,binding,recorded_at:'2026-09-26T23:15:30+08:00'});
 f.report.archive.input_snapshot_hashes[path.join(root,name)]=digest;f.report.archive.input_snapshot_hashes[path.join(f.receiptRoot,name)]=digest;f.report.archive.input_snapshot_hashes[path.join(f.receiptRoot,'receipt-records',name)]=sha(f.receiptInputs.records[name]);
}
function selfTest(){
 const call=f=>assemble(f.report,f.freezeBytes,f.sealBytes,f.released,f.results,f.receiptInputs,{synthetic:true,expectedFreezeSha:sha(f.freezeBytes),reportSha:sha(encode(f.report))});
 const fixture=synthetic(),before=canonical(fixture.report),prepared=call(fixture);
 requireValue(prepared.bundles.length===2&&prepared.bundles.every(b=>b.n===668&&b.submissions.length===27&&b.rows.length>668),'Complete D668/27 batches preparation failed');same(canonical(fixture.report),before,'Preparation changed source archive');
 const rejected=[];const reject=(name,mutate)=>{const f=synthetic();mutate(f);try{call(f);}catch{rejected.push(name);return;}throw Error('Invalid synthetic fixture accepted: '+name);};
 reject('incomplete_C_original',f=>delete f.results['agent-C/结果-27.json']);
 reject('changed_original_bytes',f=>f.results['agent-A/结果-01.json']=Buffer.concat([f.results['agent-A/结果-01.json'],Buffer.from(' ')]));
 reject('changed_first_receipt',f=>f.receiptInputs.originals['agent-A/结果-01.json']=Buffer.from('{}'));
 reject('missing_first_receipt_record',f=>delete f.receiptInputs.records['agent-C/结果-27.json']);
 reject('wrong_record_file',f=>{const name='agent-A/结果-01.json',v=json(f.receiptInputs.records[name]);v.file='agent-C/结果-01.json';f.receiptInputs.records[name]=encode(v);});
 reject('wrong_archive_label',f=>f.report.archive.raw_coder_submissions.D['agent-A/结果-01.json'].rows[0].labels.S=1);
 reject('illegal_label_even_with_rebound_bytes',f=>{f.report.archive.raw_coder_submissions.D['agent-A/结果-01.json'].rows[0].labels.S=null;rebindSyntheticOriginal(f,'agent-A/结果-01.json');});
 reject('duplicate_ID_even_with_rebound_bytes',f=>{const rows=f.report.archive.raw_coder_submissions.D['agent-A/结果-01.json'].rows;rows[0].id=rows[1].id;rebindSyntheticOriginal(f,'agent-A/结果-01.json');});
 reject('missing_row_even_with_rebound_bytes',f=>{f.report.archive.raw_coder_submissions.D['agent-A/结果-01.json'].rows.pop();rebindSyntheticOriginal(f,'agent-A/结果-01.json');});
 reject('changed_sealed_packet',f=>f.released['agent-A/材料-01.json']=Buffer.from('{}'));
 reject('missing_shared_clarification',f=>delete f.released['agent-C/共同执行澄清.md']);
 reject('wrong_unique_n',f=>f.report.statistics.metadata.unique_sample_units=1336);
 reject('incomplete_statistical_archive',f=>f.report.statistics.overall_status_estimates.pop());
 reject('not_completed',f=>f.report.status='running');
 reject('V600_status_cannot_be_adapted',f=>{f.report.status='completed_frozen_paired_ID_join_not_validation_pass';f.report.phase='V600';});
 reject('freeze_changed_bytes',f=>f.freezeBytes=Buffer.concat([f.freezeBytes,Buffer.from(' ')]));
 reject('wrong_global_ID_join',f=>f.report.archive.ID_join_provenance[600].review_id='OTHER');
 reject('wrong_mapping_weight',f=>f.report.archive.D_mapping_original.rows[0].weight=1);
 reject('missing_R_manifest',f=>delete f.report.archive.original_submission_manifest.R['agent-C/结果-24.json']);
 const positive=synthetic(),name='agent-A/结果-01.json',row=positive.report.archive.raw_coder_submissions.D[name].rows[0];
 row.labels=Object.fromEntries(DIMS.map(d=>[d,1]));row.fairness_subtypes=['access','affordability'];row.innovation_subtypes=['attribute','research_support'];row.safety_quality_basis='quality_and_other';rebindSyntheticOriginal(positive,name);
 positive.report.archive.machine_predictions='IGNORED SYNTHETIC';positive.report.archive.consensus='IGNORED SYNTHETIC';positive.report.archive.normalized_analysis_payload='IGNORED NON-SOURCE IN THIS DISPLAY TEST';
 const p=call(positive).bundles[0];same(p.rows.find(r=>r[0]===row.id&&r[1].startsWith('块 1/')).slice(3,8),[1,1,1,1,1],'Original positive labels not retained');
 requireValue(p.leaves.some(l=>l.id===row.id&&l.pointer.endsWith('/fairness_subtypes/1')&&l.body==='affordability'),'Subtype field lost');
 for(const b of prepared.bundles){reconstruct(b.contexts,b.leaves);requireValue(b.rows.filter(r=>r[1].startsWith('块 1/')).length===668,'Display rows counted as analysis units');for(const root of b.rawRoots)same(restore(b.leaves.slice(root.start,root.end),root.id,root.pointer),root.value,'Full typed root reconstruction differs');requireValue(b.leaves.some(x=>x.kind==='null')&&b.leaves.some(x=>x.pointer.includes('a~1b~0c'))&&b.leaves.some(x=>x.pointer.includes('__proto__')),'Typed/nested fields lost');for(const s of specifications(b))requireValue(s.matrix.length===s.data.length+4,'Sheet plan extent differs');}
 for(const b of prepared.bundles){const specs=specifications(b),previews=previewPlan(b,specs);for(const spec of specs){const target=previews.find(p=>p[1]===spec.name&&p[2].startsWith('A1:'));requireValue(target&&target[2].startsWith('A1:'+String.fromCharCode(64+spec.headers.length)),'Preview clips merged title');}}
 for(const source of ['😀'.repeat(35000),'\n'.repeat(1500),"'original",'2026-09-26T23:15:30+08:00','=SUM(A1:A2)','-literal','00123','1/3','\r\n原始空白\t'])requireValue(chunks(source).join('')===source,'Unicode/newline reconstruction failed');
 for(const raw of ['{"x":1,"x":2}','{"x":1e999}','{"x":NaN}','{"x":9007199254740993}']){try{json(Buffer.from(raw));}catch{continue;}throw Error('Unsafe JSON accepted');}
 same(matrixValues([['2026-09-26T23:15:30+08:00','=literal','-literal','null',0,null]]),[["'2026-09-26T23:15:30+08:00","'=literal","'-literal","'null",0,null]],'Text/date/null-string protection differs');
 requireValue(paths('A').workbook.endsWith('/D668工作簿交付/补充内容编码668-A-AI评审.xlsx')&&paths('C').workbook.endsWith('/D668工作簿交付/补充内容编码668-C-AI评审.xlsx'),'Requested isolated output names differ');
 return {status:'passed_pure_synthetic_D668_workbook_preparation',phase:'D668',synthetic_test:true,checks:{complete_new_schema_not_V600_adaptation:true,two_coders_668_units_27_batches:true,ID_join_with_reversed_submission_order:true,global_ID_provenance_verified:true,all_first_receipt_bindings_verified:true,original_archive_unmodified:true,all_20_frozen_hashes_bound:true,positive_pending_and_subtype_fields_preserved:true,all_typed_JSON_roots_reconstruct:true,null_empty_containers_numeric_object_keys_and_pointer_escaping:true,complete_unicode_long_text_and_CRLF_preserved:true,display_rows_distinguished_from_units:true,three_shared_documents_preserved:true,formula_like_date_and_numeric_text_protected:true,no_machine_normalized_or_consensus_labels_used:true,four_sheet_display_plan:true,rejected_cases:rejected},prepared_counts:prepared.bundles.map(b=>({coder:b.coder,analysis_units:b.n,display_rows:b.rows.length,raw_field_rows:b.contexts.length,typed_original_roots:b.rawRoots.length})),workbook_created:false,artifact_tool_imported:false,artifact_marker_run:false,real_D_materials_or_labels_read:false,limitations:['Preparation and ID/hash/raw-field reconstruction were tested on explicit invented fixtures only. No authoring, rendering, exported-XLSX round-trip or native Excel behavior has been tested in this turn.','Actual export must run artifact-tool, all preview inspections, input immutability checks and read-only openpyxl round-trip QA after the complete real bridge archive exists.','Raw JSON values and all source text are reconstructed; original byte whitespace/numeric lexemes remain in hashed first-submission archives, not re-created by Excel.','Hash binding proves source correspondence, not substantive coding validity or independent human review.']};
}
async function main(){
 requireValue(await fs.realpath(process.execPath)===await fs.realpath(path.join(RUNTIME,'node/bin/node')),'Use the bundled Node executable');
 const options=parseOptions(process.argv.slice(2));
 if(options.selfTest){const qa={...selfTest(),builder_sha256:sha(await fs.readFile(fileURLToPath(import.meta.url)))};if(options.qaOutput){await assertNew(options.qaOutput);await fs.writeFile(options.qaOutput,encode(qa),{flag:'wx'});}console.log(JSON.stringify(qa));return;}
 const snapshot=await load(options);await unchanged(snapshot);await author(snapshot);
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
