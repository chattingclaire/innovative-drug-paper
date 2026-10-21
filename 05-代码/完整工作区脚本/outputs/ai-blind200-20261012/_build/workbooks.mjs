import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const project = '/PROJECT_ROOT';
const inputRoot = path.join(project, 'outputs/goal-calibration-20261010/09-delivery/human200-independent-preparation-root');
const outputRoot = path.join(project, 'outputs/ai-blind200-20261012');
const mode = process.argv[2] || 'inspect';
const sides = process.argv[3] ? [process.argv[3]] : ['A', 'B'];
const dimensions = ['S', 'E', 'Ec', 'I', 'F'];
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const compactJson = value => JSON.stringify(value);
function locatorText(locator) {
  const labels={paragraph_ids:'段落',paragraph_id:'段落',physical_pages:'页',pages:'页',source_unit_id:'原文单元',sequence_index:'顺序'};
  return Object.entries(locator || {}).map(([key,value])=>`${labels[key] || key}：${Array.isArray(value)?value.join('、'):value}`).join('；');
}
function contextText(value) {
  if (typeof value === 'string') return value || '当前条款';
  if (value && typeof value === 'object' && !Array.isArray(value) && (value.current_source || value.current_locator)) {
    const location = locatorText(value.current_source?.locator || value.current_locator || {});
    const count = value.used_contexts?.length || 0;
    return `当前原文定位：${location}。${count ? `实际使用补充语境${count}处，完整定位及片段见同目录《完整依据.md》对应盲号、维度。` : '未使用补充语境。'}`;
  }
  return `完整语境定位见同目录《完整依据.md》对应盲号、维度。`;
}
function fullContext(value) {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object' && (value.current_source || value.current_locator)) {
    const lines = [`当前原文定位：${locatorText(value.current_source?.locator || value.current_locator || {})}`];
    for (const context of value.used_contexts || []) {
      const source = context.source || `${context.source_ref?.source_resource_id || context.context_id || ''} ${locatorText(context.source_ref?.locator || context.locator || {})}`;
      lines.push(`补充语境出处：${source}\n\n${context.text || context.quote || ''}${context.visual_observation?'\n\n图示判读记录：'+context.visual_observation:''}`);
    }
    return lines.join('\n\n');
  }
  return JSON.stringify(value,null,2);
}

for (const side of sides) {
  if (!['A','B'].includes(side)) throw new Error('Unknown side');
  const input = path.join(outputRoot, '_build', `frozen-coder-${side}.xlsx`);
  const buildDir = path.join(outputRoot, '_build');
  await fs.mkdir(buildDir, {recursive:true});
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(input));
  const sheet = workbook.worksheets.getItem('独立初判');
  const sourceRows = sheet.getRange('A2:C1001').values;
  if (sourceRows.length !== 1000) throw new Error('Unexpected source row count');
  if (mode === 'inspect') {
    console.log((await workbook.inspect({kind:'sheet', include:'id,name', maxChars:1000})).ndjson);
    console.log((await workbook.inspect({kind:'table', range:'独立初判!A1:E6', tableMaxRows:6, tableMaxCols:5, tableMaxCellChars:100, maxChars:2500})).ndjson);
    const blob = await workbook.render({sheetName:'独立初判', range:'A1:E6', scale:1.3, format:'png'});
    await fs.writeFile(path.join(buildDir, `source-${side}.png`), new Uint8Array(await blob.arrayBuffer()));
    await fs.writeFile(path.join(buildDir, `source-${side}-rows.json`), JSON.stringify(sourceRows));
    continue;
  }
  if (mode !== 'fill') throw new Error('Unknown mode');
  const sideDir = path.join(outputRoot, `评审${side}`);
  const raw = await fs.readFile(path.join(sideDir, 'judgments.jsonl'));
  const submission = JSON.parse(await fs.readFile(path.join(sideDir, 'submission.json'), 'utf8'));
  if (submission.status !== 'sealed' || submission.identity !== `AI评审${side}` ||
      submission.independent !== true || submission.human_judgments !== false ||
      submission.judgments_sha256 !== sha(raw) || submission.record_count !== 200 ||
      submission.judgment_count !== 1000) throw new Error('Submission seal mismatch');
  const entries = raw.toString('utf8').trim().split('\n').map(x => JSON.parse(x));
  if (entries.length !== 200) throw new Error(`Expected 200 entries, got ${entries.length}`);
  const byId = new Map(entries.map(x => [x.blind_id, x]));
  if (byId.size !== 200) throw new Error('Duplicate blind IDs');
  const seen = new Set();
  const outputValues = sourceRows.map(([blindId, , dimension]) => {
    const entry = byId.get(blindId);
    const judgment = entry?.judgments?.[dimension];
    if (!dimensions.includes(dimension) || !judgment) throw new Error(`Missing judgment ${blindId}/${dimension}`);
    seen.add(blindId);
    const {value,evidence,context,reason} = judgment;
    if (![0,1,null].includes(value) || typeof value === 'boolean') throw new Error('Invalid judgment value');
    if (typeof reason !== 'string' || !reason.trim()) throw new Error('Missing reason');
    if (typeof evidence !== 'string' || context === undefined) throw new Error('Invalid evidence/context');
    const rationale = `${value === null ? '待定：' : ''}${reason}\n原文依据：${evidence || '见具体待补项'}\n语境定位：${contextText(context)}`;
    if (rationale.length > 32767) throw new Error('Excel text limit exceeded');
    return [value, rationale];
  });
  if (seen.size !== 200) throw new Error('Coverage mismatch');
  const notes=[`# AI评审${side}完整依据`,'','本文件呈现已封存独立判断的完整证据与语境。数值及理由与独立JSONL一致。',''];
  for (const blindId of seen) {
    notes.push(`## ${blindId}`,'');
    for (const dimension of dimensions) {
      const j=byId.get(blindId).judgments[dimension];
      notes.push(`### ${dimension}：${j.value===null?'待定':j.value}`,'',`判断理由：${j.reason}`,'',`原文依据：${j.evidence}`,'',fullContext(j.context),'');
    }
  }
  await fs.writeFile(path.join(sideDir,'完整依据.md'),notes.join('\n'));
  sheet.getRange('D2:E1001').values = outputValues;
  // Preserve the five-column source template; increase only populated reason rows as needed.
  sheet.getRange('E2:E1001').format.wrapText = true;
  sheet.getRange('E2:E1001').format.verticalAlignment = 'top';
  const overflowRows = [];
  let longestRow = 2;
  const countLines=(text,capacity)=>text.split('\n').reduce((n,line)=>n+Math.max(1,Math.ceil(line.length/capacity)),0);
  let reasonCapacity=23;
  while (reasonCapacity<120 && outputValues.some(([,text])=>countLines(text,reasonCapacity)*15+12>409)) reasonCapacity++;
  if (reasonCapacity>23) sheet.getRange('E1:E1001').format.columnWidth=reasonCapacity*2;
  for (let idx=0;idx<outputValues.length;idx++) {
    const text = outputValues[idx][1];
    if (text.length > outputValues[longestRow-2][1].length) longestRow=idx+2;
    const lineCount = countLines(text,reasonCapacity);
    const row = sheet.getRange(`A${idx+2}:E${idx+2}`);
    const existingHeight = Number(row.format.rowHeight) || 92;
    const targetHeight = Math.min(409,Math.max(existingHeight,lineCount*15+12));
    if (lineCount*15+12 > 409) overflowRows.push({cell:`E${idx+2}`,blind_id:sourceRows[idx][0],dimension:sourceRows[idx][2],estimatedLines:lineCount,characters:text.length});
    row.format.rowHeight = targetHeight;
  }
  workbook.recalculate();
  console.log((await workbook.inspect({kind:'table',range:'独立初判!C1:E6',include:'values,formulas',tableMaxRows:6,tableMaxCols:3,tableMaxCellChars:150,maxChars:3000})).ndjson);
  console.log((await workbook.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
  for (const [label,range] of [['top','A1:E6'],['middle','A497:E501'],['end','A997:E1001'],['longest',`A${longestRow}:E${longestRow}`]]) {
    const blob = await workbook.render({sheetName:'独立初判',range,scale:1.2,format:'png'});
    await fs.writeFile(path.join(buildDir,`${side}-${label}.png`),new Uint8Array(await blob.arrayBuffer()));
  }
  const outPath = path.join(sideDir,`AI独立盲评-${side}-200条.xlsx`);
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(outPath);
  await fs.writeFile(path.join(sideDir,'workbook-export.json'),JSON.stringify({identity:`AI评审${side}`,sourceWorkbook:input,sourceWorkbookSha256:sha(await fs.readFile(input)),judgmentsSha256:sha(raw),submissionSealVerified:true,outputWorkbook:outPath,outputWorkbookSha256:sha(await fs.readFile(outPath)),records:200,judgments:1000,humanJudgments:false,estimatedOverflowRows:overflowRows},null,2));
  console.log(JSON.stringify({side,output:outPath,records:200,judgments:1000}));
}
