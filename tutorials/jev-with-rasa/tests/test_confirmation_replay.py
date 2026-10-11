"""Check the trace distinguishes a later reply from an earlier Yes."""
import importlib.util
from pathlib import Path
import unittest


class ConfirmationReplay(unittest.IsolatedAsyncioTestCase):
    async def test_one_removed_event_check_changes_the_read(self):
        path = Path(__file__).resolve().parents[1] / 'mantle/demo_confirmation.py'
        spec = importlib.util.spec_from_file_location('confirmation_replay', path)
        demo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(demo)
        checked = await demo.replay(False)
        removed = await demo.replay(True)
        self.assertEqual(checked['user_events'], removed['user_events'])
        self.assertFalse(checked['later_user_reply'])
        self.assertFalse(removed['later_user_reply'])
        self.assertEqual(checked['read_status'], 'needs_confirmation')
        self.assertEqual(checked['account_reads'], [])
        self.assertEqual(removed['read_status'], 'transactions')
        self.assertEqual(removed['account_reads'], ['A-CURRENT'])
        self.assertEqual(checked['scripted_sdk_requests'], 1)
        self.assertEqual(removed['scripted_sdk_requests'], 1)
        self.assertEqual(checked['external_provider_requests'], 0)
        self.assertEqual(removed['external_provider_requests'], 0)
