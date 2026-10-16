import unittest
from pathlib import Path
import tempfile
import hashlib
import runner

class RawBindingTests(unittest.TestCase):
    def setUp(self):
        self.old=runner.EXPECTED_N;runner.EXPECTED_N=2
        self.tmp=tempfile.TemporaryDirectory(prefix='rawbinding-controls-',dir=Path(__file__).parent)
        self.p=Path(self.tmp.name)/'synthetic.jsonl'
        self.p.write_text('{"id":"synthetic-a"}\n{"id":"synthetic-b"}\n')
    def tearDown(self):runner.EXPECTED_N=self.old;self.tmp.cleanup()
    def test_changed_source_sha_no_diagnostic_alignment(self):
        digest=hashlib.sha256(self.p.read_bytes()).hexdigest()
        self.p.write_text('{"id":"foreign-a"}\n{"id":"foreign-b"}\n')
        with self.assertRaisesRegex(ValueError,'frozen input SHA'):
            runner.raw_failure_diagnostics(self.p,[{'type':'ChangedDependency'}],digest,['synthetic-a','synthetic-b'])
    def test_authorized_ids_mismatch_never_reassign(self):
        with self.assertRaisesRegex(ValueError,'source-only design'):
            runner.raw_failure_diagnostics(self.p,[{'type':'SourceSchemaError'}],hashlib.sha256(self.p.read_bytes()).hexdigest(),['foreign-a','foreign-b'])
