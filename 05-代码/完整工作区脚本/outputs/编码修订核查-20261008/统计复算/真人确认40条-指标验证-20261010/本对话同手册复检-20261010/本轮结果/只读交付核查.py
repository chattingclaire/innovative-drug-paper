from pathlib import Path
import json,hashlib,openpyxl,datetime
base=Path(__file__).resolve().parent.parent
p=base/"本轮结果/40条编码核查结果.xlsx"
d=json.loads((base/"本轮结果/结果数据.json").read_text())
f=openpyxl.load_workbook(p,read_only=True,data_only=True)
sheet=f["指标结果"]
count=0
for i,m in enumerate(d["metrics"]):
    row=7+i if i<10 else 21+(i-10)
    ex=[m["kappa"],m["precision"],m["recall"],m["F1"]]
    for col,x in enumerate(ex,4):
        v=sheet.cell(row,col).value
        assert (v=="NA" if x is None else isinstance(v,(float,int)) and abs(v-x)<1e-11),(row,col,x,v)
        count+=1
    for col,x in enumerate([m["n_valid"],m["TP"],m["FP"],m["FN"],m["TN"],m["reference_positive"],m["prediction_positive"]],10):
        assert sheet.cell(row,col).value==x
        count+=1
    assert sheet.cell(row,8).value==m["project_target_status"]
source=f["逐项对照"]
assert source.cell(86,6).value==0 and source.cell(86,7).value==0 and source.cell(86,8).value==1
sources=[]
for row in f["阅读材料"].iter_rows(min_row=2,values_only=True):
    if row[0] is not None:sources.append(row)
units={u["material_id"]:u for i in range(1,5) for u in json.loads((base/f"无答案输入/批次{i:02d}.json").read_text())["units"]}
grouped={}
for row in sources:
    k=(row[0],row[1],row[2])
    grouped.setdefault(k,[]).append((row[3],row[5]))
for (mid,kind,index),parts in grouped.items():
    reconstructed="".join(x[1] for x in sorted(parts))
    actual=units[mid]["current_text"] if kind=="当前句段" else units[mid]["contexts"][index-1]
    assert reconstructed==actual
f.close()
review=base.parent.parent.parent/"人工参照复核/手册校准准备-20261010/代理试填-20261010/复核反馈处理-20261010"
raw_review={}
expected={"A":"2cc237a05b9324525560d87d997a2b110fc4b34b3a749b5bd3b0a00b8f4a26fa","B":"044f3d68bd0cfc7fd90f552326762b8f17bc36d70ad23f2ee586c0c8f5274ad7"}
for arm,h in expected.items():
    q=review/f"校准复核工作表-{arm}.xlsx"
    actual=hashlib.sha256(q.read_bytes()).hexdigest()
    assert actual==h
    raw_review[arm]={"path":str(q.resolve()),"sha256":actual,"preserved":True}
r={"checked_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"workbook":str(p.resolve()),"workbook_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"saved_cached_metric_and_count_cells_verified":count,"metric_rows":40,"saved_source_groups_reconstructed_exactly":len(grouped),"saved_reading_rows":len(sources),"original_A_B_workbooks":raw_review,"17_original_A_B_zero_adjudicated_reference_one":True,"independent_population_validation_completed":False,"other_chat77_used":False}
(base/"本轮结果/交付核查记录.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in r.items() if k!="original_A_B_workbooks"},ensure_ascii=False))
