"""Confirm immutable source packages and final copies after visual inspection."""
import hashlib
import json
import pathlib
import zipfile

build = pathlib.Path(__file__).resolve().parent
root = build.parent
source_root = root.parent / "独立真人判读-200条-20261013"
reports = json.loads((build / "build-report.json").read_text())
checks = []
for coder, report in zip("AB", reports):
    original_file_count = 0
    with zipfile.ZipFile(source_root / f"编码者{coder}材料.zip") as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            file = source_root / member.filename
            if not file.is_file() or hashlib.sha256(file.read_bytes()).digest() != hashlib.sha256(archive.read(member)).digest():
                raise AssertionError(f"Original source differs from archived package: {member.filename}")
            original_file_count += 1
    final = pathlib.Path(report["output"])
    final_hash = hashlib.sha256(final.read_bytes()).hexdigest()
    if final_hash != report["output_sha256"]:
        raise AssertionError(f"Final workbook differs from verified export: {coder}")
    note = final.parent / "AI复核说明.txt"
    if hashlib.sha256(note.read_bytes()).hexdigest() != report["reviewerNoteSha256"]:
        raise AssertionError(f"Reviewer explanation changed: {coder}")
    for forbidden in ("提交说明.txt", "开始阅读.html", f"独立判读-{coder}-200条.xlsx"):
        if (final.parent / forbidden).exists():
            raise AssertionError(f"Unexpected human submission artifact: {forbidden}")
    previews = [f"{coder}-{part}.png" for part in ("opening", "longest-reason", "ending")]
    for preview in previews:
        if not (build / preview).is_file():
            raise AssertionError(f"Missing preview: {preview}")
    report["visualReviewPending"] = False
    report["visualReview"] = {"inspected": previews, "result": "All six rendered samples inspected; headers, longest reasons and ending rows readable without clipping."}
    report["originalSourceFilesVerifiedAgainstZip"] = original_file_count
    report["finalCopyHashMatchesVerifiedExport"] = True
    checks.append({"coder": coder, "original_source_files_unchanged": original_file_count, "final_copy_verified": True, "reviewer_explanation_preserved": True, "visual_review_passed": True})
(build / "build-report.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2))
(build / "final-delivery-verification.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2))
print(json.dumps(checks, ensure_ascii=False, indent=2))
