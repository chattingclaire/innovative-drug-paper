已补齐742迁移单元的规范TEXTFAM绑定，其中原421条无唯一家族元数据已全部补齐；候选unit_id与paragraph_id来自既有候选JSON。原已知321条家族绑定均保留。

既有固定开发成员并集619条，含迁移开发成员、原33、旧240和已登记62；可推进468条（变化333，未变化135），继续隔离151条。可推进成员分别覆盖原33中的24条、旧240中的182条、已登记62中的37条。重叠成员只计一次。未抽新例；暴露状态仅限已核登记范围。同规范家族的精确文本别名以明确已暴露成员绑定，未冒称该ID直接审读。

具体可推进ID及绑定：

- `RECODE25-00005` → `u00002` / `p0004`；family `TEXTFAM-1256ef7a24ca10a2a454cab42de42617dbea1b1d103c0a304de78977e96adce9`；依赖family 2个。
- `RECODE25-00008` → `u00005` / `p0007`；family `TEXTFAM-0ea749b7286c68f6e3f39852ff52df50389dba79d49025eba97ab24193cec64e`；依赖family 6个。
- `RECODE25-00009` → `u00006` / `p0008`；family `TEXTFAM-d7add769ae3055465073e9d876985631ab6943baec5c4093aa74b522a4e18b24`；依赖family 9个。
- `RECODE25-00012` → `u00010` / `p0011`；family `TEXTFAM-571488c221c35bb7158233f407832901a72f6fd20a75b95d9982ebb02b5e8e1a`；依赖family 8个。
- `RECODE25-00014` → `u00012` / `p0013`；family `TEXTFAM-a8a4c18cb6a0ebc486f8ab1d1d7106e51f36db5276d16785ccde08d53abc431f`；依赖family 8个。
- `RECODE25-00028` → `u00030` / `p0023`；family `TEXTFAM-51d4296fbb1259f37632b9b86511db0728d66395d21380041a0a2fec301e7183`；依赖family 7个。
- `RECODE25-00066` → `u00072` / `p0061`；family `TEXTFAM-ed486e113a00f0d9f5254aeca91bc041967572db5761c27c0c52e5b004ccbc57`；依赖family 6个。
- `RECODE25-00086` → `u00097` / `p0077`；family `TEXTFAM-921bf6b0665e6ccc63c78d46efd5221d28be1a0925e1eafb20442b33c6519792`；依赖family 3个。
- `RECODE25-00088` → `u00099` / `p0080`；family `TEXTFAM-a6dfcaf9ecb977425eb40db1b092d4678158cbfc9b155c90d576c637fb514ccf`；依赖family 3个。
- `RECODE25-00090` → `u00101` / `p0082`；family `TEXTFAM-2bf8ebdd359fc8a81b5fa22c8e257eabaefaf31d4ff94b74f9fd0c4c2bdfea4e`；依赖family 4个。
- `RECODE25-00097` → `u00108` / `p0090`；family `TEXTFAM-bb91699ccc9e9f81d717d5242ef4df7c19c2d90255c7a2ee2e3bc607f1919be1`；依赖family 6个。
- `RECODE25-00098` → `u00109` / `p0090`；family `TEXTFAM-f0c570d42ba4b7163c78bd1766030386922f1bf03691906b505e135dd26ebce5`；依赖family 6个。

字段来源：rule_inputs_shared_v14.jsonl 的 input.candidate_file/candidate_sha256/unit_id；实际候选JSON的 unit_candidates[].paragraph_id、paragraphs[].id；input.llm_v29_shared_context 的实际上下文ID、路径、hash及文字字段仅在内存绑定。全部可推进ID、隔离原因、保护依赖及字段定位见同名JSON。

未打印或序列化保护原文、标签或机器证据；未打开源policyfile或预测文件，冻结文件不改。JSON SHA：`157cd723de676a3009de046bf6bd5b2868bf9a384b384721ab5e82a72d9d810b`。
