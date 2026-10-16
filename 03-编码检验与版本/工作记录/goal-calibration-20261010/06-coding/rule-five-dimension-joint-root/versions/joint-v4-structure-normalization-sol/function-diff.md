v4 相对已封存 v3 有效函数差异：19项（relations 16，dimensions 3），顶层常量改动0。source_packet、source_receipts、evidence原字节不变。

|模块|函数|变化|v3行|v4行|
|---|---|---|---|---|
|relations.py|RelationView._IF_named_feedback_access|modified|1987|2057|
|relations.py|RelationView.__init__|modified|71|87|
|relations.py|RelationView._article_group_pointers|modified|1377|1398|
|relations.py|RelationView._reference_candidates|modified|1264|1286|
|relations.py|RelationView._reference_members|modified|1225|1242|
|relations.py|RelationView._se_article_proof|modified|1715|1736|
|relations.py|RelationView._se_clause_proof|modified|1822|1891|
|relations.py|RelationView._se_operational_references|modified|1847|1916|
|relations.py|RelationView._supplied_address|new|—|1825|
|relations.py|RelationView._supplied_article_number|new|—|1874|
|relations.py|RelationView._supplied_clause_number|modified|1802|1878|
|relations.py|RelationView._supplied_group_article_number|new|—|1882|
|relations.py|RelationView._table_protection_branches|modified|1310|1332|
|relations.py|article_number|new|—|69|
|relations.py|clause_number|modified|59|79|
|relations.py|structure_ordinal|new|—|59|
|dimensions.py|_fairness|modified|710|738|
|dimensions.py|_innovation|modified|606|634|
|dimensions.py|_same_current_RND_comparative_support|new|—|606|

详细有效源码、SHA及统一补丁见 function-diff.json、relations-v3-to-v4.patch、dimensions-v3-to-v4.patch。共享 _add/_units/_generic/judge 有效AST未改。
