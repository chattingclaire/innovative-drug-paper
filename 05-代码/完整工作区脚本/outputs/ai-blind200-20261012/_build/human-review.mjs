import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';

const root='/PROJECT_ROOT/outputs/ai-blind200-20261012';
const outputDir=path.join(root,'真人复核');
const template=path.join(root,'_build/frozen-coder-A.xlsx');
const mode=process.argv[2]||'inspect';
if(mode.startsWith('human-wording-')) {
  const stage=mode.slice('human-wording-'.length);
  const cases=[
    {key:'summary',input:path.join(outputDir,'真人标注汇总-200条.xlsx'),sheet:'真人标注汇总',side:'A',output:path.join(outputDir,'真人标注汇总-200条.xlsx')},
    ...['A','B'].map(side=>({key:side,input:path.join(root,`_build/frozen-coder-${side}.xlsx`),sheet:'独立初判',side,output:path.join(outputDir,`${side}版`,`真人复核-${side}-200条.xlsx`)}))
  ];
  if(stage==='preview') {
    for(const item of cases.filter(x=>x.key!=='A')) {
      const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(item.input));
      console.log((await wb.inspect({kind:'table',range:`${item.sheet}!A1:E2`,tableMaxRows:2,tableMaxCols:5,tableMaxCellChars:120,maxChars:1500})).ndjson);
      const blob=await wb.render({sheetName:item.sheet,range:'A1:E2',scale:1.2,format:'png'});
      await fs.writeFile(path.join(root,`_build/review-before-${item.key}.png`),new Uint8Array(await blob.arrayBuffer()));
    }
  } else if(stage==='fill') {
    const archive=path.join(root,'_build/human-before-review-wording');
    await fs.mkdir(archive,{recursive:true});
    for(const name of ['真人标注汇总-200条.xlsx','录入记录.json','录入核查.json','录入说明.md','真人标注汇总-逐维记录.csv']) {
      try {await fs.access(path.join(archive,name));} catch {await fs.copyFile(path.join(outputDir,name),path.join(archive,name));}
    }
    const manifest=JSON.parse(await fs.readFile(path.join(archive,'录入记录.json'),'utf8'));
    const records=new Map(manifest.rows.map(item=>[`${item.source_id}/${item.dimension}`,item]));
    const mappings=JSON.parse(await fs.readFile('/PROJECT_ROOT/outputs/goal-calibration-20261010/09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json','utf8')).records;
    function displayReason(item) {
      const id=`记录：${item.source_id}；维度：${item.dimension}。`;
      if(item.human_value===null)return `待定：${item.status}\n${id}\n复核意见：${item.reason}`;
      if(item.recording_source==='user_bulk_confirmation_of_AI_consensus')return `真人复核确认：标注值为${item.human_value}。\n${id}`;
      return `真人复核意见：标注值为${item.human_value}。\n${id}\n复核理由：${item.reason}`;
    }
    const outputs=[];
    for(const item of cases) {
      const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(item.key==='summary'?path.join(archive,'真人标注汇总-200条.xlsx'):item.input));
      const sh=wb.worksheets.getItem(item.sheet);
      const byBlind=new Map(mappings.map(r=>[r[`${item.side}_blind_id`],r.source_id]));
      const source=sh.getRange('A2:C1001').values;
      const writes=source.map(([blind,,dimension],idx)=>{
        const rec=records.get(`${byBlind.get(blind)}/${dimension}`);
        if(!rec)throw new Error(`Mapping missing ${blind}/${dimension}`);
        return {row:idx+2,record:rec,display_reason:displayReason(rec)};
      });
      if(new Set(writes.map(x=>`${x.record.source_id}/${x.record.dimension}`)).size!==1000)throw new Error('Duplicate result');
      sh.getRange('A1').values=[['材料编号（点击读完整材料）']];
      sh.getRange('D1:E1').values=[['真人复核值\n（0/1）','真人复核意见']];
      sh.getRange('A1:E1').format.rowHeight=46;
      sh.getRange('D1:E1').format.wrapText=true;
      sh.getRange('D2:E1001').values=writes.map(x=>[x.record.human_value,x.display_reason]);
      sh.getRange('E2:E1001').format.wrapText=true;
      sh.getRange('E2:E1001').format.verticalAlignment='top';
      for(const x of writes) {
        const textLines=x.display_reason.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/23)),0);
        const existing=Number(sh.getRange(`A${x.row}:E${x.row}`).format.rowHeight)||42;
        sh.getRange(`A${x.row}:E${x.row}`).format.rowHeight=Math.min(409,Math.max(existing,textLines*15+12));
      }
      wb.recalculate();
      console.log((await wb.inspect({kind:'table',range:`${item.sheet}!C1:E2`,tableMaxRows:2,tableMaxCols:3,tableMaxCellChars:160,maxChars:1200})).ndjson);
      console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:500})).ndjson);
      const selections=[['header','A1:E2'],...['RECODE25-03683/Ec','RECODE25-01750/I'].map(key=>{const r=writes.find(x=>`${x.record.source_id}/${x.record.dimension}`===key).row;return [key.replace('/','-'),`A${r}:E${r}`];})];
      for(const [label,range] of selections){
        const blob=await wb.render({sheetName:item.sheet,range,scale:1.2,format:'png'});
        await fs.writeFile(path.join(root,`_build/review-after-${item.key}-${label}.png`),new Uint8Array(await blob.arrayBuffer()));
      }
      await fs.mkdir(path.dirname(item.output),{recursive:true});
      await (await SpreadsheetFile.exportXlsx(wb)).save(item.output);
      outputs.push({key:item.key,side:item.side,path:item.output,sheet_name:item.key==='summary'?'真人标注汇总':`真人复核（${item.side}顺序）`,original_sheet_name:item.sheet});
      if(item.key==='summary') for(const x of writes){x.record.original_recorded_reason=x.record.recorded_reason;x.record.recorded_reason=x.display_reason;}
    }
    manifest.presentation_revision={date:'2026-10-12',user_request:'真人复核过了，按之前真人填写内容使用真人表述，不写AI填写',display_labels:'真人复核值／真人复核意见',values_changed:0,pending_values:4,same_review_in_two_material_orders:true,original_provenance_preserved:true};
    await fs.writeFile(path.join(outputDir,'录入记录.json'),JSON.stringify(manifest,null,2));
    await fs.writeFile(path.join(outputDir,'真人复核版本记录.json'),JSON.stringify({date:'2026-10-12',same_review_in_two_material_orders:true,independent_reviewers_count_not_inferred:true,outputs},null,2));
    console.log(JSON.stringify(outputs));
  } else throw new Error('Unknown human wording stage');
  process.exit(0);
}
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load(template));
const sheet=workbook.worksheets.getItem('独立初判');
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
if(mode==='inspect') {
  console.log(workbook.help('worksheet',{search:'name|rename',include:'index,examples,notes',maxChars:3000}).ndjson);
  console.log((await workbook.inspect({kind:'table',range:'独立初判!A7:E11',tableMaxRows:5,tableMaxCols:5,tableMaxCellChars:80,maxChars:2000})).ndjson);
  const preview=await workbook.render({sheetName:'独立初判',range:'A7:E11',scale:1.2,format:'png'});
  await fs.writeFile(path.join(root,'_build/human-source.png'),new Uint8Array(await preview.arrayBuffer()));
} else if(mode==='fill') {
  const request=JSON.parse(await fs.readFile(path.join(outputDir,'复核建议原始记录.json'),'utf8'));
  const discrepancies=JSON.parse(await fs.readFile(path.join(root,'封存后对照/disagreements.json'),'utf8'));
  const byKey=new Map(discrepancies.map(r=>[`${r.source_id}/${r.dimension}`,r]));
  const lookup=new Map();
  for(const item of request.items) {
    for(const dimension of item.dimensions) {
      const key=`${item.source_id}/${dimension}`;
      if(lookup.has(key)) throw new Error(`Duplicate input ${key}`);
      const pair=byKey.get(key);
      if(!pair) throw new Error(`Unknown discrepancy ${key}`);
      if(item.suggested_value!==null && Number(pair[`${item.supported_side}_state`])!==item.suggested_value) throw new Error(`Supported side mismatch ${key}`);
      lookup.set(key,{...item,dimension,A_blind_id:pair.A_blind_id,B_blind_id:pair.B_blind_id,A_value:Number(pair.A_state),B_value:Number(pair.B_state)});
    }
  }
  if(lookup.size!==13 || [...lookup.keys()].some(key=>!byKey.has(key))) throw new Error('Input scope mismatch');
  const byBlind=new Map([...lookup.values()].map(r=>[`${r.A_blind_id}/${r.dimension}`,r]));
  const ai={};
  for(const side of ['A','B']) {
    const raw=await fs.readFile(path.join(root,`评审${side}/judgments.jsonl`));
    const seal=JSON.parse(await fs.readFile(path.join(root,`评审${side}/submission.json`),'utf8'));
    if(seal.status!=='sealed'||seal.judgments_sha256!==sha(raw))throw new Error('AI source seal mismatch');
    ai[side]=new Map(raw.toString('utf8').trim().split('\n').map(line=>{const record=JSON.parse(line);return [record.blind_id,record.judgments];}));
  }
  const mapping=JSON.parse(await fs.readFile('/PROJECT_ROOT/outputs/goal-calibration-20261010/09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json','utf8'));
  const mappingByA=new Map(mapping.records.map(record=>[record.A_blind_id,record]));
  const sourceRows=sheet.getRange('A2:C1001').values;
  const inputBlanks=sheet.getRange('D2:E1001').values;
  if(inputBlanks.some(row=>row.some(x=>x!==null && x!==''))) throw new Error('Template is not blank');
  // The public API documentation does not expose a rename operation. The final
  // metadata-only packaging step gives this sheet its human-review name.
  sheet.getRange('D1:E1').values=[['真人标注值\n（0/1）','真人说明与录入来源']];
  sheet.getRange('A1:E1').format.rowHeight=46;
  sheet.getRange('D1').format.wrapText=true;
  const written=[];
  sourceRows.forEach(([blindId,,dimension],index)=>{
    let item=byBlind.get(`${blindId}/${dimension}`);
    const pair=mappingByA.get(blindId);
    if(!pair)throw new Error('Missing source mapping');
    const a=ai.A.get(pair.A_blind_id)?.[dimension]?.value;
    const b=ai.B.get(pair.B_blind_id)?.[dimension]?.value;
    let recordingSource='user_item_specific_confirmation';
    if(!item) {
      if(![0,1].includes(a)||a!==b)throw new Error(`Bulk confirmation applied to non-consensus ${pair.source_id}/${dimension}`);
      recordingSource='user_bulk_confirmation_of_AI_consensus';
      item={source_id:pair.source_id,dimension,suggested_value:a,A_blind_id:pair.A_blind_id,B_blind_id:pair.B_blind_id,A_value:a,B_value:b,status:'用户统一确认一致',reason:'用户在本轮确认其余真人标注与AI标注没有区别。'};
    } else if(item.suggested_value===null) recordingSource='user_pending_discussion';
    const row=index+2;
    const reason=recordingSource==='user_bulk_confirmation_of_AI_consensus'?
      `用户统一确认：本项真人标注与两AI一致，标注值为${a}。\n记录：${item.source_id}；维度：${dimension}。\n本项未另提供逐项真人理由。`:
      (item.suggested_value===null?'待定：':'用户逐项意见确认录入：')+item.status+
      `\n记录：${item.source_id}；维度：${dimension}。`+
      (item.suggested_value===null?'':`\n原意见倾向支持${item.supported_side}，录入值为${item.suggested_value}。`)+
      `\n用户理由：${item.reason}`;
    sheet.getRange(`D${row}:E${row}`).values=[[item.suggested_value,reason]];
    sheet.getRange(`E${row}`).format.wrapText=true;
    sheet.getRange(`E${row}`).format.verticalAlignment='top';
    const lineCount=reason.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/23)),0);
    const existing=Number(sheet.getRange(`A${row}:E${row}`).format.rowHeight)||42;
    sheet.getRange(`A${row}:E${row}`).format.rowHeight=Math.min(409,Math.max(existing,lineCount*15+12));
    written.push({...item,human_value:item.suggested_value,recording_source:recordingSource,sheet_row:row,recorded_reason:reason});
  });
  if(written.length!==1000)throw new Error('Written row count mismatch');
  const numeric=written.filter(x=>x.suggested_value!==null);
  if(numeric.length!==996 || written.filter(x=>x.recording_source==='user_bulk_confirmation_of_AI_consensus').length!==987)throw new Error('Value counts mismatch');
  workbook.recalculate();
  const inspectRows=[written.find(x=>x.source_id==='RECODE25-00050').sheet_row,written.find(x=>x.source_id==='RECODE25-01750').sheet_row,written.find(x=>x.source_id==='RECODE25-03683').sheet_row];
  for(let i=0;i<inspectRows.length;i++) {
    const row=inspectRows[i];
    console.log((await workbook.inspect({kind:'table',range:`独立初判!C${row}:E${row}`,tableMaxRows:1,tableMaxCols:3,tableMaxCellChars:500,maxChars:2200})).ndjson);
    const preview=await workbook.render({sheetName:'独立初判',range:`A${row}:E${row}`,scale:1.2,format:'png'});
    await fs.writeFile(path.join(root,`_build/human-filled-${i}.png`),new Uint8Array(await preview.arrayBuffer()));
  }
  console.log((await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
  const outputPath=path.join(outputDir,'真人标注汇总-200条.xlsx');
  await (await SpreadsheetFile.exportXlsx(workbook)).save(outputPath);
  const manifest={status:'user_confirmed_human_labels_recorded_with_four_pending',date:request.date,qualification:request.qualification,latest_confirmation:request.subsequent_user_confirmation,formal_adjudication:false,independent_execution_verified:false,
    total_materials:200,total_dimension_rows:1000,item_specific_suggestions:13,item_specific_numeric_values:9,bulk_confirmed_values:987,numeric_values:996,pending_discussion:4,
    template:template,template_sha256:sha(await fs.readFile(template)),request_sha256:sha(await fs.readFile(path.join(outputDir,'复核建议原始记录.json'))),output_path:outputPath,output_sha256:sha(await fs.readFile(outputPath)),rows:written};
  await fs.writeFile(path.join(outputDir,'录入记录.json'),JSON.stringify(manifest,null,2));
  console.log(JSON.stringify({output:outputPath,itemSpecific:13,bulkConfirmed:987,numeric:996,pending:4}));
} else throw new Error('Invalid mode');
