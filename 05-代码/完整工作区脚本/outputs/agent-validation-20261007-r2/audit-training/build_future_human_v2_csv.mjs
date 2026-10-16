import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook } from '@oai/artifact-tool';

const auditDir = path.dirname(fileURLToPath(import.meta.url));
const run = path.dirname(auditDir);
const matrices = JSON.parse(await fs.readFile(path.join(auditDir, 'future_human_v2_csv_matrices.json'), 'utf8'));
const quote = value => '"' + String(value ?? '').replaceAll('"', '""') + '"';
for (const coder of ['A', 'C']) {
  const wb = Workbook.create();
  const sheet = wb.worksheets.add('真人编码空白表');
  sheet.getRange('A1:S241').values = matrices[coder];
  wb.recalculate();
  const values = sheet.getRange('A1:S241').values.map(row => row.map(value => value ?? ''));
  if (JSON.stringify(values) !== JSON.stringify(matrices[coder])) throw new Error(`Workbook changed source/blank values for ${coder}`);
  if (values.slice(1).some(row => row.slice(5).some(value => value !== ''))) throw new Error('Answer field is not blank');
  const inspected = await wb.inspect({kind:'table', range:'真人编码空白表!F1:S3', include:'values,formulas', tableMaxRows:3, tableMaxCols:14, maxChars:1200});
  if (!inspected.ndjson) throw new Error('Could not inspect blank answer columns');
  // CSV is the explicitly requested analytical format. Serialize actual authoring
  // tool cell values, with quoted UTF-8 fields and no formula or style payload.
  const csv = '\ufeff' + values.map(row => row.map(quote).join(',')).join('\r\n') + '\r\n';
  await fs.writeFile(path.join(run, 'future-human-validation-v2', `真人${coder}-空白编码表.csv`), csv, 'utf8');
  console.log(JSON.stringify({coder, rows:values.length-1, columns:values[0].length, answerFieldsFilled:0}));
}
