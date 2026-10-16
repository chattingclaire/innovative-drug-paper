import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const mode=process.argv[2]??'preview';
const dims=['S','E','Ec','I','F'];
if(mode==='preview'){
  const w=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(dir,'agent-A','校准试填-A.xlsx')));
  const summary=await w.inspect({kind:'workbook,sheet,table',maxChars:1800,tableMaxRows:2,tableMaxCols:3});
  console.log(summary.ndjson);
  for(const [name,range] of [['source-left','A1:G8'],['source-right','H5:J8']]){
    const b=await w.render({sheetName:'独立试填',range,scale:1,format:'png'});
    await fs.writeFile(path.join(dir,name+'.png'),new Uint8Array(await b.arrayBuffer()));
  }
} else if(mode==='final-preview'){
  for(const coder of ['A','C']){
    const w=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(dir,`校准盲评-${coder}-AI专家.xlsx`)));
    for(const [name,range] of [['upper','A9:J11'],['lower','A16:J19']]){
      const b=await w.render({sheetName:'独立试填',range,scale:1,format:'png'});
      await fs.writeFile(path.join(dir,`review-${coder}-${name}.png`),new Uint8Array(await b.arrayBuffer()));
    }
  }
} else if(mode==='manual-preview'){
  const w=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(dir,'agent-A','校准试填-A.xlsx')));
  const b=await w.render({sheetName:'编码手册',range:'A1:A7',scale:1,format:'png'});
  await fs.writeFile(path.join(dir,'source-manual.png'),new Uint8Array(await b.arrayBuffer()));
} else if(mode==='fill'){
  const binding=JSON.parse(await fs.readFile(path.join(dir,'统一口径','三种方法版本绑定.json'),'utf8'));
  const note=(await fs.readFile(path.join(dir,'统一口径','执行说明.md'),'utf8')).trim().split(/\n\s*\n/).slice(1);
  for(const coder of (process.argv[3]?[process.argv[3]]:['A','C'])){
    const r=JSON.parse(await fs.readFile(path.join(dir,`agent-${coder}`,`result-${coder}.json`),'utf8'));
    if(r.protocol_version!==binding.protocol_version || !r.protocol_acknowledged) throw new Error('Protocol not acknowledged');
    const input=JSON.parse(await fs.readFile(path.join(dir,`agent-${coder}`,'待评材料.json'),'utf8'));
    if(r.records.length!==18 || new Set(r.records.map(x=>x.id)).size!==18) throw new Error('Invalid record count');
    const records=new Map(r.records.map(x=>[x.id,x]));
    const rows=input.rows.map(x=>{
      const item=records.get(x.id);
      if(!item || dims.some(d=>![0,1,'待定'].includes(item.labels[d])) || !item.evidence || !item.material_issue || !item.rationale)throw new Error('Invalid record '+x.id);
      const allowed=['无','上下文不足','断词或乱码','标题或碎片','其他'];
      const issue=allowed.includes(item.material_issue)?item.material_issue:/语境|上下文/.test(item.material_issue)?'上下文不足':/断词|乱码/.test(item.material_issue)?'断词或乱码':/标题|碎片/.test(item.material_issue)?'标题或碎片':'其他';
      const reason=issue===item.material_issue?item.rationale:`材料问题原述：${item.material_issue}\n${item.rationale}`;
      return [...dims.map(d=>item.labels[d]),item.evidence,issue,reason];
    });
    const w=await SpreadsheetFile.importXlsx(await FileBlob.load(path.join(dir,`agent-${coder}`,`校准试填-${coder}.xlsx`)));
    const s=w.worksheets.getItem('独立试填');
    s.getRange('C6:J23').values=rows;
    s.getRange('A1').values=[[`AI专家agent ${coder}｜18条独立盲评结果`]];
    s.getRange('A2').values=[[`共用定义${binding.protocol_version}。1=涉及，0=不涉及，待定=无法可靠判断。完成：${r.completed_at}`]];
    // Expand only newly populated narrative columns to make evidence and reasons readable.
    s.getRange('H5:H23').format.columnWidth=32;
    s.getRange('J5:J23').format.columnWidth=52;
    for(let i=0;i<rows.length;i++){
      const textLines=(v,n)=>String(v).split('\n').reduce((sum,line)=>sum+Math.max(1,Math.ceil([...line].reduce((l,ch)=>l+(ch.charCodeAt(0)>255?1:0.55),0)/n)),0);
      const maxLines=Math.max(textLines(input.rows[i].text,34),textLines(rows[i][5],20),textLines(rows[i][6],8),textLines(rows[i][7],32));
      s.getRange(`A${i+6}:J${i+6}`).format.rowHeight=Math.min(409,Math.max(84,maxLines*15+14));
    }
    const manual=w.worksheets.getItem('编码手册');
    const appendix=[`本轮共用执行说明 ${binding.protocol_version}`,`共同协议SHA-256：${binding.common_protocol_sha256}`,...note.map(x=>x.replaceAll('**',''))];
    appendix.forEach((txt,i)=>{
      const row=60+i;
      manual.getRange(`A${row}`).copyFrom(manual.getRange(i===0?'A3':'A4'),'all');
      manual.getRange(`A${row}`).values=[[txt]];
      manual.getRange(`A${row}`).format.wrapText=true;
      manual.getRange(`A${row}`).format.verticalAlignment='top';
      manual.getRange(`A${row}`).format.rowHeight=Math.max(30,Math.ceil([...txt].length/65)*15+14);
    });
    w.recalculate();
    const check=await w.inspect({kind:'table',range:'独立试填!C6:J23',include:'values,formulas',tableMaxRows:18,tableMaxCols:8,maxChars:30000});
    await fs.writeFile(path.join(dir,`inspection-${coder}.ndjson`),check.ndjson);
    const errors=await w.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'formula error check',maxChars:1500});
    console.log(coder,errors.ndjson);
    const output=path.join(dir,`校准盲评-${coder}-AI专家.xlsx`);
    await (await SpreadsheetFile.exportXlsx(w)).save(output);
    for(const [name,range] of [['top','A1:J8'],['middle','A12:J15'],['end','A20:J23']]){
      const b=await w.render({sheetName:'独立试填',range,scale:1,format:'png'});
      await fs.writeFile(path.join(dir,`review-${coder}-${name}.png`),new Uint8Array(await b.arrayBuffer()));
    }
    if(coder==='A'){
      const b=await w.render({sheetName:'编码手册',range:'A60:A68',scale:1,format:'png'});
      await fs.writeFile(path.join(dir,'shared-manual-appendix.png'),new Uint8Array(await b.arrayBuffer()));
    }
    console.log(JSON.stringify({coder,output,records:r.records.length}));
  }
}
