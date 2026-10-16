"""Untouched statistics() excerpt from the independently audited batch adapter."""
from fractions import Fraction
from vendor import stability_engine as math_engine
DIMS, PAIRS = math_engine.DIMS, math_engine.PAIRS

def statistics(reg, meta, selected, firsts):
    """Reuse the untouched audited single-record mathematics with origin pointers."""
    pairs = {}
    for a, b in PAIRS:
        pair = {"runs": [a, b], "orientation": "first run rows, second run columns; neither side is truth", "dimensions": {}}
        for dim in DIMS:
            domain = math_engine.domain_accounting((a, b), selected, meta, dim)
            counts = dict.fromkeys(("n00", "n01", "n10", "n11"), 0)
            weighted = {k: Fraction(0) for k in counts}
            changes = []
            for i in domain["joint_comparable_assignedIDs"]:
                x, y = selected[a][i]["labels"][dim], selected[b][i]["labels"][dim]
                counts[f"n{x}{y}"] += 1
                weighted[f"n{x}{y}"] += meta["weights"][i]
                if x != y:
                    changes.append({"assignedID": i, "first_label": x, "second_label": y, "first_origin": firsts[a][i], "second_origin": firsts[b][i]})
            pair["dimensions"][dim] = {"domain": domain, "raw": math_engine.table_metrics(counts), "weighted": math_engine.table_metrics(weighted), "label_changes": changes, "weight_kind": reg["sample"]["weight_kind"]}
        pair["five_dimension_vector"] = math_engine.agreement_summary((a, b), selected, meta)
        pair["semantic_null_patterns"] = math_engine.null_patterns((a, b), selected, meta)
        pair["q"] = math_engine.q_group((a, b), selected, meta, reg["sample"]["weight_kind"])
        pairs[f"{a}/{b}"] = pair
    main = ("R1", "R2", "R3")
    triple = {"runs": list(main), "five_dimension_vector": math_engine.agreement_summary(main, selected, meta), "by_dimension": {d: math_engine.agreement_summary(main, selected, meta, d) for d in DIMS}, "semantic_null_patterns": math_engine.null_patterns(main, selected, meta), "q": math_engine.q_group(main, selected, meta, reg["sample"]["weight_kind"])}
    return pairs, triple

