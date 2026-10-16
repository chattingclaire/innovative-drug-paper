import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';

const admin = path.dirname(fileURLToPath(import.meta.url));
const base = path.dirname(admin);
const out = path.join(base, '代理试填-20261010');
const payload = JSON.parse(await fs.readFile(path.join(admin, '无答案校准内容.json'), 'utf8'));
const dims = ['S', 'E', 'Ec', 'I', 'F'];
const font = 'Heiti SC';
const quotedReason = (reason, evidence) => {
  const chars = Array.from(evidence);
  return chars.length <= 120
    ? `${reason}\n依据：“${evidence}”`
    : `${reason}\n依据（节选）：“${chars.slice(0, 120).join('')}”\n完整原文见“阅读材料”同编号。`;
};
const log = { purpose: '两位AI代理独立开发试填，供真人事后复核', manual_sha256: payload.manual_sha256, workbooks: {} };
await fs.mkdir(path.join(out, 'previews'), { recursive: true });

for (const coder of ['A', 'B']) {
  const labels = JSON.parse(await fs.readFile(path.join(out, `代理${coder}独立判定.json`), 'utf8'));
  if (labels.manual_sha256 !== payload.manual_sha256 || labels.units.length !== 40) throw Error('代理材料或手册不匹配');
  const byId = new Map(labels.units.map(u => [u.material_id, u]));
  if (byId.size !== 40) throw Error('代理编号重复');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(base, `校准试填-${coder}.xlsx`)));
  const jud = wb.worksheets.getItem('填写');
  const guide = wb.worksheets.getItem('填写说明');
  const rows = payload.units.map(u => {
    const x = byId.get(u.material_id);
    if (!x) throw Error(`代理缺少${u.material_id}`);
    for (const d of dims) {
      if (![0, 1].includes(x.labels[d]) || !x.reasons[d]?.trim() || !x.evidence[d]?.trim()) throw Error(`${u.material_id}/${d}未完成`);
      if (![u.current_text, ...u.contexts].some(t => t.includes(x.evidence[d]))) throw Error(`${u.material_id}/${d}引文不在材料中`);
    }
    return [...dims.map(d => x.labels[d]), ...dims.map(d => quotedReason(x.reasons[d], x.evidence[d])), x.material_issue ?? null];
  });
  jud.getRange('C6:M45').values = rows;
  jud.getRange('A2').values = [[`AI代理${coder}校准试填（供真人复核）`]];
  jud.getRange('A3').values = [['五维标签与理由已由代理独立填写。真人复核后请另存，并记录修改。']];
  for (let i = 0; i < rows.length; i++) {
    const current = jud.getRange(`B${i + 6}`).values[0][0] ?? '';
    const strings = [current, ...rows[i].slice(5, 10)];
    const widths = [80, 35, 35, 35, 35, 35];
    const lines = Math.max(...strings.map((v, j) => String(v).split('\n').reduce((sum, t) => sum + Math.max(1, Math.ceil(Array.from(t).length / (widths[j] * 0.46))), 0)));
    jud.getRange(`A${i + 6}:M${i + 6}`).format.rowHeight = Math.max(60, Math.min(409, lines * 17 + 12));
  }
  guide.getRange('A2').values = [[`AI代理${coder}试填与真人复核记录`]];
  guide.getRange('A3').values = [['本稿保留代理初判身份；真人实际复核信息填写在下方记录栏。']];
  guide.getRange('B11:C11').values = [['本稿已完成代理独立试填，真人逐条复核后另存', '保留原代理试填稿，在下方记录实际人员、日期及修改情况。']];
  guide.getRange('C13').values = [['本表展示代理答案，真人接续填写属于事后复核；独立信度检验另行开展。']];
  guide.getRange('A14:C20').values = [
    ['代理初判者编号', `AI代理${coder}`, 'AI代理身份；不是已提交的真人判断'],
    ['代理方式与模型', '药品政策评价方向专家角色；gpt-5.6-sol', '按共同手册进行语义判读'],
    ['代理实际开始日期', new Date('2026-10-10T00:00:00Z'), '日期按本次任务的北京时间记录'],
    ['代理实际提交日期', new Date('2026-10-10T00:00:00Z'), '日期按本次任务的北京时间记录'],
    ['确认使用本表所附手册', '是', '共同手册全文与两份材料一致'],
    ['代理接触的判定材料', '共同手册及40条无答案原文、共同必要语境', '未读取另一代理、旧编码员或机器结果'],
    ['代理独立填写情况', '独立会话一次判读；两份结果完成前未交换答案', '独立结果另行保留，分歧复核不回写初判']
  ];
  guide.getRange('B16:B17').setNumberFormat('yyyy-mm-dd');
  guide.getRange('A22').values = [['真人复核记录']];
  guide.getRange('A22').format.font = { name: font, size: 14, bold: true, color: '#18202A' };
  guide.getRange('A24:C29').values = [
    ['实际复核人姓名或编号', null, '由实际复核人填写'],
    ['专业背景与编码经验', null, '由实际复核人填写'],
    ['实际复核日期', null, '填写实际日期'],
    ['确认使用所附共同手册', null, '确认后填写“是”，或说明实际使用文件'],
    ['标签及理由修改情况', null, '记录未修改，或列明修改的材料编号、维度及依据'],
    ['实际接触答案的情况', null, '如实记录已看过的代理答案、讲解或共同讨论']
  ];
  guide.getRange('A24:C29').format.font = { name: font, size: 11, color: '#18202A' };
  guide.getRange('A24:C29').format.verticalAlignment = 'top';
  guide.getRange('A24:C29').format.wrapText = true;
  guide.getRange('A24:C29').format.rowHeight = 54;
  guide.getRange('B24:B29').format.fill = '#FFF8E3';
  guide.getRange('B26').setNumberFormat('yyyy-mm-dd');
  guide.getRange('A14:C20').format.rowHeight = 74;
  wb.recalculate();
  const checks = [];
  checks.push((await wb.inspect({ kind: 'table', range: '填写!A5:G9', include: 'values,formulas', tableMaxRows: 5, tableMaxCols: 7, maxChars: 1700 })).ndjson);
  checks.push((await wb.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 50 }, maxChars: 1000 })).ndjson);
  await fs.writeFile(path.join(out, `inspect_${coder}.ndjson`), checks.join('\n'));
  const views = { labels: ['填写', 'A2:G9'], reasons: ['填写', 'H5:M9'], review: ['填写说明', 'A14:C29'] };
  for (const [name, [sheetName, range]] of Object.entries(views)) {
    const img = await wb.render({ sheetName, range, scale: 1, format: 'png' });
    await fs.writeFile(path.join(out, 'previews', `${coder}_${name}.png`), new Uint8Array(await img.arrayBuffer()));
  }
  const file = path.join(out, `代理试填-${coder}（供真人复核）.xlsx`);
  await (await SpreadsheetFile.exportXlsx(wb)).save(file);
  log.workbooks[coder] = { path: file, label_cells: 200, reason_cells: 200, human_review_fields_blank: 6, renders: Object.keys(views) };
  console.log(JSON.stringify(log.workbooks[coder]));
}
await fs.writeFile(path.join(out, '表格填写记录.json'), JSON.stringify(log, null, 2) + '\n');
