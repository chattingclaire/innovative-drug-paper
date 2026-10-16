"""Independent, post-seal comparison with the 41-case AI development reference.

This program never imports a coder. A sealed prediction file is immutable input.
The reference is opened only after its run seal and prediction digest are checked.
All 41 records and all 205 decisions remain visible, including abstentions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from typing import Any


DIMENSIONS = ("S", "E", "Ec", "I", "F")
EXPECTED_RECORDS = 41
EVALUATION_SCOPE = (
    "AI consensus development comparison; not a human reliability estimate, "
    "not independent final validation, and not final acceptance."
)


class EvaluationError(ValueError):
    """Fail closed on an unsealed, changed, malformed, or incomplete input."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationError(message)


def sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def read_jsonl_bytes(payload: bytes, description: str) -> list[dict[str, Any]]:
    rows = []
    for number, line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        require(isinstance(value, dict), f"{description} line {number} is not an object")
        rows.append(value)
    return rows


def seal_value(seal: dict[str, Any], field: str) -> Any:
    """Support explicit flat bindings or a nested prediction binding."""
    if field in seal:
        return seal[field]
    if field.startswith("prediction_"):
        item = seal.get("prediction") or seal.get("predictions")
        if isinstance(item, dict):
            return item.get(field.removeprefix("prediction_"))
    return None


def verify_seal(seal_path: Path, predictions: Path) -> tuple[dict[str, Any], bytes]:
    require(seal_path.is_file(), "Run seal does not exist; reference access is forbidden")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    require(isinstance(seal, dict), "Run seal is not an object")
    status = seal.get("status")
    require(status in {"sealed", "sealed_development_predictions", "sealed_development_run"},
            "Run seal status is not sealed; reference access is forbidden")
    bound_path = seal_value(seal, "prediction_path")
    bound_sha = seal_value(seal, "prediction_sha256")
    require(isinstance(bound_path, str) and Path(bound_path).resolve() == predictions,
            "Prediction path differs from the sealed run")
    require(isinstance(bound_sha, str) and re.fullmatch(r"[0-9a-f]{64}", bound_sha) is not None,
            "Run seal has no valid prediction SHA-256")
    require(predictions.is_file(), "Sealed prediction file does not exist")
    payload = predictions.read_bytes()
    require(sha_bytes(payload) == bound_sha, "Predictions changed after sealing")
    for flag in ("reference_labels_loaded", "reference_loaded"):
        if flag in seal:
            require(seal[flag] is False, "Run seal declares that the runtime loaded reference labels")
    if "no_reference_read" in seal:
        require(seal["no_reference_read"] is True, "Run seal does not affirm no runtime reference access")
    if "decision_n" in seal:
        require(seal["decision_n"] == EXPECTED_RECORDS * len(DIMENSIONS), "Run seal decision count is not 205")
    return seal, payload


def fixture_bindings(fixture: Path, seal: dict[str, Any]) -> dict[str, Any]:
    manifest_path = fixture / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("n") == EXPECTED_RECORDS, "Fixture is not the complete 41-case development set")
    require(manifest.get("dimension_judgments") == EXPECTED_RECORDS * len(DIMENSIONS),
            "Fixture manifest does not declare all 205 decisions")
    outputs = manifest.get("outputs", [])
    require(isinstance(outputs, list), "Fixture output bindings are absent")
    bindings = {}
    for name in ("source.jsonl", "manual.md", "reference.jsonl"):
        path = (fixture / name).resolve()
        items = [item for item in outputs if isinstance(item, dict)
                 and Path(item.get("path", "")).resolve() == path]
        require(len(items) == 1, f"Fixture manifest does not uniquely bind {name}")
        digest = items[0].get("sha256")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
                f"Fixture {name} has no valid SHA-256")
        bindings[name] = {"path": path, "sha256": digest}
    for prefix, name in (("source", "source.jsonl"), ("manual", "manual.md")):
        path_key, hash_key = prefix + "_path", prefix + "_sha256"
        if path_key in seal:
            require(Path(seal[path_key]).resolve() == bindings[name]["path"],
                    f"Run {prefix} path differs from the independent fixture")
        if hash_key in seal:
            require(seal[hash_key] == bindings[name]["sha256"],
                    f"Run {prefix} SHA differs from the independent fixture")
    if "fixture_manifest_path" in seal:
        require(Path(seal["fixture_manifest_path"]).resolve() == manifest_path.resolve(),
                "Run fixture manifest path differs")
    if "fixture_manifest_sha256" in seal:
        require(seal["fixture_manifest_sha256"] == sha_file(manifest_path),
                "Run fixture manifest changed")
    bindings["manifest.json"] = {"path": manifest_path.resolve(), "sha256": sha_file(manifest_path)}
    return bindings


def row_id(row: dict[str, Any]) -> str:
    value = row.get("id", row.get("unit_id"))
    require(isinstance(value, str) and bool(value.strip()), "Record identifier is absent")
    return value


def index_rows(rows: list[dict[str, Any]], description: str) -> dict[str, dict[str, Any]]:
    indexed = {}
    for row in rows:
        identifier = row_id(row)
        require(identifier not in indexed, f"Duplicate {description} identifier: {identifier}")
        indexed[identifier] = row
    require(len(indexed) == EXPECTED_RECORDS, f"{description} must retain all 41 records")
    return indexed


def decision_map(row: dict[str, Any]) -> dict[str, Any]:
    """Adapt label/decision shapes at evaluation time without consulting a coder."""
    candidates = [row]
    for key in ("prediction", "reference", "consensus"):
        if isinstance(row.get(key), dict):
            candidates.append(row[key])
    for candidate in candidates:
        for key in ("decisions", "labels", "consensus_labels"):
            value = candidate.get(key)
            if isinstance(value, dict) and set(DIMENSIONS).issubset(value):
                return {dimension: value[dimension] for dimension in DIMENSIONS}
            if isinstance(value, list):
                mapped = {item.get("dimension"): item for item in value if isinstance(item, dict)}
                if set(DIMENSIONS).issubset(mapped):
                    return {dimension: mapped[dimension] for dimension in DIMENSIONS}
        if set(DIMENSIONS).issubset(candidate):
            return {dimension: candidate[dimension] for dimension in DIMENSIONS}
    raise EvaluationError("Unknown decision shape: expected five labels or five dimension decisions")


def label_value(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("label", "value", "decision"):
            if key in value:
                value = value[key]
                break
        else:
            raise EvaluationError("Dimension decision has no label/value/decision")
    require(value is None or (type(value) is int and value in (0, 1)),
            f"Invalid binary-or-null decision: {value!r}")
    return value


def extract_reason(row: dict[str, Any], dimension: str, decision: Any) -> Any:
    if isinstance(decision, dict):
        for key in ("reason", "reasons", "rationale"):
            if key in decision:
                return decision[key]
    for candidate in (row, row.get("prediction", {}), row.get("reference", {}), row.get("consensus", {})):
        if not isinstance(candidate, dict):
            continue
        for key in ("reasons", "rationales"):
            if isinstance(candidate.get(key), dict):
                return candidate[key].get(dimension)
    return None


def divide(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def binary_metrics(counts: Counter[str], total: int) -> dict[str, Any]:
    tp, fp, fn, tn = (counts[key] for key in ("TP", "FP", "FN", "TN"))
    determined = tp + fp + fn + tn
    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    specificity = divide(tn, tn + fp)
    f1 = divide(2 * tp, 2 * tp + fp + fn)
    balanced = (recall + specificity) / 2 if recall is not None and specificity is not None else None
    observed = divide(tp + tn, determined)
    expected = divide((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp), determined * determined)
    kappa = (observed - expected) / (1 - expected) if observed is not None and expected != 1 else None
    return {
        "confusion_determined": {key: counts[key] for key in ("TP", "FP", "FN", "TN")},
        "all_source_denominator": total,
        "determined_denominator": determined,
        "prediction_null_n": counts["prediction_null"],
        "reference_null_n": counts["reference_null"],
        "null_prediction_reference_positive_n": counts["null_positive"],
        "null_prediction_reference_negative_n": counts["null_negative"],
        "null_coverage": divide(total - counts["prediction_null"], total),
        "coverage": divide(total - counts["prediction_null"], total),
        "prediction_null_rate": divide(counts["prediction_null"], total),
        "paired_determined_coverage": divide(determined, total),
        "precision": precision, "recall": recall, "specificity": specificity,
        "F1": f1, "balanced_accuracy": balanced,
        "determined_accuracy": observed,
        "all_source_correct_rate": divide(tp + tn, total),
        "all_source_unresolved_or_error_n": total - tp - tn,
        "recall_all_reference_positives_with_null_unresolved": divide(tp, tp + fn + counts["null_positive"]),
        "specificity_all_reference_negatives_with_null_unresolved": divide(tn, tn + fp + counts["null_negative"]),
        "cohens_kappa": kappa,
        "kappa_identity": "Agreement with AI consensus development labels; not human inter-coder reliability",
        "metric_denominator_note": (
            "TP/FP/FN/TN and conventional precision/recall/specificity/F1/balanced accuracy/kappa use "
            "binary predictions paired with binary references. All-source correctness, errors and "
            "coverage retain every case; null predictions are unresolved and never disappear. "
            "Undefined denominators, n=0, or kappa expected agreement=1 produce null."
        ),
    }


def count_pair(counts: Counter[str], predicted: int | None, reference: int | None) -> str:
    if predicted is None:
        counts["prediction_null"] += 1
    if reference is None:
        counts["reference_null"] += 1
    if predicted is None or reference is None:
        if predicted is None and reference is not None:
            counts["null_positive" if reference else "null_negative"] += 1
        return "null_unresolved"
    category = { (1, 1): "TP", (1, 0): "FP", (0, 1): "FN", (0, 0): "TN" }[(predicted, reference)]
    counts[category] += 1
    return category


def diagnostic_candidates(dimension: str, source: dict[str, Any], predicted: int | None) -> list[dict[str, str]]:
    """Manual-based review prompts, not automatic replacement labels or tuning."""
    text = source.get("text", "")
    contexts = source.get("contexts", [])
    text += "\n" + "\n".join(item.get("text", "") for item in contexts if isinstance(item, dict))
    candidates = []
    def add(category: str, clause: str, question: str) -> None:
        candidates.append({"category": category, "manual_clause": clause, "review_prompt": question})
    if predicted is None:
        add("MATERIAL_OR_IMPLEMENTATION_ABSTENTION", "§2材料问题与规则争议分开", "核实缺失的是必要来源还是未覆盖语法；保留原未定，不把未知改0。")
    if dimension == "Ec":
        if re.search(r"确认|核验|核对|字段|格式|签章|协议", text):
            add("EC_SUBSTANTIVE_INFORMATION_VS_FORMALITY", "§1资料证据共同门槛；§5经济性边界", "当前核验哪项价格/标准/范围实质内容，还是只处理非空、格式或签约手续？已有信息不因未改变被排除。")
        if re.search(r"支付范围|支付标准|支付责任", text):
            add("EC_CONDITION_AND_PAYMENT_CONSEQUENCE", "§5支付内容的条件与形式操作", "当前与直接父谓词是否组成指定支付内容的授权、限制或条件后果，而非普通目录身份？")
        add("EC_DRUG_TREATMENT_RESOURCE_OBJECT", "§5定义、纳入、排除", "核明费用/资源的药品治疗或支付对象，不借科研、行政、设备费用赋Ec。")
    elif dimension == "F":
        if "公平" in text:
            add("F_GENERAL_EQUITY_EVALUATION", "§7第一类公平评价/信息", "是否当前要求实质公平评价/信息，还是栏目、形式或竞争公平？不补造具体障碍。")
        if re.search(r"价格|自付|承担|支付|负担", text):
            add("F_AFFORDABILITY_VS_FEE_LIABILITY", "§7患者可负担性", "是否表达患者能否负担及支付能力关系，还是只有费用责任、比例或基金承受？")
        if re.search(r"未满足|短缺|尚无|未获批|未上市|优先|申请", text):
            add("F_NEED_GAP_AND_TARGETED_OPPORTUNITY", "§7上游按需机会", "区分无有效选项、境内无对应获批、实际供药不足；缺口是否直接连接按需申请/优先/资源机会？")
        add("F_CONCRETE_EQUITY_VS_GENERAL_ACCESS", "§7具体公平关系及排除", "获取/持续/负担对象与可指认获取差异、按需保障或支付能力是否同时成立？普通渠道、名单、供药或管理便利本身不足。")
    elif dimension == "I":
        add("I_ATTRIBUTE_MODIFICATION_SUPPORT_OR_QUALIFICATION", "§6 I1/I2/I3/I4", "分别核明新颖/实质改良内容、对象—可用研发支持—直接联系或资格—实质待遇；身份/普遍规范不得替代。")
    elif dimension == "S":
        add("S_DRUG_HARM_AND_EVIDENCE_RELATION", "§3安全性", "风险/损害或证据是否属于药物及用药，而非数据、基金、疾病严重程度或一般质量？")
    elif dimension == "E":
        add("E_DRUG_EFFECT_CONTENT_AND_EVIDENCE", "§4有效性", "是否有药物防治效果/健康收益或效果证据，还是用途、行政有效、一般方法或未满足需要？")
    if contexts or re.search(r"下列|以下|第.+条|上述|按照|本办法", text):
        add("LIMITED_CONTEXT_PARENT_OR_REFERENCE_SCOPE", "§2必要语境、记录单元与计数", "实际使用了哪些同版本确指片段？父谓词是否直接承接当前，是否误继承兄弟/全文标签或漏完整标准？")
    if re.search(r"不|未|无|不得|仅|除外|或者|或|如果|符合|终止", text):
        add("NEGATION_CONDITION_OR_BRANCH_SCOPE", "§2否定、条件与例外", "保存完整否定/条件/或分支及后果；议题在场不表示正面属性、现实条件已满足或所有条件失败。")
    return candidates


def json_bytes(value: Any, *, lines: bool = False) -> bytes:
    if lines:
        return ("".join(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n" for item in value)).encode("utf-8")
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def evaluate(fixture: Path, predictions: Path, seal_path: Path, output_dir: Path) -> dict[str, Any]:
    fixture, predictions, seal_path, output_dir = (path.resolve() for path in (fixture, predictions, seal_path, output_dir))
    # This is the reference access gate. Do not move reference reads above it.
    seal, prediction_bytes = verify_seal(seal_path, predictions)
    bindings = fixture_bindings(fixture, seal)
    source_payload = bindings["source.jsonl"]["path"].read_bytes()
    manual_payload = bindings["manual.md"]["path"].read_bytes()
    require(sha_bytes(source_payload) == bindings["source.jsonl"]["sha256"], "Independent source SHA mismatch")
    require(sha_bytes(manual_payload) == bindings["manual.md"]["sha256"], "Independent manual SHA mismatch")
    manual_text = manual_payload.decode("utf-8")
    require(bool(manual_text.strip()), "Independent manual is empty")
    reference_payload = bindings["reference.jsonl"]["path"].read_bytes()
    require(sha_bytes(reference_payload) == bindings["reference.jsonl"]["sha256"], "Independent reference SHA mismatch")
    source_rows = read_jsonl_bytes(source_payload, "source")
    sources = index_rows(source_rows, "source")
    predicted = index_rows(read_jsonl_bytes(prediction_bytes, "prediction"), "prediction")
    references = index_rows(read_jsonl_bytes(reference_payload, "reference"), "reference")
    require(set(sources) == set(predicted) == set(references), "Source/prediction/reference IDs differ; subsets are forbidden")
    sealed_n = seal_value(seal, "prediction_n")
    if sealed_n is not None:
        require(sealed_n == EXPECTED_RECORDS, "Run seal prediction count is not 41")
    per_dimension = {dimension: Counter() for dimension in DIMENSIONS}
    comparison, errors = [], []
    complete_records = exact_records = known_error_records = unresolved_records = 0
    source_order = [row_id(row) for row in source_rows]
    for identifier in source_order:
        source, prediction, reference = sources[identifier], predicted[identifier], references[identifier]
        pmap, rmap = decision_map(prediction), decision_map(reference)
        pvalues = {dimension: label_value(pmap[dimension]) for dimension in DIMENSIONS}
        rvalues = {dimension: label_value(rmap[dimension]) for dimension in DIMENSIONS}
        if isinstance(prediction.get("labels"), dict):
            require(set(prediction["labels"]) == set(DIMENSIONS), "Prediction label dimensions differ")
            require({d: label_value(prediction["labels"][d]) for d in DIMENSIONS} == pvalues,
                    "Sealed prediction labels and decisions disagree")
        binary_complete = all(pvalues[d] is not None and rvalues[d] is not None for d in DIMENSIONS)
        complete_records += int(binary_complete)
        exact_records += int(binary_complete and pvalues == rvalues)
        known_error_records += int(any(pvalues[d] is not None and rvalues[d] is not None and pvalues[d] != rvalues[d] for d in DIMENSIONS))
        unresolved_records += int(not binary_complete)
        for dimension in DIMENSIONS:
            category = count_pair(per_dimension[dimension], pvalues[dimension], rvalues[dimension])
            correct = category in {"TP", "TN"}
            row = {
                "id": identifier, "dimension": dimension,
                "source_text": source.get("text", ""),
                "prediction": pvalues[dimension], "reference": rvalues[dimension],
                "comparison": category, "correct_binary_pair": correct,
                "prediction_decision": pmap[dimension],
                "prediction_reason": extract_reason(prediction, dimension, pmap[dimension]),
                "reference_decision": rmap[dimension],
                "reference_reason": extract_reason(reference, dimension, rmap[dimension]),
                "reference_record": reference,
                "source_contexts": source.get("contexts", []),
                "prediction_relation_traces": prediction.get("relation_traces", []),
                "prediction_implementation_errors": prediction.get("implementation_errors", []),
            }
            comparison.append(row)
            if not correct:
                errors.append({**row, "diagnostic_category_candidates": diagnostic_candidates(dimension, source, pvalues[dimension]),
                               "diagnostic_status": "manual_and_source_review_candidates_not_new_adjudication"})
    require(len(comparison) == EXPECTED_RECORDS * len(DIMENSIONS), "Comparison must retain all 205 decisions")
    pooled = Counter()
    for counts in per_dimension.values():
        pooled.update(counts)
    metrics = {
        "scope": EVALUATION_SCOPE, "source_records": EXPECTED_RECORDS, "dimension_decisions": len(comparison),
        "all41": {
            "n": EXPECTED_RECORDS, "exact_complete_vector_n": exact_records,
            "error_or_unresolved_record_n": EXPECTED_RECORDS - exact_records,
            "known_disagreement_record_n": known_error_records, "unresolved_record_n": unresolved_records,
            "determined_record_denominator": complete_records,
            "exact_complete_vector_rate_all41": divide(exact_records, EXPECTED_RECORDS),
            "exact_vector_rate_determined": divide(exact_records, complete_records),
            "note": "Known disagreements and unresolved record counts can overlap. Every null remains in all41.",
        },
        "all205": binary_metrics(pooled, len(comparison)),
        "per_dimension": {dimension: binary_metrics(per_dimension[dimension], EXPECTED_RECORDS) for dimension in DIMENSIONS},
        "no_metric_based_version_selection": True, "human_reliability_claim": False, "final_acceptance": False,
    }
    outputs = {"comparison205.jsonl": json_bytes(comparison, lines=True),
               "errors.jsonl": json_bytes(errors, lines=True), "metrics.json": json_bytes(metrics)}
    require(all(not (output_dir / name).exists() for name in (*outputs, "evaluation-manifest.json")),
            "Evaluation outputs already exist; never overwrite an evaluation")
    require(output_dir != fixture and predictions.parent != output_dir,
            "Write evaluation into a separate directory, not fixture or sealed prediction directory")
    require(sha_file(predictions) == seal_value(seal, "prediction_sha256"), "Prediction input changed during evaluation")
    require(all(sha_file(item["path"]) == item["sha256"] for item in bindings.values()), "Fixture input changed during evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        with (output_dir / name).open("xb") as handle:
            handle.write(payload)
    manifest = {
        "status": "completed_ai_development_comparison_not_final_validation",
        "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "scope": EVALUATION_SCOPE,
        "prediction_seal": {"path": str(seal_path), "sha256": sha_file(seal_path)},
        "prediction": {"path": str(predictions), "sha256": sha_bytes(prediction_bytes), "records": EXPECTED_RECORDS},
        "fixture_inputs": {name: {"path": str(item["path"]), "sha256": item["sha256"]} for name, item in bindings.items()},
        "evaluator": {"path": str(Path(__file__).resolve()), "sha256": sha_file(Path(__file__))},
        "outputs": [{"path": str(output_dir / name), "sha256": sha_bytes(payload)} for name, payload in outputs.items()],
        "reference_read_after_seal_validation": True, "predictions_modified": False,
        "all_inputs_unchanged": True, "complete_records_retained": EXPECTED_RECORDS,
        "complete_dimension_decisions_retained": len(comparison), "diagnostics_n": len(errors),
        "human_execution_completed": False, "final_acceptance": False,
    }
    with (output_dir / "evaluation-manifest.json").open("xb") as handle:
        handle.write(json_bytes(manifest))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--seal", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        metrics = evaluate(args.fixture, args.predictions, args.seal, args.output_dir)
    except (EvaluationError, OSError, json.JSONDecodeError, UnicodeError) as error:
        parser.exit(2, f"Evaluation refused: {error}\n")
    print(json.dumps({"status": "completed", "scope": EVALUATION_SCOPE, "all41": metrics["all41"],
                      "output_dir": str(args.output_dir.resolve())}, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
