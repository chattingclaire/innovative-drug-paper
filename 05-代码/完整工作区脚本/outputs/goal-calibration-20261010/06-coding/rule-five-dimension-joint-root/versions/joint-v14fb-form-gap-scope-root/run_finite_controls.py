"""Run only this F successor's fixed domain controls."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent.parents[3]
if __name__=='__main__':
    runpy.run_path(str(ROOT/'10-closure-20261012/rule-repair-v14/F-final/run_bounded_controls.py'),run_name='__main__')
