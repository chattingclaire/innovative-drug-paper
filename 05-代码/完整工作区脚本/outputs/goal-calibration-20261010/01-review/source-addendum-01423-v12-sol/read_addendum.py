#!/usr/bin/env python3
"""读取本目录单一纯来源补充对象；不写标签，不改旧包。"""
import argparse
import sys
from pathlib import Path
p = argparse.ArgumentParser(description="返回角色共用的 addendum.json 原字节")
p.add_argument("--role", choices=("rule", "model", "human"), default="human")
p.parse_args()
sys.stdout.buffer.write(Path(__file__).with_name("addendum.json").read_bytes())
