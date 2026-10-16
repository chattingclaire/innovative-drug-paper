"""One no-data fake subprocess check; no campaign/model/receiver invocation."""
import ast
import importlib.util
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ast.parse((HERE / 'scheduler.py').read_text(), filename='scheduler.py')
ast.parse(Path(__file__).read_text(), filename='finite_check.py')
spec = importlib.util.spec_from_file_location('prepared_scheduler', HERE / 'scheduler.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='scheduler-no-data-check-') as directory:
    argv = [sys.executable, '-c', 'pass']
    job = module.spawn(argv, Path(directory), 'mechanical-no-data-process')
    start = module.start_receipt(job)
    job['process'].wait()
    terminal = module.terminal_receipt(job)
    assert start['pid'] == terminal['pid'] == job['process'].pid and terminal['pid'] > 0
    assert start['argv'] == terminal['argv'] == argv
    assert terminal['exitcode'] == 0
    assert terminal['stdout']['bytes'] == terminal['stderr']['bytes'] == 0
    result = {'status': 'passed', 'AST_syntax_checks': ['scheduler.py', 'finite_check.py'],
              'fake_subprocess_N': 1, 'actual_fake_process_pid': terminal['pid'],
              'argv': argv, 'exitcode': terminal['exitcode'],
              'fake_process_started_at_utc': start['started_at_utc'],
              'terminal_observed_at_utc': terminal['terminal_observed_at_utc'],
              'campaign_data_or_coding_answer_created': False,
              'frozen_runner_or_receiver_or_model_invoked': False,
              'actual_campaign_slots_or_receptions_read_by_check': False}
module.save(HERE / 'finite-check.json', result)
print('AST syntax and one no-data subprocess ownership/termination check passed.')
