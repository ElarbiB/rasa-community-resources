"""Refuse a migration target that silently keeps the old framework."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("target_audit", ROOT / "audit_target.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TargetAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for file in ("mantle/uv.lock", "mantle/agent.yml", "mantle/integrations.yml", "mantle/skills/query_store/skill.md", "mantle/skills/query_store/tools.py", "shared/database.py"):
            dest = self.root / file
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / file, dest)

    def test_complete_target_retains_shared_library_without_deepagents(self):
        result = module.audit(self.root)
        self.assertFalse(result["deepagents_in_target_lock"])
        self.assertEqual(result["provider_requests"], 0)

    def test_lock_reintroducing_deepagents_is_refused(self):
        path = self.root / "mantle/uv.lock"
        path.write_text(path.read_text() + '\n[[package]]\nname = "deepagents"\nversion = "0.7.23"\n')
        with self.assertRaisesRegex(ValueError, "still installs"):
            module.audit(self.root)

    def test_wrapper_reintroducing_deepagents_is_refused(self):
        path = self.root / "mantle/skills/query_store/tools.py"
        path.write_text(path.read_text() + "\nimport deepagents\n")
        with self.assertRaisesRegex(ValueError, "still imports"):
            module.audit(self.root)

    def test_missing_lock_is_not_success(self):
        (self.root / "mantle/uv.lock").unlink()
        with self.assertRaises(FileNotFoundError):
            module.audit(self.root)
