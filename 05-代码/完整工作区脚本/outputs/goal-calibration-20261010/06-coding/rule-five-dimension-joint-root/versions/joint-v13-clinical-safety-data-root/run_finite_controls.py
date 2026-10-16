"""Run this isolated candidate's controls against v11, never the old v11 audit."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent.parents[3]
if __name__ == '__main__':
    runpy.run_path(str(ROOT / '10-closure-20261012/rule-repair-v12/run_controls.py'), run_name='__main__')
