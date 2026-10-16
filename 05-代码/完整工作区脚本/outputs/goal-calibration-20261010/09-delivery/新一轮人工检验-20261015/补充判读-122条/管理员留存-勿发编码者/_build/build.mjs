import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const here=path.dirname(fileURLToPath(import.meta.url));
const admin=path.dirname(here), packet=path.dirname(admin);
const mapping=JSON.parse(await fs.readFile(path.join(admin,'blind-assignment.json'),'utf8'));
const dimensions=['安全性 S','有效性 E','经济性 Ec','创新性 I','公平性 F'];
for(const side of ['A','B']) {
  const wb=Workbook.create(), sh=wb.worksheets.add('独立判读');
  sh.showGridLines=false;
  sh.getRange('A1:E614').format.font={name:'宋体',size:11,color:'#202A32'};
  sh.mergeCells('A1:E1');sh.getRange('A1').values=[[`编码者${side}补充判读表`]];
  sh.getRange('A1:E1').format={font:{name:'黑体',size:16,bold:true},rowHeight:36};
  sh.mergeCells('A2:E2');sh.getRange('A2').values=[['122条，共610项。打开“开始阅读.html”，按编号查原文；只填写黄色区域。待定时留空并写明原因。']];
  sh.getRange('A2:E2').format={wrapText:true,rowHeight:40};
  sh.getRange('A4:E4').values=[['材料编号','原文位置（见阅读目录）','评价维度','判定 0 / 1','理由及原文依据']];
  sh.getRange('A4:E4').format={fill:'#284857',font:{name:'黑体',size:11,color:'#FFFFFF',bold:true},rowHeight:30};
  const rows=mapping[side].flatMap(m=>dimensions.map(d=>[m.blind_id,null,d,null,null]));
  sh.getRange('A5:E614').values=rows;
  sh.getRange('A5:E614').format={rowHeight:32,verticalAlignment:'center',wrapText:true};
  for(let n=0;n<122;n++) {
    const first=5+n*5,last=first+4,m=mapping[side][n];
    sh.getRange(`A${first}:C${last}`).format.fill=n%2?'#EEF3F6':'#FFFFFF';
    sh.getRange(`D${first}:E${last}`).format.fill=n%2?'#FFF0C2':'#FFF8E4';
    sh.getRange(`A${first}:E${first}`).format.borders={top:{style:'medium',color:'#8A9CA7'}};
    sh.getRange(`B${first}:B${last}`).values=dimensions.map(()=>[m.material_locator]);
  }
  sh.getRange('B5:B614').format.font={name:'宋体',size:11,color:'#536372'};
  sh.getRange('D5:D614').dataValidation={rule:{type:'list',values:['0','1']}};
  sh.getRange('D5:D614').setNumberFormat('0');
  sh.getRange('D5:D614').format.horizontalAlignment='center';
  for(const [c,w] of [['A',13],['B',24],['C',17],['D',14],['E',58]])sh.getRange(`${c}1:${c}614`).format.columnWidth=w;
  sh.freezePanes.freezeRows(4);
  wb.recalculate();
  const check=await wb.inspect({kind:'table',range:'独立判读!A4:E9',include:'values,formulas',tableMaxRows:6,tableMaxCols:5,maxChars:2500});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'final formula error scan'});
  await fs.writeFile(path.join(here,`${side}-inspect.txt`),check.ndjson+'\n'+errors.ndjson);
  if(sh.getRange('D5:E614').values.flat().some(v=>v!==null&&v!==''))throw new Error('Response cells must be empty');
  const blob=await wb.render({sheetName:'独立判读',range:'A1:E19',scale:1.5,format:'png'});
  await fs.writeFile(path.join(here,`${side}-preview.png`),new Uint8Array(await blob.arrayBuffer()));
  const output=await SpreadsheetFile.exportXlsx(wb);
  await output.save(path.join(packet,`编码者${side}`,`补充判读-${side}-122条.xlsx`));
  console.log(JSON.stringify({side,items:122,judgments:610,blankResponseCells:1220,errors:errors.ndjson}));
}
