import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const base='/PROJECT_ROOT/outputs/goal-calibration-20261010/09-delivery/agent-review-20261010';
const out='/PROJECT_ROOT/outputs/ab-review-20261010';
for(const coder of ['A','B']) {
  const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(`${base}/编码复核表-${coder}.xlsx`));
  const summary=await wb.inspect({kind:'workbook,sheet,table',maxChars:3000,tableMaxRows:3,tableMaxCols:4});
  await fs.writeFile(`${out}/${coder}-inspection.ndjson`,summary.ndjson);
  console.log(coder,summary.ndjson);
  const picture=await wb.render({sheetName:'编码表',range:'A6:F11',scale:1,format:'png'});
  await fs.writeFile(`${out}/${coder}-preview.png`,new Uint8Array(await picture.arrayBuffer()));
}
