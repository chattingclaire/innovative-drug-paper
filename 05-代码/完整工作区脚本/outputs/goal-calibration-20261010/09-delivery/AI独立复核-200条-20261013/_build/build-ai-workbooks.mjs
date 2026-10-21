import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const buildDir = path.dirname(fileURLToPath(import.meta.url));
const outputRoot = path.dirname(buildDir);
const deliveryRoot = path.dirname(outputRoot);
const sourceRoot = path.join(deliveryRoot, '独立真人判读-200条-20261013');
const python = '/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const marker = '/LOCAL_HOME/.codex/plugins/cache/openai-primary-runtime/spreadsheets/26.1009.11318/skills/spreadsheets/container_tools/mark_artifact_operation_started.mjs';
const dimensions = ['S', 'E', 'Ec', 'I', 'F'];
const coders = ['A', 'B'];
const headers = ['AI判定（0/1）\n待定留空', 'AI理由与原文依据'];

function insist(condition, message) {
  if (!condition) throw new Error(message);
}
async function exists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}
function validatePredictions(data, coder) {
  insist(Array.isArray(data) && data.length === 200, `${coder}: predictions must contain exactly 200 records`);
  const found = new Map();
  for (const record of data) {
    insist(record && new RegExp(`^${coder}-\\d{3}$`).test(record.blind_id), `${coder}: invalid blind_id`);
    insist(!found.has(record.blind_id), `${coder}: duplicate ${record.blind_id}`);
    insist(record.judgments && Object.keys(record.judgments).sort().join(',') === [...dimensions].sort().join(','), `${record.blind_id}: five exact dimensions required`);
    for (const dimension of dimensions) {
      const judgment = record.judgments[dimension];
      insist(judgment && [0, 1, null].includes(judgment.value), `${record.blind_id}/${dimension}: value must be 0, 1 or null`);
      insist(typeof judgment.reason === 'string' && judgment.reason.trim().length > 0, `${record.blind_id}/${dimension}: reason required`);
      insist(judgment.reason.length <= 32767, `${record.blind_id}/${dimension}: Excel cell length exceeded`);
    }
    found.set(record.blind_id, record);
  }
  return found;
}

// Conservative text measurement in Excel column-width units. The estimate
// distinguishes Latin from wide CJK/emoji characters and respects explicit lines.
function displayUnits(text) {
  let total = 0;
  for (const character of String(text)) {
    if (/\p{Mark}/u.test(character) || character === '\u200d' || character === '\ufe0f') continue;
    if (character === '\t') { total += 4; continue; }
    const point = character.codePointAt(0);
    const wide = point >= 0x1100 && (point <= 0x115f || point >= 0x2329 && point <= 0x232a || point >= 0x2e80 && point <= 0xa4cf || point >= 0xac00 && point <= 0xd7a3 || point >= 0xf900 && point <= 0xfaff || point >= 0xfe10 && point <= 0xfe6f || point >= 0xff00 && point <= 0xff60 || point >= 0xffe0 && point <= 0xffe6 || point >= 0x1f000);
    total += wide ? 2 : 1;
  }
  return total;
}

function wrappedLines(text, width, fontPoints) {
  // Excel column widths are approximately 7 px per default digit. Reserve
  // horizontal padding and another 10% for font and wrapping differences.
  const capacity = Math.max(8, Math.floor((width * 7 - 18) / (fontPoints * 96 / 72 * 0.56) * 0.90));
  let lines = 0;
  for (const paragraph of String(text).replaceAll('\r\n', '\n').replaceAll('\r', '\n').split('\n')) {
    let paragraphLines = 1;
    let occupied = 0;
    const tokens = paragraph.match(/[\p{Script=Latin}\p{Number}_./:%?=&+#@-]+|[^\r\n]/gu) ?? [];
    for (const token of tokens) {
      const units = displayUnits(token);
      if (units <= capacity) {
        if (occupied > 0 && occupied + units > capacity) { paragraphLines++; occupied = 0; }
        occupied += units;
      } else {
        for (const character of token) {
          const characterUnits = displayUnits(character);
          if (occupied > 0 && occupied + characterUnits > capacity) { paragraphLines++; occupied = 0; }
          occupied += characterUnits;
        }
      }
    }
    lines += paragraphLines;
  }
  return lines;
}

function neededHeight(text, width, fontPoints) {
  return Math.ceil(wrappedLines(text, width, fontPoints) * (fontPoints * 1.45 + 1) + 8);
}

if (!process.argv.includes('--confirmed')) {
  console.log('Prepared only. After both reviewers have submitted and the coordinator confirms, run this script with --confirmed. No predictions or workbooks were opened.');
  process.exit(0);
}

// Read completed submissions only after the explicit confirmation flag.
const jobs = [];
for (const coder of coders) {
  const outputDir = path.join(outputRoot, `AI复核者${coder}`);
  const predictionPath = path.join(outputDir, 'predictions.json');
  const predictions = validatePredictions(JSON.parse(await fs.readFile(predictionPath, 'utf8')), coder);
  const reviewerNotePath = path.join(outputDir, 'AI复核说明.txt');
  const reviewerNoteSha256 = createHash('sha256').update(await fs.readFile(reviewerNotePath)).digest('hex');
  const sourceDir = path.join(sourceRoot, `发给编码者${coder}`);
  const sourcePath = path.join(sourceDir, `独立判读-${coder}-200条.xlsx`);
  await fs.access(sourcePath);
  jobs.push({ coder, outputDir, predictionPath, predictions, sourceDir, sourcePath, reviewerNotePath, reviewerNoteSha256 });
}

// Emit the required operation marker once for this two-workbook authoring task.
const markerReceipt = path.join(buildDir, 'operation-started.json');
if (!(await exists(markerReceipt))) {
  const result = execFileSync(process.execPath, [marker, '--operation-kind', 'edit', '--expected-output-count', '2', '--output-format', 'xlsx'], { cwd: buildDir, encoding: 'utf8' });
  await fs.writeFile(markerReceipt, JSON.stringify({ startedAt: new Date().toISOString(), result }, null, 2));
}

const reports = [];
for (const job of jobs) {
  const { coder, outputDir, predictionPath, predictions, sourceDir, sourcePath } = job;
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));
  const sheet = workbook.worksheets.getItem('独立初判');
  const before = sheet.getRange('A1:E1001').values;
  const sourceLayout = JSON.parse(execFileSync(python, [path.join(buildDir, 'verify-ai-workbook.py'), '--source-layout', sourcePath], { cwd: buildDir, encoding: 'utf8' }));
  insist(before.length === 1001, `${coder}: unexpected workbook row count`);
  const seen = new Map();
  const entries = [];
  for (let r = 1; r < before.length; r++) {
    const [blindId, material, dimension, blankValue, blankReason] = before[r];
    insist((blankValue === null || blankValue === undefined || blankValue === '') && (blankReason === null || blankReason === undefined || blankReason === ''), `${coder}: source contains prefilled review cells`);
    insist(predictions.has(blindId) && dimensions.includes(dimension), `${coder}: unexpected source identity at row ${r + 1}`);
    insist(typeof material === 'string' && material.length, `${coder}: missing material link`);
    const keys = seen.get(blindId) ?? [];
    keys.push(dimension);
    seen.set(blindId, keys);
    const judgment = predictions.get(blindId).judgments[dimension];
    // A leading '=' is literal reviewer prose, never a spreadsheet formula.
    const reason = judgment.reason.startsWith('=') ? `'${judgment.reason}` : judgment.reason;
    entries.push([judgment.value, reason]);
  }
  insist(seen.size === 200 && [...seen.values()].every(ds => ds.join(',') === dimensions.join(',')), `${coder}: expected 200 complete five-dimension blocks`);
  insist([...predictions.keys()].every(id => seen.has(id)), `${coder}: predictions do not match source IDs`);

  // Retain the established tab name; the two changed headers identify AI review explicitly.
  sheet.getRange('D1:E1').values = [headers];
  sheet.getRange('D2:E1001').values = entries;
  const lengths = entries.map(row => displayUnits(row[1])).sort((a, b) => a - b);
  const p90 = lengths[Math.floor(lengths.length * 0.9)];
  const widths = {
    D: Math.max(sourceLayout.widths.D, 20),
    E: Math.max(sourceLayout.widths.E, p90 > 260 ? 96 : p90 > 180 ? 88 : 80),
  };
  sheet.getRange('D1:D1001').format.columnWidth = widths.D;
  sheet.getRange('E1:E1001').format.columnWidth = widths.E;
  const rowHeights = {};
  for (let row = 1; row <= 1001; row++) {
    const rowMetadata = sourceLayout.rows[row];
    const reasonText = row === 1 ? headers[1] : predictions.get(before[row - 1][0]).judgments[before[row - 1][2]].reason;
    const reasonHeight = neededHeight(reasonText, widths.E, rowMetadata.eFontPoints);
    const judgmentHeight = row === 1 ? neededHeight(headers[0], widths.D, rowMetadata.dFontPoints) : 0;
    const height = Math.max(rowMetadata.height, reasonHeight, judgmentHeight);
    insist(height <= 409, `${coder}: row ${row} requires ${height} points, beyond Excel's safe row height; resolve readability before exporting`);
    rowHeights[row] = height;
    if (height !== rowMetadata.height) sheet.getRange(`A${row}:E${row}`).format.rowHeight = height;
  }
  const layoutPath = path.join(buildDir, `${coder}-layout-adjustments.json`);
  await fs.writeFile(layoutPath, JSON.stringify({ widths, rowHeights, p90DisplayUnits: p90, purpose: 'Fit AI reasons without clipping; preserve original height minimum' }, null, 2));
  workbook.recalculate();
  const after = sheet.getRange('A1:E1001').values;
  for (let r = 0; r < 1001; r++) {
    for (let c = 0; c < 3; c++) insist(after[r][c] === before[r][c], `${coder}: source column changed at row ${r + 1}`);
  }
  const scan = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 30 }, summary: 'AI review formula error scan', maxChars: 3000 });
  await fs.writeFile(path.join(buildDir, `${coder}-inspection.ndjson`), scan.ndjson);

  await fs.mkdir(outputDir, { recursive: true });
  for (const folder of ['材料', '附件']) {
    await fs.cp(path.join(sourceDir, folder), path.join(outputDir, folder), { recursive: true, force: true });
  }
  for (const filename of ['材料目录.html', '共同编码手册.txt']) {
    await fs.copyFile(path.join(sourceDir, filename), path.join(outputDir, filename));
  }
  const workbookFilename = `AI复核-${coder}-200条.xlsx`;
  const aiDescription = `AI 复核者 ${coder} 结果包交付说明\n\n本目录保存 AI 对 200 条材料的五维复核结果。复核者身份为 AI，不是真人编码者的首次提交。\n\n打开“${workbookFilename}”查看结果。D 列是 AI 判定（0 或 1；待定留空），E 列是 AI 理由与原文依据。每条材料包含 S、E、Ec、I、F 五个维度。\n\n打开“材料目录.html”查阅原文及附件；“共同编码手册.txt”是统一判读规则。材料和附件保留原样。\n\n“AI复核说明.txt”由该 AI 复核者单独提交，记录其实际材料处理、待定及争议事项，技术整理程序保持其原文。\n\n真人打印盲评与这些 AI 复核结果分别保存。此目录不含真人提交声明。\n`;
  await fs.writeFile(path.join(outputDir, 'AI交付说明.txt'), aiDescription, 'utf8');
  // The unchanged material directory links this established filename. Supply
  // an AI-specific note there instead of copying the human filling instructions.
  await fs.writeFile(path.join(outputDir, '填写说明.txt'), `本目录为 AI 复核者 ${coder} 的结果包。\n\n请阅读“AI复核说明.txt”，并打开“${workbookFilename}”查看 AI 判定与依据。\n此文件为 AI 目录导航说明，不是真人填写说明或真人首次提交声明。\n`, 'utf8');
  const candidate = path.join(buildDir, `AI复核-${coder}-200条.candidate.xlsx`);
  const saved = await SpreadsheetFile.exportXlsx(workbook);
  await saved.save(candidate);
  const verification = execFileSync(python, [path.join(buildDir, 'verify-ai-workbook.py'), sourcePath, candidate, predictionPath, outputDir, layoutPath], { cwd: buildDir, encoding: 'utf8' });
  const report = JSON.parse(verification);
  await fs.writeFile(path.join(buildDir, `${coder}-verification.json`), JSON.stringify(report, null, 2));

  const longestIndex = entries.reduce((best, row, index) => String(row[1]).length > String(entries[best][1]).length ? index : best, 0);
  const longestRow = longestIndex + 2;
  const views = [
    ['opening', 'A1:E11'],
    ['longest-reason', `A${Math.max(2, longestRow - 1)}:E${Math.min(1001, longestRow + 1)}`],
    ['ending', 'A997:E1001'],
  ];
  for (const [label, range] of views) {
    const rendered = await workbook.render({ sheetName: '独立初判', range, scale: 1.5, format: 'png' });
    await fs.writeFile(path.join(buildDir, `${coder}-${label}.png`), new Uint8Array(await rendered.arrayBuffer()));
  }
  const finalPath = path.join(outputDir, `AI复核-${coder}-200条.xlsx`);
  await fs.copyFile(candidate, finalPath);
  const entrance = `<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI 复核者 ${coder} 阅读入口</title><style>body{max-width:760px;margin:48px auto;padding:0 24px;font:17px/1.75 system-ui,sans-serif;color:#263544}h1{font-size:28px}li{margin:14px 0}a{color:#205ea8}</style></head><body><h1>AI 复核者 ${coder} 阅读入口</h1><p>本包是 AI 对 200 条材料的五维复核结果。复核者身份为 AI，不是真人编码者的首次提交。</p><ul><li><a href="${encodeURIComponent(workbookFilename)}">打开 AI 复核工作簿</a></li><li><a href="${encodeURIComponent('材料目录.html')}">阅读 200 条原文及附件</a></li><li><a href="${encodeURIComponent('共同编码手册.txt')}">共同编码手册</a></li><li><a href="${encodeURIComponent('AI复核说明.txt')}">AI 复核者提交的说明</a></li><li><a href="${encodeURIComponent('AI交付说明.txt')}">结果包交付说明</a></li></ul></body></html>\n`;
  await fs.writeFile(path.join(outputDir, 'AI复核阅读入口.html'), entrance, 'utf8');
  const navigation = JSON.parse(execFileSync(python, [path.join(buildDir, 'verify-ai-workbook.py'), '--links-only', outputDir], { cwd: buildDir, encoding: 'utf8' }));
  insist(createHash('sha256').update(await fs.readFile(job.reviewerNotePath)).digest('hex') === job.reviewerNoteSha256, `${coder}: reviewer-submitted explanation changed during delivery`);
  await fs.writeFile(path.join(buildDir, `${coder}-navigation-verification.json`), JSON.stringify(navigation, null, 2));
  reports.push({ ...report, navigation, reviewerNoteSha256: job.reviewerNoteSha256, reviewerNotePreserved: true, output: finalPath, visualReviewPending: true });
}
await fs.writeFile(path.join(buildDir, 'build-report.json'), JSON.stringify(reports, null, 2));
console.log(JSON.stringify(reports, null, 2));
console.log('Open all six PNG previews before reporting delivery complete. Original human workbooks and submission declarations were not changed or copied.');
