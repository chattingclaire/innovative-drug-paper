"""Run only fixed Ec61 affected controls; common353 is ROOT merge work."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent.parents[3]
if __name__ == "__main__":
    runpy.run_path(str(ROOT/"10-closure-20261012/rule-repair-v14/Ec-final/run_controls.py"),run_name="__main__")
