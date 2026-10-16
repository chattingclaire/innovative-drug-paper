// Finite constructed parser controls only. Originals are never exported or changed.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const here = path.dirname(fileURLToPath(import.meta.url));
const binding = JSON.parse(await fs.readFile(path.join(here, 'bindings.json'), 'utf8'));
const mapping = JSON.parse(await fs.readFile(binding.inputs.mapping.path, 'utf8'));
const destination = path.join(here, 'checks', 'constructed-fixtures');
await fs.mkdir(destination, {recursive: true});
const anchor = mapping.records.find(x => x.A_blind_id === 'A-000001');
const bRow = 2 + (Number(anchor.B_blind_id.slice(2)) - 1) * 5;
const checks = [];
for (const side of ['A', 'B']) {
  for (const variant of ['sparse', 'invalid']) {
    const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(binding.inputs[`template_${side}`].path));
    const sheet = wb.worksheets.getItem('初判-pre-release');
    // D/E only: source prose never displayed or semantically inspected.
    if (side === 'A' && variant === 'sparse') {
      const before = await wb.render({sheetName: sheet.name, range: 'D1:E5', scale: 1, format: 'png'});
      await fs.writeFile(path.join(destination, 'before-DE.png'), new Uint8Array(await before.arrayBuffer()));
    }
    if (variant === 'sparse') {
      const start = side === 'A' ? 2 : bRow;
      sheet.getRange(`D${start}:E${start + 2}`).values = side === 'A'
        ? [[0, '构造测试理由，非真人首判。'], ['1', '构造测试文本1，非真人首判。'], ['0', '构造测试文本0，非真人首判。']]
        : [[1, '构造测试分歧，非真人首判。'], [1, '构造测试一致，非真人首判。'], ['0', '构造测试一致，非真人首判。']];
    } else {
      sheet.getRange('A2:A3').values = [[`${side}-999999`], [`${side}-999999`]];
      sheet.getRange('C3:C4').values = [['S'], ['WRONG']];
      if (side === 'A') {
        sheet.getRange('D5').formulas = [['=1']];
        sheet.getRange('D6').values = [[true]];
        sheet.getRange('D7').values = [[1]];
        sheet.getRange('D8:D9').values = [[' 1 '], ['1.0']];
      }
    }
    wb.recalculate();
    const start = variant === 'sparse' && side === 'B' ? bRow : 2;
    checks.push({side, variant, inputRange: `D${start}:E${start + 7}`, inspection: (await wb.inspect({kind: 'table', range: `${sheet.name}!D${start}:E${start + 7}`, include: 'values,formulas', tableMaxRows: 8, tableMaxCols: 2, maxChars: 2000})).ndjson});
    if (side === 'A') {
      const after = await wb.render({sheetName: sheet.name, range: 'D1:E9', scale: 1, format: 'png'});
      await fs.writeFile(path.join(destination, `${variant}-DE.png`), new Uint8Array(await after.arrayBuffer()));
    }
    await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(destination, `${side}-${variant}.xlsx`));
  }
}
await fs.writeFile(path.join(destination, 'artifact-inspection.json'), JSON.stringify({status: 'constructed_only', source_id: anchor.source_id, A_row: 2, B_row: bRow, checks}, null, 2) + '\n');
console.log(JSON.stringify({constructed_workbooks: 4, A_row: 2, B_row: bRow, original_workbooks_modified: false}));
