#!/usr/bin/env python3
"""准备层纯来源envelope读取器；不是正式packet/规则协议适配器。"""
import argparse
import sys
from pathlib import Path
p = argparse.ArgumentParser(description="返回同一完整 material-envelope.json 原字节")
p.add_argument("--role", choices=("rule", "model", "human"), default="human")
p.parse_args()
sys.stdout.buffer.write(Path(__file__).with_name("material-envelope.json").read_bytes())
