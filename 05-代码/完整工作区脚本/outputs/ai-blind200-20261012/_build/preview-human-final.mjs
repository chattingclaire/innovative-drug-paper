import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root='/PROJECT_ROOT/outputs/ai-blind200-20261012';
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load(`${root}/真人复核/真人标注汇总-200条.xlsx`));
const manifest=JSON.parse(await fs.readFile(`${root}/真人复核/录入记录.json`,'utf8'));
const selections=[['header','A1:E2'],...[
  ['RECODE25-00050','S'],['RECODE25-01750','I'],['RECODE25-03683','Ec'],['RECODE25-03445','I']
].map(([id,dim])=>{const row=manifest.rows.find(r=>r.source_id===id&&r.dimension===dim).sheet_row;return [`${id}-${dim}`,`A${row}:E${row}`];})];
for(const [name,range] of selections){
  const preview=await workbook.render({sheetName:'真人标注汇总',range,scale:1.2,format:'png'});
  const output=`${root}/_build/human-final-${name}.png`;
  await fs.writeFile(output,new Uint8Array(await preview.arrayBuffer()));
  console.log(output);
}
