import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const out=path.dirname(fileURLToPath(import.meta.url));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(out,'三部门编码与注意力指标.xlsx')));
for(const [sheetName,range,name] of [
  ['κ对照','A27:F52','workbook-department-kappa.png'],
  ['方法与来源','A24:D43','workbook-source-bindings.png'],
]) {
  const image=await wb.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(path.join(out,name),new Uint8Array(await image.arrayBuffer()));
}
console.log(JSON.stringify({workbook_modified:false,rendered_views:2}));
