import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const out=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(out,'../..');
const files=['三部门编码指标.json','三部门注意力分布与敏感性.json','llm-v29/stability_comparison_v2.json'];
const raw=await Promise.all(files.map(name=>fs.readFile(path.join(out,name),'utf8')));
const [coding,attention,stability]=raw.map(JSON.parse);
const sha=x=>createHash('sha256').update(x).digest('hex');
const sources=Object.fromEntries(files.map((name,i)=>[name,sha(raw[i])]));
if(coding.population_n!==4481 || attention.population_n!==4481) throw Error('Unexpected department population');
for(const [key,value] of Object.entries(coding.source_sha256||{})) {
  if(attention.source_sha256?.[key] && attention.source_sha256[key]!==value) throw Error(`Different shared source versions: ${key}`);
}
const dims=['S','E','Ec','I','F'];
const names={S:'安全性S',E:'有效性E',Ec:'经济性Ec',I:'创新性I',F:'公平性F'};
const groups=['ALL','NMPA','NHSA','NHC'];
const groupsCN={ALL:'三部门合计',NMPA:'药监NMPA',NHSA:'医保NHSA',NHC:'卫健NHC'};
const actualMethods=[...new Set(coding.records.map(x=>x.method))];
const ruleMethods=actualMethods.filter(x=>/^rule/i.test(x));
const llmMethods=actualMethods.filter(x=>/^llm/i.test(x));
const latestRule=ruleMethods.at(-1);
const latestLLM=llmMethods.at(-1);
if(!latestRule) throw Error('Missing actual rule classification metrics');
const wb=Workbook.create();
const sheets=Object.fromEntries(['κ对照','完整分类指标','注意力分布','稳健性结果','方法与来源','LLM稳定性'].map(name=>[name,wb.worksheets.add(name)]));
const palette={ink:'#203348',navy:'#274461',light:'#EEF2F6',muted:'#58697B',amber:'#FFF2CC'};
const col=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const value=x=>typeof x==='object'&&x!==null&&'value'in x?x.value:x;
function setup(sheet,lastCol,lastRow,title){
  const range=sheet.getRange(`A1:${lastCol}${lastRow}`);
  range.format.font={name:'Arial',size:10,color:palette.ink};
  range.format.rowHeight=21;
  range.format.columnWidth=13;
  range.format.verticalAlignment='center';
  sheet.showGridLines=false;
  sheet.getRange('A2').values=[[title]];
  sheet.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:palette.ink};
  sheet.getRange(`A3:${lastCol}3`).format.borders={bottom:{style:'thin',color:palette.navy}};
}
function header(sheet,row,labels){
  const r=sheet.getRange(`A${row}:${col(labels.length)}${row}`);r.values=[labels];
  r.format.fill=palette.navy;r.format.font={name:'Arial',size:10,bold:true,color:'#FFFFFF'};
  r.format.horizontalAlignment='center';r.format.wrapText=true;r.format.rowHeight=34;
  r.format.borders={insideVertical:{style:'thin',color:'#FFFFFF'}};
}
function writeTable(sheet,row,rows){
  if(!rows.length)return;
  sheet.getRange(`A${row}:${col(rows[0].length)}${row+rows.length-1}`).values=rows;
}
function note(sheet,cell,text){sheet.getRange(cell).values=[[text]];sheet.getRange(cell).format.font={name:'Arial',size:10,color:palette.muted,italic:true};}
const expected=[];
function expect(sheet,cell,v){expected.push({sheet,cell,expected:v});}
const isMissing=x=>x===null||x===undefined;
function compare(actual,wanted,label){
  if(isMissing(wanted)){if(![null,undefined,'','NA'].includes(actual))throw Error(`${label}: expected unavailable, got ${actual}`);}
  else if(typeof wanted==='number'){if(typeof actual!=='number'||Math.abs(actual-wanted)>1e-10)throw Error(`${label}: ${actual} != ${wanted}`);}
  else if(actual!==wanted)throw Error(`${label}: ${actual} != ${wanted}`);
}

// Own all classification calculations here; summary sheets link to these cells.
const records=[...coding.records];
if(!latestLLM){
  for(const frame of Object.keys(coding.frame_n))for(const group of groups)for(const dimension of dims)for(const reference of ['A','C']){
    records.push({frame,group,dimension,method:'LLM（未完成）',reference,pending:true});
  }
}
const full=sheets['完整分类指标'];
setup(full,'BH',records.length+6,'三部门逐维分类指标');
note(full,'A4','四格列对A—C表示A1C1、A1C0、A0C1、A0C0；对机器—参照依次表示TP、FP、FN、TN。A—C不设置准确性金标准。');
const headers=['样本框','部门','维度','方法版本','参照','状态','框内n','原数据配对n','排除n','左侧待定','右侧待定','双方待定','文件聚类数',
  '1/1或TP','1/0或FP','0/1或FN','0/0或TN','配对n（公式）','左侧正类n','右侧正类n','左侧正类比','右侧正类比','机会一致p_e','观察一致率','Cohen κ','Precision','Recall','F1',
  ...['一致率','κ','Precision','Recall','F1','左正类比','右正类比'].flatMap(x=>[x+'下界',x+'上界',x+'有效重复',x+'未定义重复']),
  '有配对文件数','来源条目数','统计身份'];
header(full,6,headers);
const recordRows=new Map();
const metricOrder=['agreement','kappa','precision','recall','f1','left_positive_rate','right_positive_rate'];
const rows=records.map((r,i)=>{
  const row=i+7;
  recordRows.set([r.frame,r.group,r.dimension,r.method,r.reference].join('|'),row);
  const four=r.cross_tab?Object.values(r.cross_tab):r.confusion?['TP','FP','FN','TN'].map(k=>r.confusion[k]):[null,null,null,null];
  const vals=[r.frame,groupsCN[r.group]||r.group,names[r.dimension],r.method,r.reference,r.pending?'未完成':'已完成',r.frame_n??null,r.n??null,r.excluded_n??null,
    r.exclusions?.left_pending_only??null,r.exclusions?.right_pending_only??null,r.exclusions?.both_pending??null,r.source_clusters??null,
    ...four,...Array(11).fill(null)];
  for(const metric of metricOrder){const ci=r.metrics?.[metric]?.ci95;vals.push(ci?.low??null,ci?.high??null,ci?.defined_repetitions??null,ci?.undefined_repetitions??null);}
  vals.push(r.paired_source_clusters??null,r.source_entry_clusters??null,r.method==='A_C'?'两AI编码员对称一致':r.pending?'实际全量尚未完成':'机器相对原AI参照');
  if(!r.pending){
    for(const [metric,c]of Object.entries({kappa:'Y',agreement:'X',precision:'Z',recall:'AA',f1:'AB',left_positive_rate:'U',right_positive_rate:'V'}))expect(full.name,`${c}${row}`,r.metrics?.[metric]?.estimate??null);
    expect(full.name,`R${row}`,r.n);
  }
  return vals;
});
writeTable(full,7,rows);
const formulas=records.map((r,i)=>{
  const n=i+7,guard=f=>`=IF(F${n}="未完成","",${f})`,ratio=(num,den)=>`IF(${den}=0,"NA",(${num})/(${den}))`;
  return [guard(`SUM(N${n}:Q${n})`),guard(`N${n}+O${n}`),guard(`N${n}+P${n}`),guard(ratio(`S${n}`,`R${n}`)),guard(ratio(`T${n}`,`R${n}`)),
    guard(`IF(R${n}=0,"NA",(S${n}*T${n}+(R${n}-S${n})*(R${n}-T${n}))/R${n}^2)`),
    guard(ratio(`N${n}+Q${n}`,`R${n}`)),guard(`IF(R${n}=0,"NA",IF(W${n}=1,"NA",(X${n}-W${n})/(1-W${n})))`),
    r.method==='A_C'?'=""':guard(ratio(`N${n}`,`N${n}+O${n}`)),r.method==='A_C'?'=""':guard(ratio(`N${n}`,`N${n}+P${n}`)),
    r.method==='A_C'?'=""':guard(ratio(`2*N${n}`,`2*N${n}+O${n}+P${n}`))];
});
full.getRange(`R7:AB${records.length+6}`).formulas=formulas;
full.getRange(`G7:T${records.length+6}`).setNumberFormat('#,##0');
full.getRange(`U7:V${records.length+6}`).setNumberFormat('0.00%');
full.getRange(`W7:AB${records.length+6}`).setNumberFormat('0.0000');
for(let i=0;i<7;i++){
  const c=29+i*4;
  full.getRange(`${col(c)}7:${col(c+1)}${records.length+6}`).setNumberFormat('0.0000');
  full.getRange(`${col(c+2)}7:${col(c+3)}${records.length+6}`).setNumberFormat('#,##0');
}
full.getRange('A:A').format.columnWidth=22;full.getRange('B:C').format.columnWidth=17;full.getRange('D:D').format.columnWidth=30;
full.getRange('BG:BG').format.columnWidth=30;
full.freezePanes.freezeRows(6);full.freezePanes.freezeColumns(3);
full.tables.add(`A6:BG${records.length+6}`,true,'CodingMetrics');

const summary=sheets['κ对照'];setup(summary,'G',55,'三部门编码一致性');
summary.getRange('A:A').format.columnWidth=18;summary.getRange('B:F').format.columnWidth=18;
note(summary,'A4',`主参照1057条。规则：${latestRule}。LLM：${latestLLM||'未完成，数值留空'}。`);
const pairs=[['A—C','A_C','C'],['规则—A',latestRule,'A'],['规则—C',latestRule,'C'],['LLM—A',latestLLM||'LLM（未完成）','A'],['LLM—C',latestLLM||'LLM（未完成）','C']];
for(const [group,start]of [['ALL',6],['NMPA',27],['NHSA',37],['NHC',47]]){
  header(summary,start,[groupsCN[group]+' κ',...pairs.map(x=>x[0])]);
  dims.forEach((d,i)=>{
    const row=start+1+i;summary.getRange(`A${row}`).values=[[names[d]]];
    summary.getRange(`B${row}:F${row}`).formulas=[pairs.map(([,method,ref])=>{const source=recordRows.get(['main1057',group,d,method,ref].join('|'));if(!source)throw Error('Missing summary pair');return `='完整分类指标'!Y${source}`;})];
  });
  summary.getRange(`B${start+1}:F${start+5}`).setNumberFormat('0.0000');
}
header(summary,16,['三部门观察一致率',...pairs.map(x=>x[0])]);
dims.forEach((d,i)=>{const row=17+i;summary.getRange(`A${row}`).values=[[names[d]]];summary.getRange(`B${row}:F${row}`).formulas=[pairs.map(([,method,ref])=>`='完整分类指标'!X${recordRows.get(['main1057','ALL',d,method,ref].join('|'))}`)];});
summary.getRange('B17:F21').setNumberFormat('0.00%');
note(summary,'A23','κ未定义显示NA。A—C只表示两份AI独立首次判读的一致性；机器P/R/F1见完整分类指标。');
summary.tabColor=palette.navy;

const att=sheets['注意力分布'];
const attMethods=Object.keys(attention.primary);
const primaryRules=attMethods.filter(x=>/^rule/i.test(x));
const primaryLLMs=attMethods.filter(x=>/^llm/i.test(x));
const primaryRefs=attMethods.filter(x=>!/^rule|^llm/i.test(x));
if(!primaryRules.includes(latestRule))throw Error('Refresh attention JSON to the same current rule method before building');
if(latestLLM&&!primaryLLMs.includes(latestLLM))throw Error('Refresh attention JSON to the same actual LLM method before building');
const orderedAtt=[...primaryRules,...(primaryLLMs.length?primaryLLMs:['LLM（未完成）']),...primaryRefs];
setup(att,'AD',orderedAtt.length*3+6,'三部门五维注意力分布');
note(att,'A4','规则全量为主描述；A/C为原29层设计权重估计。每维句次除以本部门五维句次合计，跨维可共现。');
header(att,6,['部门','方法版本','状态','实际单元n','权重单元合计','S句次','E句次','Ec句次','I句次','F句次','五维句次分母','S占比','E占比','Ec占比','I占比','F占比','占比合计','待定加权句次','原始已知句次','计数口径',...dims.flatMap(d=>[d+'补全下界',d+'补全上界'])]);
const attRows=[];
for(const group of groups.slice(1))for(const method of orderedAtt){
  const data=attention.primary[method]?.[group],row=7+attRows.length;
  const vals=[groupsCN[group],method,data?'已完成':'未完成',data?.observed_unit_count??null,value(data?.weighted_unit_count)??null,
    ...dims.map(d=>value(data?.dimensions[d]?.weighted_known_hit_count)??null),null,...Array(6).fill(null),
    value(data?.weighted_five_dimension_pending_sum)??null,data?.raw_five_dimension_known_hit_sum??null,/^[AC]_/.test(method)?'按原层N_h/n_h加权':'全量等权计数'];
  for(const d of dims)vals.push(...(data?.dimensions[d]?.pending_completion_descriptive_range||[null,null]).map(value));
  attRows.push(vals);
  if(data){for(let j=0;j<5;j++)expect(att.name,`${col(12+j)}${row}`,value(data.dimensions[dims[j]].attention_share));expect(att.name,`K${row}`,value(data.weighted_five_dimension_known_hit_sum));expect(att.name,`Q${row}`,1);}
}
writeTable(att,7,attRows);
const attFormulas=attRows.map((_,i)=>{const r=i+7;return [`=IF(C${r}="未完成","",SUM(F${r}:J${r}))`,...dims.map((d,j)=>`=IF(C${r}="未完成","",IF(K${r}=0,"NA",${col(6+j)}${r}/K${r}))`),`=IF(C${r}="未完成","",IF(K${r}=0,"NA",SUM(L${r}:P${r})))`];});
att.getRange(`K7:Q${attRows.length+6}`).formulas=attFormulas;
att.getRange(`D7:J${attRows.length+6}`).setNumberFormat('#,##0.00');att.getRange(`K7:K${attRows.length+6}`).setNumberFormat('#,##0.00');
att.getRange(`D7:D${attRows.length+6}`).setNumberFormat('#,##0');
att.getRange(`L7:Q${attRows.length+6}`).setNumberFormat('0.00%');att.getRange(`R7:S${attRows.length+6}`).setNumberFormat('#,##0.00');
att.getRange(`U7:AD${attRows.length+6}`).setNumberFormat('0.00%');
att.getRange('A:A').format.columnWidth=17;att.getRange('B:B').format.columnWidth=28;att.getRange('T:T').format.columnWidth=25;
att.freezePanes.freezeRows(6);att.freezePanes.freezeColumns(2);
att.tables.add(`A6:AD${attRows.length+6}`,true,'AttentionShares');

const sensitivity=sheets['稳健性结果'];
const scenarioNames={policy_file_equal_weight:'来源条目等权',policy_series_equal_weight:'年度系列等权',latest_member_of_annual_series_only:'系列仅最新成员',exclude_all_joint_publications:'剔除联合文本',exclude_quality_only:'排除仅质量安全',exclude_F_clinical_management_only:'排除仅临床管理',F_access_affordability_only:'公平仅获取与负担',exclude_F_dimension_information_only:'排除仅公平信息要求',exclude_I_qualification_advantage_only:'排除仅创新资格优势'};
const sensitivityRows=[];
function addSensitivity(method,scenario,group,data,discarded=''){
  const row=sensitivityRows.length+7;
  const shares=dims.map(d=>value(data?.dimensions?.[d]?.attention_share)??null);
  const vals=[method,scenario,groupsCN[group],data?.known_hit_active_cluster_count??null,...shares,null,discarded,
    data?.observed_unit_count??null,value(data?.weighted_five_dimension_known_hit_sum)??null,
    ...(dims.flatMap(d=>(data?.dimensions?.[d]?.pending_completion_descriptive_range||[null,null]).map(value))),
    (data?.excluded_zero_known_hit_clusters||[]).join('；')];
  sensitivityRows.push(vals);
  shares.forEach((v,j)=>expect(sensitivity.name,`${col(5+j)}${row}`,v));
}
for(const [method,data]of Object.entries(attention.sensitivities||{})){
  for(const [scenario,distribution]of Object.entries(data.scenarios||{}))for(const group of groups.slice(1))if(distribution[group])addSensitivity(method,scenarioNames[scenario]||scenario,group,distribution[group]);
  for(const entry of data.leave_one_policy_file_out||[]){
    const group=groups.slice(1).find(g=>entry.discarded_file.startsWith(g)||entry.discarded_file.startsWith(g==='NMPA'?'CDE-':'UNMATCHED-'));
    if(group&&entry.distribution[group])addSensitivity(method,'逐条目剔除',group,entry.distribution[group],entry.discarded_file);
    else for(const g of groups.slice(1))if(entry.distribution[g])addSensitivity(method,'逐条目剔除',g,entry.distribution[g],entry.discarded_file);
  }
}
setup(sensitivity,'X',sensitivityRows.length+6,'注意力分布的稳健性检验');
note(sensitivity,'A4','补全上下界是待定标签的描述性范围，与分类指标的bootstrap置信区间不同。逐条目剔除列保留实际被剔除条目。');
header(sensitivity,6,['方法版本','情景','部门','有效聚类数',...dims.map(d=>names[d]+'占比'),'占比合计','剔除条目','实际单元n','五维句次分母',...dims.flatMap(d=>[d+'补全下界',d+'补全上界']),'零分母排除条目']);
writeTable(sensitivity,7,sensitivityRows);
sensitivity.getRange(`J7:J${sensitivityRows.length+6}`).formulas=sensitivityRows.map((_,i)=>[`=IF(COUNT(E${i+7}:I${i+7})=5,SUM(E${i+7}:I${i+7}),"NA")`]);
sensitivity.getRange(`E7:J${sensitivityRows.length+6}`).setNumberFormat('0.00%');sensitivity.getRange(`N7:W${sensitivityRows.length+6}`).setNumberFormat('0.00%');
sensitivity.getRange('A:A').format.columnWidth=28;sensitivity.getRange('B:B').format.columnWidth=23;sensitivity.getRange('C:C').format.columnWidth=17;sensitivity.getRange('K:K').format.columnWidth=65;sensitivity.getRange('X:X').format.columnWidth=65;
sensitivity.freezePanes.freezeRows(6);sensitivity.freezePanes.freezeColumns(3);sensitivity.tables.add(`A6:X${sensitivityRows.length+6}`,true,'SensitivityShares');

const method=sheets['方法与来源'];
const sourceRows=[...new Map([...Object.entries(coding.source_sha256||{}),...Object.entries(attention.source_sha256||{})]).entries()];
setup(method,'E',sourceRows.length+46,'指标定义、依据与数据来源');
method.getRange('A:A').format.columnWidth=24;method.getRange('B:B').format.columnWidth=70;method.getRange('C:C').format.columnWidth=65;method.getRange('D:D').format.columnWidth=90;
header(method,6,['指标或材料','定义与职责','原始方法依据','主来源入口']);
writeTable(method,7,[
 ['注意力占比','本维编码句次/同部门五维编码句次合计；同维一次、跨维可共现','文宏2014语境计句；陈星平等2018同维去重、跨维计数','https://doi.org/10.15939/j.jujsse.2014.02.012\nhttps://www.kjjb.org/fileup/1001-7348/HTML/2018-23-155.htm'],
 ['Cohen κ','扣除两侧边际比例决定的机会一致；p_e=1时记NA','Cohen1960；A—C对称一致，不认定一方为真值','https://doi.org/10.1177/001316446002000104'],
 ['观察一致率','(1/1+0/0)/全部共同可判数；同时报告类比例','Cohen1960的一致性框架；与κ共同解释类别失衡','https://doi.org/10.1177/001316446002000104'],
 ['Precision','TP/(TP+FP)，识别机器多判；无预测正类时NA','Kristensen-McLachlan等2025正类P/R/F1报告','https://doi.org/10.1093/pnasnexus/pgaf069'],
 ['Recall','TP/(TP+FN)，识别机器漏判；无参照正类时NA','同上；机器阴性必须包含在配对材料','https://doi.org/10.1093/pnasnexus/pgaf069'],
 ['F1','2TP/(2TP+FP+FN)；平衡多判与漏判，分母0时NA','同上；逐维正类F1，不作加权多类F1替代','https://doi.org/10.1093/pnasnexus/pgaf069'],
 ['领域词典与语境规则','按药品对象、命题关系、纳排条件及否定处理','Loughran与McDonald2011；Grimmer与Stewart2013','https://doi.org/10.1111/j.1540-6261.2010.01625.x\nhttps://doi.org/10.1093/pan/mps028'],
 ['LLM代码本判读','完整操作定义、纳排边界、正反例及原文证据','Gilardi等2023；Halterman与Keith2026（2025在线）','https://doi.org/10.1073/pnas.2305016120\nhttps://doi.org/10.1017/pan.2025.10017'],
 ['区间与稀有类','来源文件聚类bootstrap5000次，百分位95%区间；逐指标排除未定义重复','Davison与Hinkley1997；具体聚类层级、次数与种子为本研究实施','https://doi.org/10.1017/CBO9780511802843\n实际defined/undefined重复数见完整分类指标'],
 ['五维内容定义','医保五维作为比较坐标；语义纳排是本研究操作定义','CAL-5D-20260926-v1.3；政策原文与定义对照','指标依据与理论对齐.md'],
 ['A/C身份','两名AI agent按同一规范独立首次判读，原始标签不变','按双编码员标准报告；现有材料已用于方法修订','不称真人标注或新独立验证'],
 ['A/C注意力权重','沿用原29层N_h/n_h；先估计句次，再以五维估计合计求比；不宣称比值无偏','Horvitz与Thompson1952估计总量；三部门域1057：436/394/227','https://doi.org/10.1080/01621459.1952.10483446\n分类指标在共同可判集等权，不借用此设计权重'],
 ['统计范围','三部门4481单元、51条目；中央443单元仅作背景','药监1848、医保2100、卫健533','主参照1057；补充H411单列'],
 ['内容效度','政策原文—概念—纳排—证据的对照，尚无独立真人评分','国内原始论文提供专家检查方法先例','不填造CVI、专家轮次或真人信效度数值'],
 ['更新方式','先更新两份指标JSON，再运行同一builder覆盖本工作簿','方法版本由输入读取；完整LLM未完成时留空','点估计使用公式；CI及待定补全范围来自实际输出'],
]);
method.getRange('A7:D21').format.wrapText=true;method.getRange('A7:D21').format.rowHeight=43;
writeTable(method,22,[['LLM重复与提示稳定性','同提示同36条整批重复、维度顺序扰动分别报告；生产25条分批对照单列为批次组成差异','Törnberg2024第4、7、9节；36条与维度顺序扰动为本文实施设计，二元κ依据Cohen1960','https://doi.org/10.6092/issn.1971-8853/19461\nhttps://sociologica.unibo.it/article/download/19461/18662?inline=1']]);
method.getRange('A22:D22').format.wrapText=true;method.getRange('A22:D22').format.rowHeight=62;
header(method,24,['输入文件','实际状态','SHA256','说明']);
writeTable(method,25,files.map((name,i)=>[name,i===2?'36条稳定性已完成':i===0?(latestLLM?'含实际LLM':'LLM未完成'):(primaryLLMs.length?'含实际LLM':'LLM未完成'),sources[name],i===2?'严格重复、维度顺序扰动、批次组成改变分开报告；不替代真人验证':i===0?coding.reference_identity:attention.A_C_weighting]));
method.getRange('D25:D27').format.wrapText=true;method.getRange('A25:D27').format.rowHeight=40;
method.getRange('A27:D27').format.wrapText=true;method.getRange('A27:D27').format.rowHeight=55;
header(method,29,['源记录','SHA256','来源类别','']);
writeTable(method,30,sourceRows.map(([name,digest])=>[path.basename(name),digest,'原始输入／实际输出或复跑脚本',path.relative(root,name)]));
method.getRange('A30:A'+(sourceRows.length+29)).format.wrapText=true;
method.getRange('D30:D'+(sourceRows.length+29)).format.wrapText=true;
method.getRange('A30:D'+(sourceRows.length+29)).format.rowHeight=34;
method.freezePanes.freezeRows(6);method.tabColor='#8392A1';

// Stability is a separate repeated-model check. Reconstruct four cells from the
// frozen raw outputs and match the existing comparison JSON without relabeling.
const stab=sheets['LLM稳定性'];setup(stab,'J',52,'LLM重复及提示稳定性：36条冻结材料');
for(const [c,w]of [['A',34],['B',20],['C',9],['D',13],['E',13],['F',13],['G',13],['H',15],['I',15],['J',36]])stab.getRange(`${c}:${c}`).format.columnWidth=w;
stab.mergeCells('A4:J4');note(stab,'A4','三种比较分开报告；每种均36条。模型重复稳定性不等于真人效度，未按一致率挑选重跑结果。');
const comparisonNames={
 strict_same_prompt_same_36_row_batch_repeat:'同提示、同36条整批严格重复',
 equivalent_prompt_dimension_order_perturbation_same_36_row_batch:'同36条整批的维度顺序扰动',
 batch_composition_changed_recoding_difference_not_strict_repeat:'生产25条分批 vs 36条整批（非严格重复）',
};
const runNames={production_25_batch:'生产25条分批',same_repeat_1_36_batch:'同提示36条第1次',same_repeat_2_36_batch:'同提示36条第2次',dimension_order_repeat_36_batch:'维度顺序扰动36条'};
const bindingPaths={
 production_25_batch:'llm-v29/production-25-v29/all_predictions.jsonl',
 same_repeat_1_36_batch:'llm-v29/stability-v2/same-repeat/raw_output.json',
 same_repeat_2_36_batch:'llm-v29/stability-v2/same-repeat-2/raw_output.json',
 dimension_order_repeat_36_batch:'llm-v29/stability-v2/dimension-order-repeat/raw_output.json',
};
const sampleFile='llm-v29/stability_sample_36_v2.json';
const sampleRaw=await fs.readFile(path.join(out,sampleFile),'utf8');
if(sha(sampleRaw)!==stability.sample_sha256)throw Error('Stability sample binding changed');
const sample=JSON.parse(sampleRaw).rows,ids=sample.map(x=>x.id);
if(ids.length!==36||stability.n!==36||stability.comparisons.length!==3)throw Error('Unexpected stability design');
const rawRuns={};
for(const [key,name]of Object.entries(bindingPaths)){
 const content=await fs.readFile(path.join(out,name),'utf8');
 if(sha(content)!==stability.output_bindings[key])throw Error(`Stability output binding changed: ${key}`);
 const data=name.endsWith('.jsonl')?content.trim().split('\n').map(JSON.parse):JSON.parse(content).rows;
 rawRuns[key]=new Map(data.map(x=>[x.id,x]));
}
header(stab,6,['比较身份','n','整组相同数','整组一致率','比较批次与分歧','','','','','']);stab.mergeCells('E6:J6');
const detailRows=[],disagreementRows=[];
for(const [i,c]of stability.comparisons.entries()){
 const a=rawRuns[c.left],b=rawRuns[c.right],name=comparisonNames[c.comparison_identity];
 if(!name)throw Error('Unknown stability comparison');
 const allCorrect=ids.filter(id=>dims.every(d=>a.get(id).labels[d]===b.get(id).labels[d])).length;
 compare(allCorrect/36,c.all_five_labels_exact_agreement,'All-five stability');
 const r=7+i;writeTable(stab,r,[[name,36,allCorrect,null,`${runNames[c.left]} → ${runNames[c.right]}；分歧：${c.disagreements.map(x=>x.id+' '+x.dimension).join('；')||'无'}`]]);
 stab.mergeCells(`E${r}:J${r}`);stab.getRange(`D${r}`).formulas=[[`=C${r}/B${r}`]];
 stab.getRange(`A${r}:J${r}`).format.wrapText=true;stab.getRange(`A${r}:J${r}`).format.rowHeight=43;
 expect(stab.name,`B${r}`,36);expect(stab.name,`C${r}`,allCorrect);expect(stab.name,`D${r}`,c.all_five_labels_exact_agreement);
 for(const d of dims){
  const counts=[0,0,0,0],bad=[];
  for(const id of ids){const left=a.get(id)?.labels[d],right=b.get(id)?.labels[d];if(![0,1].includes(left)||![0,1].includes(right))throw Error('Nonbinary stability label');counts[left===1?(right===1?0:1):(right===1?2:3)]++;if(left!==right)bad.push(id);}
  if(JSON.stringify(bad)!==JSON.stringify(c.per_dimension[d].disagreement_ids))throw Error('Stability disagreement mismatch');
  const row=14+detailRows.length;detailRows.push([name,names[d],null,...counts,null,null,bad.join('；')||'无']);
  const agreement=(counts[0]+counts[3])/36,peNumerator=(counts[0]+counts[1])*(counts[0]+counts[2])+(counts[2]+counts[3])*(counts[1]+counts[3]);
  const kappa=peNumerator===36*36?null:((counts[0]+counts[3])*36-peNumerator)/(36*36-peNumerator);
  compare(agreement,c.per_dimension[d].agreement,'Stability agreement');compare(kappa,c.per_dimension[d].kappa,'Stability kappa');
  expect(stab.name,`C${row}`,36);for(let k=0;k<4;k++)expect(stab.name,`${col(4+k)}${row}`,counts[k]);
  expect(stab.name,`H${row}`,agreement);expect(stab.name,`I${row}`,kappa);
 }
 for(const d of c.disagreements)disagreementRows.push([name,d.id,null,d.dimension,d.left,d.right,d.text]);
}
stab.getRange('D7:D9').setNumberFormat('0.00%');
header(stab,13,['比较身份','维度','n','1/1','1/0','0/1','0/0','逐维一致率','逐维Cohen κ','分歧ID']);
writeTable(stab,14,detailRows);
for(let i=0;i<detailRows.length;i++){
 const r=14+i,pe=`((D${r}+E${r})*(D${r}+F${r})+(F${r}+G${r})*(E${r}+G${r}))`;
 stab.getRange(`C${r}`).formulas=[[`=SUM(D${r}:G${r})`]];
 stab.getRange(`H${r}:I${r}`).formulas=[[`=IF(C${r}=0,"NA",(D${r}+G${r})/C${r})`,`=IF(C${r}^2=${pe},"NA",((D${r}+G${r})*C${r}-${pe})/(C${r}^2-${pe}))`]];
}
stab.getRange('A14:J28').format.wrapText=true;stab.getRange('A14:J28').format.rowHeight=37;
stab.getRange('H14:H28').setNumberFormat('0.00%');stab.getRange('I14:I28').setNumberFormat('0.0000');
header(stab,32,['冻结记录','相对路径','','SHA256','','','','','','']);stab.mergeCells('B32:C32');stab.mergeCells('D32:J32');
const stableBindings=[['稳定性汇总','llm-v29/stability_comparison_v2.json',sources['llm-v29/stability_comparison_v2.json']],['冻结样本',sampleFile,stability.sample_sha256],...Object.entries(bindingPaths).map(([k,p])=>[runNames[k],p,stability.output_bindings[k]])];
for(const [i,[name,p,digest]]of stableBindings.entries()){
 const r=33+i;stab.getRange(`A${r}`).values=[[name]];stab.mergeCells(`B${r}:C${r}`);stab.getRange(`B${r}`).values=[[p]];stab.mergeCells(`D${r}:J${r}`);stab.getRange(`D${r}`).values=[[digest]];
 stab.getRange(`A${r}:J${r}`).format.wrapText=true;stab.getRange(`A${r}:J${r}`).format.rowHeight=48;
}
header(stab,41,['比较身份','分歧ID','','维度','左标签','右标签','句段原文','','','']);stab.mergeCells('B41:C41');stab.mergeCells('G41:J41');
for(const [i,row]of disagreementRows.entries()){
 const r=42+i;writeTable(stab,r,[row]);stab.mergeCells(`B${r}:C${r}`);stab.mergeCells(`G${r}:J${r}`);stab.getRange(`A${r}:J${r}`).format.wrapText=true;stab.getRange(`A${r}:J${r}`).format.rowHeight=75;
}
stab.mergeCells('A49:J50');note(stab,'A49','依据：Törnberg (2024), Best Practices for Text Annotation with Large Language Models, 第4、7、9节。36条样本、重复设计与顺序扰动是本研究实施；二元κ依据Cohen (1960)。κ无法定义时保留NA，当前15个逐维κ均可定义。');stab.getRange('A49:J50').format.wrapText=true;
stab.freezePanes.freezeRows(6);stab.tabColor='#408A8C';

// Verify that an upstream four-cell change flows through the point formulas,
// then restore every temporary input before final calculation/export.
const testRecord=records.findIndex(r=>!r.pending&&r.method!=='A_C');
const testRow=testRecord+7,testCell=full.getRange(`N${testRow}`),original=testCell.values[0][0];
testCell.values=[[original+1]];
const testFour=full.getRange(`N${testRow}:Q${testRow}`).values[0];
compare(full.getRange(`Z${testRow}`).values[0][0],testFour[0]/(testFour[0]+testFour[1]),'Live Precision input-change check');
testCell.values=[[original]];
wb.recalculate();
for(const e of expected)compare(sheets[e.sheet].getRange(e.cell).values[0][0],e.expected,`${e.sheet}!${e.cell}`);
const errorScan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},maxChars:2500,summary:'Final formula error scan'});
await fs.writeFile(path.join(out,'workbook-formula-scan.ndjson'),errorScan.ndjson);
const inspect=await wb.inspect({kind:'table',range:'κ对照!A6:F11',include:'values,formulas',tableMaxRows:6,tableMaxCols:6,maxChars:2500});
await fs.writeFile(path.join(out,'workbook-summary-inspect.ndjson'),inspect.ndjson);
for(const [name,range,filename]of [
 ['κ对照','A1:F23','workbook-kappa.png'],['完整分类指标','A1:Q18','workbook-classification-counts.png'],
 ['完整分类指标','R6:AH18','workbook-classification-formulas.png'],['注意力分布','A1:Q18','workbook-attention.png'],
 ['稳健性结果','A1:J18','workbook-sensitivity.png'],['方法与来源','A1:D22','workbook-methods.png'],
 ['LLM稳定性','A1:J28','workbook-llm-stability.png'],['LLM稳定性','A30:J50','workbook-llm-stability-bindings.png']]){
 const blob=await wb.render({sheetName:name,range,scale:1.5,format:'png'});await fs.writeFile(path.join(out,filename),new Uint8Array(await blob.arrayBuffer()));
}
for(let i=0;i<files.length;i++)if(sha(await fs.readFile(path.join(out,files[i]),'utf8'))!==sources[files[i]])throw Error('Input changed during workbook build; rerun against complete snapshots');
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(out,'三部门编码与注意力指标.xlsx'));
await fs.writeFile(path.join(out,'workbook-expected-cells.json'),JSON.stringify({source_sha256:sources,expected,classification_records:records.length,actual_classification_records:coding.records.length,attention_rows:attRows.length,sensitivity_rows:sensitivityRows.length,stability_comparisons:3,stability_dimension_rows:detailRows.length,stability_disagreements:disagreementRows.length,latest_rule:latestRule,latest_llm:latestLLM||null,live_input_change_check:true},null,2));
console.log(JSON.stringify({output:'三部门编码与注意力指标.xlsx',actualRecords:coding.records.length,placeholderLLMRows:records.filter(r=>r.pending).length,attentionRows:attRows.length,sensitivityRows:sensitivityRows.length,checkedCells:expected.length,latestRule,latestLLM:latestLLM||'未完成'}));
