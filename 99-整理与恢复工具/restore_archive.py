#!/usr/bin/env python3
"""Verify and restore the paper's versioned GitHub release archives safely."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile


REPOSITORY = "chattingclaire/innovative-drug-paper"
RELEASE_TAG = "archive-20261016"
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
ASSET = re.compile(r"archive-[0-9]+\.tar\.gz\Z")


class RestoreError(Exception):
    pass


def safe_member_name(name: object) -> str:
    """Reject alternative spellings as well as path traversal and drive paths."""
    if not isinstance(name, str) or not name or "\x00" in name or "\\" in name:
        raise RestoreError("归档含无效路径。")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise RestoreError(f"拒绝绝对路径：{name!r}")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise RestoreError(f"拒绝不规范或越界路径：{name!r}")
    if PurePosixPath(name).is_absolute():
        raise RestoreError(f"拒绝绝对路径：{name!r}")
    return name


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def stream_sha256(stream) -> str:
    hasher = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        hasher.update(block)
    return hasher.hexdigest()


def read_metadata(directory: Path, requested: list[str] | None):
    summary_path = directory / "归档总览.json"
    if not summary_path.is_file():
        summary_path = directory / "archive-summary.json"
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RestoreError(f"无法读取归档总览：{summary_path}") from exc
    if not isinstance(summary, dict) or not isinstance(summary.get("bundles"), list):
        raise RestoreError("归档总览缺少 bundles 列表。")
    bundles = {}
    for item in summary["bundles"]:
        if not isinstance(item, dict):
            raise RestoreError("归档总览含无效包记录。")
        name, checksum = item.get("asset"), item.get("sha256")
        if not isinstance(name, str) or not ASSET.fullmatch(name):
            raise RestoreError("归档总览含无效包名称。")
        if name in bundles or not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
            raise RestoreError(f"归档包名称重复或SHA-256无效：{name}")
        bundles[name] = dict(item, sha256=checksum.lower())
    if not bundles:
        raise RestoreError("归档总览没有可用的包。")
    selected_names = set(requested or bundles)
    unknown = selected_names.difference(bundles)
    if unknown:
        raise RestoreError("未知归档包：" + ", ".join(sorted(unknown)))
    selected = {name: bundles[name] for name in sorted(selected_names)}

    sources = summary.get("sources", [])
    if not isinstance(sources, list) or any(not isinstance(p, str) for p in sources):
        raise RestoreError("归档来源清单无效。")
    allowed_roots = {Path(p).name for p in sources}
    manifest_path = directory / "全部文件清单.jsonl.gz"
    if not manifest_path.is_file():
        manifest_path = directory / "manifest.jsonl.gz"
    opener = gzip.open
    if not manifest_path.is_file():
        manifest_path = directory / "全部文件清单.jsonl"
        opener = open
        if not manifest_path.is_file():
            manifest_path = directory / "manifest.jsonl"
    catalog = {}
    counts = {name: 0 for name in selected}
    try:
        with opener(manifest_path, "rt", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict) or not isinstance(row.get("bundle"), str) or row.get("bundle") not in bundles:
                    raise RestoreError(f"文件清单第{line_number}行的包记录无效。")
                name = safe_member_name(row.get("archive_member"))
                source_root, relative = row.get("source_root"), row.get("relative_path")
                if not isinstance(source_root, str) or not isinstance(relative, str):
                    raise RestoreError(f"文件清单第{line_number}行缺少来源路径。")
                safe_member_name(relative)
                if "/" in source_root or name != source_root + "/" + relative:
                    raise RestoreError(f"文件清单第{line_number}行的来源路径不一致。")
                if allowed_roots and source_root not in allowed_roots:
                    raise RestoreError(f"文件清单含未登记的来源根目录：{source_root}")
                checksum = row.get("archived_sha256")
                size = row.get("archived_bytes")
                if not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
                    raise RestoreError(f"文件清单SHA-256无效：{name}")
                if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                    raise RestoreError(f"文件清单文件大小无效：{name}")
                if name in catalog:
                    raise RestoreError(f"文件清单路径重复：{name}")
                catalog[name] = dict(row, archived_sha256=checksum.lower())
                if row["bundle"] in selected:
                    counts[row["bundle"]] += 1
    except RestoreError:
        raise
    except (OSError, ValueError, EOFError) as exc:
        raise RestoreError(f"无法完整读取文件清单：{manifest_path}") from exc
    for name, item in selected.items():
        if "file_count" in item and counts[name] != item["file_count"]:
            raise RestoreError(f"清单文件数与归档总览不符：{name}")
        if not counts[name]:
            raise RestoreError(f"选定包在文件清单中没有记录：{name}")
    expected = {name: row for name, row in catalog.items() if row["bundle"] in selected}
    return selected, expected, sources, allowed_roots, catalog, bundles


def read_internal_links(directory: Path, catalog, bundles, allowed_roots):
    """Only this reviewed map may create links; tar links remain forbidden."""
    path = directory / "内部研究链接映射.json"
    if not path.is_file():
        path = directory / "internal-links.json"
    if not path.exists():
        print("未找到内部研究链接映射；仅处理普通归档文件。", flush=True)
        return [], 0
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RestoreError(f"无法读取内部研究链接映射：{path}") from exc
    if not isinstance(mapping, dict) or mapping.get("schema_version") != 1 or not isinstance(mapping.get("links"), list):
        raise RestoreError("内部研究链接映射结构或版本无效。")
    links = []
    names = set()
    disabled = 0
    for row in mapping["links"]:
        if not isinstance(row, dict) or not isinstance(row.get("restorable"), bool):
            raise RestoreError("内部研究链接映射含无效记录。")
        name = safe_member_name(row.get("archive_member"))
        source_root, relative = row.get("source_root"), row.get("relative_path")
        if not isinstance(source_root, str) or not isinstance(relative, str):
            raise RestoreError(f"内部链接缺少来源路径：{name}")
        safe_member_name(relative)
        if "/" in source_root or name != source_root + "/" + relative:
            raise RestoreError(f"内部链接来源路径不一致：{name}")
        if allowed_roots and source_root not in allowed_roots:
            raise RestoreError(f"内部链接来源根目录未登记：{name}")
        if name in names:
            raise RestoreError(f"内部链接路径重复：{name}")
        names.add(name)
        if not row["restorable"]:
            disabled += 1
            continue
        entry_type = row.get("entry_type")
        if entry_type not in {"file", "directory"}:
            raise RestoreError(f"内部链接目标类型无效：{name}")
        target = safe_member_name(row.get("resolved_archive_member"))
        if name == target or name.startswith(target + "/") or target.startswith(name + "/"):
            raise RestoreError(f"内部链接不能指向自身或其祖先、后代：{name}")
        if name in catalog:
            raise RestoreError(f"内部链接占用归档文件路径：{name}")
        if entry_type == "file":
            if target not in catalog:
                raise RestoreError(f"内部链接目标不在文件清单：{name}")
            target_files = [target]
        else:
            target_files = [member for member in catalog if member.startswith(target + "/")]
            if target in catalog or not target_files:
                raise RestoreError(f"内部目录链接目标不是已归档普通文件的祖先目录：{name}")
            if row.get("target_archived_file_count") != len(target_files):
                raise RestoreError(f"内部目录链接目标文件数与清单不符：{name}")
        if any(member.startswith(name + "/") for member in catalog):
            raise RestoreError(f"内部链接与归档目录冲突：{name}")
        for parent in PurePosixPath(name).parents:
            if str(parent) in catalog:
                raise RestoreError(f"内部链接父目录与普通文件冲突：{name}")
        target_bundle = row.get("target_bundle")
        target_bundles = {catalog[member]["bundle"] for member in target_files}
        if target_bundle is not None and (entry_type != "file" or target_bundle != catalog[target]["bundle"]):
            raise RestoreError(f"内部链接目标包与文件清单不符：{name}")
        declared_target_bundles = row.get("target_bundles")
        if declared_target_bundles is not None:
            if not isinstance(declared_target_bundles, list) or any(not isinstance(asset, str) for asset in declared_target_bundles) or set(declared_target_bundles) != target_bundles:
                raise RestoreError(f"内部链接目标包列表与文件清单不符：{name}")
        elif entry_type == "directory":
            raise RestoreError(f"内部目录链接缺少目标包列表：{name}")
        owner_bundle = row.get("owner_bundle")
        if not isinstance(owner_bundle, str) or owner_bundle not in bundles:
            raise RestoreError(f"内部链接缺少有效的来源包归属：{name}")
        parent = str(PurePosixPath(name).parent)
        parent_bundles = {r["bundle"] for member, r in catalog.items() if member.rsplit("/", 1)[0] == parent}
        if owner_bundle not in parent_bundles:
            raise RestoreError(f"内部链接来源包不含同父目录普通文件：{name}")
        candidates = row.get("owner_bundle_candidates")
        if candidates is not None:
            if not isinstance(candidates, list) or any(not isinstance(asset, str) or asset not in parent_bundles for asset in candidates):
                raise RestoreError(f"内部链接候选包归属无效：{name}")
            if owner_bundle not in candidates:
                raise RestoreError(f"内部链接来源包不在候选归属中：{name}")
        anchor = row.get("owner_anchor_archive_member")
        if anchor is not None:
            anchor = safe_member_name(anchor)
            if anchor not in catalog or str(PurePosixPath(anchor).parent) != parent or catalog[anchor]["bundle"] != owner_bundle:
                raise RestoreError(f"内部链接来源锚点与文件清单不符：{name}")
        # The original target text is historical evidence only. It is never used
        # as a filesystem path, even if it names the original absolute source.
        links.append({"archive_member": name, "resolved_archive_member": target,
                      "entry_type": entry_type, "target_files": target_files})
    for link in links:
        name, target = link["archive_member"], link["resolved_archive_member"]
        if target in names:
            raise RestoreError(f"内部链接目标不能是另一链接：{name}")
        if link["entry_type"] == "directory" and any(other.startswith(target + "/") for other in names):
            raise RestoreError(f"内部目录链接目标不能包含其他映射链接，避免循环：{name}")
        if any(name.startswith(other + "/") for other in names if other != name):
            raise RestoreError(f"内部链接不能用作其他映射链接的父目录：{name}")
    return links, disabled


def select_internal_links(links, expected):
    eligible = []
    missing_target = 0
    missing_parent = 0
    for link in links:
        if not all(member in expected for member in link["target_files"]):
            missing_target += 1
            continue
        parent_prefix = str(PurePosixPath(link["archive_member"]).parent) + "/"
        if not any(member.startswith(parent_prefix) for member in expected):
            missing_parent += 1
            continue
        eligible.append(link)
    return eligible, missing_target, missing_parent


def restore_internal_links(root: Path, links):
    for link in links:
        path = root.joinpath(*link["archive_member"].split("/"))
        target = root.joinpath(*link["resolved_archive_member"].split("/"))
        assert_safe_parent(root, path)
        assert_safe_parent(root, target)
        if not path.parent.is_dir():
            raise RestoreError(f"内部链接来源目录未实际恢复：{path}")
        if path.exists() or path.is_symlink():
            raise RestoreError(f"拒绝覆盖内部链接位置的已有内容：{path}")
        correct_type = target.is_file() if link["entry_type"] == "file" else target.is_dir()
        if target.is_symlink() or not correct_type:
            raise RestoreError(f"内部链接目标未恢复或类型不符：{target}")
        for member in link["target_files"]:
            actual_file = root.joinpath(*member.split("/"))
            assert_safe_parent(root, actual_file)
            if actual_file.is_symlink() or not actual_file.is_file():
                raise RestoreError(f"内部链接依赖的普通文件未实际恢复：{actual_file}")
        resolved_target = target.resolve(strict=True)
        if root not in resolved_target.parents:
            raise RestoreError(f"内部链接目标超出恢复目录：{path}")
        relative_target = os.path.relpath(target, start=path.parent)
        try:
            os.symlink(relative_target, path)
        except FileExistsError as exc:
            raise RestoreError(f"拒绝覆盖内部链接位置的已有内容：{path}") from exc
        if not path.is_symlink() or path.resolve(strict=True) != resolved_target:
            raise RestoreError(f"内部链接解析目标核验失败：{path}")
    return len(links)


def download_missing(archives: Path, selected):
    if shutil.which("gh") is None:
        raise RestoreError("未找到GitHub CLI（gh）；请安装并登录，或手动下载归档包。")
    archives.mkdir(parents=True, exist_ok=True)
    for name in selected:
        target = archives / name
        if target.exists() or target.is_symlink():
            continue
        result = subprocess.run(
            ["gh", "release", "download", RELEASE_TAG, "--repo", REPOSITORY,
             "--pattern", name, "--dir", str(archives)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if result.returncode:
            raise RestoreError("gh下载失败；请检查登录状态、私有仓库权限和网络。未输出身份凭据。")
        print(f"已下载：{name}", flush=True)


def verify_archives(archives: Path, selected):
    for name, item in selected.items():
        path = archives / name
        if path.is_symlink() or not path.is_file():
            raise RestoreError(f"归档包缺失、不是普通文件或为链接：{path}")
        if file_sha256(path) != item["sha256"]:
            raise RestoreError(f"归档包SHA-256不符：{name}；未开始解压。")
        print(f"包SHA-256通过：{name}", flush=True)


def inspect_archives(archives: Path, selected, expected, allowed_roots):
    seen = set()
    kinds = {}
    for asset in selected:
        with tarfile.open(archives / asset, "r:gz") as archive:
            for member in archive:
                # Tar directory headers conventionally end with a slash.
                name = safe_member_name(member.name.rstrip("/") if member.isdir() else member.name)
                if allowed_roots and name.split("/", 1)[0] not in allowed_roots:
                    raise RestoreError(f"归档包含未登记的来源根目录：{name}")
                if not (member.isfile() or member.isdir()):
                    raise RestoreError(f"拒绝链接或特殊类型成员：{name}")
                if not isinstance(member.mtime, (int, float)) or not math.isfinite(member.mtime):
                    raise RestoreError(f"归档成员修改时间无效：{name}")
                kind = "directory" if member.isdir() else "file"
                if name in kinds and (kinds[name] != kind or kind == "file"):
                    raise RestoreError(f"归档成员路径重复或类型冲突：{name}")
                kinds[name] = kind
                if member.isdir():
                    continue
                row = expected.get(name)
                if row is None or row["bundle"] != asset:
                    raise RestoreError(f"归档包含清单外文件或错误的包归属：{name}")
                if member.size != row["archived_bytes"]:
                    raise RestoreError(f"归档文件大小与清单不符：{name}")
                seen.add(name)
    missing = set(expected).difference(seen)
    if missing:
        raise RestoreError(f"选定包缺少清单文件：{sorted(missing)[0]}")
    for name in kinds:
        for parent in PurePosixPath(name).parents:
            if str(parent) != "." and kinds.get(str(parent)) == "file":
                raise RestoreError(f"归档中普通文件被用作目录：{parent}")
    print(f"全部成员路径、类型、数量及大小检查通过：{len(seen)}个文件。", flush=True)


def check_destination(destination: Path, sources):
    if destination.is_symlink():
        raise RestoreError("恢复目录不能是链接。")
    resolved = destination.resolve()
    for source in sources:
        source_path = Path(source).expanduser().resolve()
        if resolved == source_path or source_path in resolved.parents:
            raise RestoreError("恢复目录不能位于任何原始来源目录内。请使用新的空目录。")
    if destination.exists():
        if not destination.is_dir() or any(destination.iterdir()):
            raise RestoreError("恢复目录必须不存在或完全为空；拒绝覆盖已有文件。")
    return resolved


def assert_safe_parent(root: Path, target: Path):
    """Recheck real parents before each write; never follow a created symlink."""
    if target.is_symlink():
        raise RestoreError(f"恢复路径出现链接：{target}")
    current = target.parent
    while current != root:
        if current.is_symlink():
            raise RestoreError(f"恢复路径的父目录出现链接：{current}")
        if current == current.parent:
            raise RestoreError("恢复路径超出目标目录。")
        current = current.parent
    resolved_parent = target.parent.resolve()
    if root != resolved_parent and root not in resolved_parent.parents:
        raise RestoreError("恢复路径超出目标目录。")


def extract_archives(archives: Path, selected, expected, root: Path):
    root.mkdir(parents=True, exist_ok=True)
    directory_metadata = {}
    for asset in selected:
        with tarfile.open(archives / asset, "r:gz") as archive:
            for member in archive:
                name = safe_member_name(member.name.rstrip("/") if member.isdir() else member.name)
                if not (member.isfile() or member.isdir()):
                    raise RestoreError(f"拒绝链接或特殊类型成员：{name}")
                target = root.joinpath(*name.split("/"))
                assert_safe_parent(root, target)
                if member.isdir():
                    if target.exists() and not target.is_dir():
                        raise RestoreError(f"拒绝覆盖已有文件：{target}")
                    target.mkdir(parents=True, exist_ok=True)
                    directory_metadata[target] = (member.mode & 0o777, member.mtime)
                    continue
                row = expected.get(name)
                if row is None or row["bundle"] != asset or row["archived_bytes"] != member.size:
                    raise RestoreError(f"解压时成员与已检查清单不一致：{name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                assert_safe_parent(root, target)
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                flags |= getattr(os, "O_NOFOLLOW", 0)
                try:
                    descriptor = os.open(target, flags, 0o600)
                except FileExistsError as exc:
                    raise RestoreError(f"拒绝覆盖已有文件：{target}") from exc
                with os.fdopen(descriptor, "wb") as output:
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise RestoreError(f"无法读取归档成员：{name}")
                    with stream:
                        shutil.copyfileobj(stream, output, length=1024 * 1024)
                # Verify before applying possibly unreadable original permission bits.
                if target.stat().st_size != row["archived_bytes"] or file_sha256(target) != row["archived_sha256"]:
                    raise RestoreError(f"恢复后文件SHA-256不符：{name}；已写文件保留用于排查。")
                target.chmod(member.mode & 0o777)
                os.utime(target, (member.mtime, member.mtime), follow_symlinks=False)
        print(f"已恢复并逐文件核验：{asset}", flush=True)
    for directory, (mode, mtime) in sorted(directory_metadata.items(), key=lambda item: len(item[0].parts), reverse=True):
        directory.chmod(mode)
        os.utime(directory, (mtime, mtime), follow_symlinks=False)


def verify_member_contents(archives: Path, selected, expected):
    count = 0
    for asset in selected:
        with tarfile.open(archives / asset, "r:gz") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                name = safe_member_name(member.name)
                row = expected[name]
                with archive.extractfile(member) as stream:
                    checksum = stream_sha256(stream)
                if checksum != row["archived_sha256"]:
                    raise RestoreError(f"包内文件SHA-256不符：{name}")
                count += 1
        print(f"包内逐文件SHA-256通过：{asset}", flush=True)
    return count


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="安全核验并恢复创新药论文的完整归档；仅使用Python标准库。")
    parser.add_argument("--archives", required=True, type=Path, help="本地archive-*.tar.gz存放目录")
    parser.add_argument("--destination", type=Path, help="新建或完全为空的恢复目录；不会覆盖已有文件")
    parser.add_argument("--verify-only", action="store_true", help="检查归档及包内全部选定文件，不解压")
    parser.add_argument("--download", action="store_true", help="通过已登录gh下载固定私有仓库release中缺少的包")
    parser.add_argument("--bundle", action="append", metavar="ASSET", help="仅恢复一个包，可重复指定，例如archive-001.tar.gz")
    parser.add_argument("--metadata", type=Path, default=Path(__file__).resolve().parent.parent / "90-完整归档", help="归档总览及文件清单所在目录（默认本仓库90-完整归档）")
    args = parser.parse_args(argv)
    if not args.verify_only and args.destination is None:
        parser.error("恢复时必须指定 --destination；只核验可用 --verify-only。")
    return args


def main(argv=None):
    args = parse_args(argv)
    selected, expected, sources, allowed_roots, catalog, bundles = read_metadata(args.metadata.expanduser(), args.bundle)
    links, disabled_links = read_internal_links(args.metadata.expanduser(), catalog, bundles, allowed_roots)
    eligible_links, missing_targets, missing_parents = select_internal_links(links, expected)
    archives = args.archives.expanduser().resolve()
    destination = None
    if not args.verify_only:
        destination = check_destination(args.destination.expanduser(), sources)
    if args.download:
        download_missing(archives, selected)
    verify_archives(archives, selected)
    inspect_archives(archives, selected, expected, allowed_roots)
    if args.verify_only:
        count = verify_member_contents(archives, selected, expected)
        print(f"内部链接映射核验通过：{len(eligible_links)}条满足所选包恢复条件；缺完整目标{missing_targets}条，缺来源目录{missing_parents}条，不恢复的链接{disabled_links}条。")
        print(f"核验完成：{len(selected)}个包，{count}个文件；未解压。")
    else:
        # Recheck after all potentially long read-only checks and before the first write.
        destination = check_destination(destination, sources)
        extract_archives(archives, selected, expected, destination)
        restored_links = restore_internal_links(destination, eligible_links)
        print(f"安全重建并核验内部研究链接：{restored_links}条；缺完整目标{missing_targets}条，缺来源目录{missing_parents}条，不恢复的链接{disabled_links}条。")
        print(f"恢复完成：{len(selected)}个包，{len(expected)}个文件；路径：{destination}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RestoreError, OSError, tarfile.TarError, EOFError, ValueError) as exc:
        print(f"恢复停止：{exc}", file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("恢复已中断；已写入的文件保留，再次恢复请使用新的空目录。", file=sys.stderr)
        raise SystemExit(130)
