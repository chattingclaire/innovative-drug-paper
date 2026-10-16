"""Seal the finite workbook delivery after independent mechanical read-back."""
from pathlib import Path
import datetime, hashlib, json

OUT = Path(__file__).resolve().parents[1]
H = lambda raw: hashlib.sha256(raw).hexdigest()
def cj(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'absolute_path': str(p), 'bytes': len(raw), 'sha256': H(raw)}
def put(name, text):
    with (OUT / name).open('xb') as handle: handle.write(text.encode())
    (OUT / name).chmod(0o600)

assert not (OUT / 'seal.json').exists()
checks = json.loads((OUT / 'mechanical-readback.json').read_bytes())
manifest = json.loads((OUT / 'workbook-manifest.json').read_bytes())
assert checks['all_material_pages_opened_N'] == 1600 and checks['blank_dimension_input_slots_N'] == 8000
dependency_link = OUT / '_build/node_modules'
if dependency_link.is_symlink(): dependency_link.unlink()
put('README.md', '''正式800真人填写表的pre-release交付。A/B各自目录有一份XLSX、候选手册原文、填写说明、共享资产索引及800个盲号材料页和原始JSON。

每份表仅A盲号、B条款正文、C维度、D值、E理由五列，4000行五维。A列盲号链接本方完整材料页，B列原条款正文逐字保留。D空白待独立填0/1，E空白待填理由；证据不足留空并写待定原因与补材，不能缺材填0。表头及盲号列冻结，D列设0/1验证且允许待定空白。没有真人复核栏、机器答案、分层/曝光/权重字段或任何真实判读。

分别给A/B本方coder目录和同一个shared-source，放在同一个包根目录，不改变相对路径。材料页显示完整body/context和全部源束字符串、完整补充资源，保留原始源束JSON链接。图片、PDF和来源文件是shared-source/source-files中的实际同SHA副本，source-assets-index.json提供真实路径。不要给一方另一方目录。

候选pre-release。ROOT开发结果和联合freeze完成前，不分发正式判读。发布后五维独立判读，不能看另一方或机器/Gold，不请求AI代填。保存原始独立初判后再补材重判或裁定，保留初判版本。
''')
put('report.md', f'''已制作两份真人空白填写XLSX，交付状态pre-release，release尚未完成。每份800个原blind按各自原packet顺序展开成4000行S/E/Ec/I/F，仅A-E五列；D/E均为真正空白，没有真人复核栏或任何编码标签。当前正文最长1053字符，全部逐字放B，未裁正文。

完整v15材料以本方800个HTML页及800份原始源束JSON保存，每页机械escape全部来源字符串并保留body/context和完整补充资源，JSON原SHA/字节保持不变。最大源束234966字节，完整放在外部材料页，不受Excel单元格限制。共同shared-source带158个实际同SHA来源资产，图片/PDF有明确本地链接。

独立有限读回确认：800唯一blind×5，A/B原顺序一致，D共8000空槽、E共8000空槽；1600材料页全部以UTF8打开，{checks['all_literal_source_string_fields_compared_N']}个字符串字段逐字比较，{checks['local_material_and_asset_links_opened_N']}个本地链接目标均实际可读；原source-seal及184个member不变，167个绑定输入未变。保存的OOXML确认冻结表头/盲号列、0/1验证允许空白且拒绝其他值、每方4000个原生材料超链接。artifact-tool创建表、执行读回与render；顶端和最长条文视图已目视核查，正文和列头可读。

artifact-tool的HYPERLINK计算未实现，因此A列使用真实blind字符串，导出后有限补入标准原生XLSX超链接关系和验证错误控制；独立OOXML读回核对这些关系及实际文件。未进行Excel客户端点击测试；文件读取与路径核对不冒称客户端行为或真实阅读记录。已封存新输入输出，未改此前已sealed的来源包。

下一条件：ROOT最后开发结果、联合freeze及正式独立分发确认。不能据本次材料和空表准备声称已经启动、完成或取得真人编码。原始独立初判保存后，再组织补材及裁定。
''')
members = [dict(path=str(p.relative_to(OUT)), **bind(p)) for p in sorted(OUT.rglob('*')) if p.is_file()]
seal = {'version': 'formal800-human-workbooks-v15-prerelease-1',
    'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'pre_release',
    'workbook_N': 2, 'rows_per_workbook': 4000, 'material_HTML_page_N': 1600, 'raw_source_JSON_N': 1600,
    'shared_source_asset_N': 158, 'human_or_AI_labels_created_N': 0, 'human_review_columns_added_N': 0,
    'final_release_freeze_completed': False, 'coding_released': False,
    'input_N': len(manifest['input_bindings']), 'input_bindings': manifest['input_bindings'],
    'original_source_seal': manifest['source_package_seal'], 'original_source_members_unchanged_N': 184,
    'members_N': len(members), 'members': members, 'member_table_sha256': H(cj(members)),
    'self_hash_policy': 'seal.json excluded from own member table; all other output files included',
    'prior_sealed_source_package_modified': False}
put('seal.json', json.dumps(seal, ensure_ascii=False, indent=2) + '\n')
assert H(cj(seal['members'])) == seal['member_table_sha256']
for member in seal['members']: assert bind(member['absolute_path']) == {k: member[k] for k in ('absolute_path', 'bytes', 'sha256')}
for original in seal['input_bindings']: assert bind(original['absolute_path']) == original
assert bind(seal['original_source_seal']['absolute_path']) == seal['original_source_seal']
print(json.dumps({'status': 'pre_release_delivery_sealed', 'members_N': len(members), 'input_N': seal['input_N'],
    'seal_sha256': H((OUT / 'seal.json').read_bytes()), 'final_release_freeze_completed': False}, ensure_ascii=False))
