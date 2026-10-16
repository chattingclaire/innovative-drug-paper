#!/usr/bin/env python3
"""Redirect the already-frozen ten-control runner to a new runtime03 output directory."""

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "run_actual_controls_once.py"
RUNTIME = HERE.parents[3] / "自动规则编码" / "实质评价与支持关系修复" / "runtime03"
OUTDIR = HERE / "原10控制完整入口"
OUTDIR.mkdir(exist_ok=False)

spec = importlib.util.spec_from_file_location("frozen_ten_control_runner", ORIGINAL)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.OUTPUT = OUTDIR / "实际入口输出10.jsonl"
runner.FREEZE = OUTDIR / "实际入口执行冻结.json"
runner.REPORT = OUTDIR / "实际入口执行报告.json"
sys.argv = [str(ORIGINAL), "--runtime-dir", str(RUNTIME.resolve()),
            "--expected-runtime-tree-sha256",
            "d7d8b8fe77a5a420ec089d52ae28974d50963a0ef2acd47dc009f25591f1bb1d",
            "--expected-version", "substantive-evaluation-support-repair-03"]
runner.main()
