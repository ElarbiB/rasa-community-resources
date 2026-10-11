"""Invoke real decorated Mantle tools against a real loopback worker."""
import importlib.util
import inspect
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from typesafe_sdk import RetryPolicy, TypeSafeClient
from jacaranda_jev.accounts import Accounts
from jacaranda_jev.scripted import scripted_transport
from jacaranda_jev.selector import MODEL, Selector
from jacaranda_jev.server import handler


class MantleBindings(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        path = Path(__file__).resolve().parents[1] / "mantle/skills/recent_transactions/tools.py"
        spec = importlib.util.spec_from_file_location("jev_mantle_tools", path)
        self.tools = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tools)
        self.accounts = Accounts()
        transport, self.requests = scripted_transport()
        self.client = TypeSafeClient(api_key="scripted-local-test", base_url="https://scripted.invalid",
                                    transport=transport, model=MODEL, retry=RetryPolicy(max_retries=0))
        self.server = HTTPServer(("127.0.0.1", 0), handler(Selector(self.client, self.accounts)))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        original = self.tools.urlopen
        def local(request, **kwargs):
            from urllib.request import Request
            request = Request(f"http://127.0.0.1:{self.server.server_port}/select", data=request.data,
                              headers=dict(request.headers), method=request.method)
            return original(request, **kwargs)
        self.redirect = patch.object(self.tools, "urlopen", side_effect=local)
        self.redirect.start()
        self.context = patch("rasa.mantle.orchestration.turn_context.current_turn_context",
                             return_value=SimpleNamespace(sender_id="sender-a"))
        self.context.start()

    async def asyncTearDown(self):
        self.context.stop()
        self.redirect.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.client.close()

    async def test_tool_does_not_offer_owner_or_account_id(self):
        self.assertEqual(set(inspect.signature(self.tools.recent_transactions).parameters), {"message", "context"})

    async def test_unbound_sender_is_refused_before_worker(self):
        result = await self.tools.recent_transactions("Current")
        self.assertEqual(result.llm_response, {"status": "needs_demo_code"})
        self.assertEqual(self.requests, [])

    async def test_actual_mantle_tool_reaches_native_sdk_and_read(self):
        await self.tools.select_demo("111111")
        result = await self.tools.recent_transactions("Show my current account")
        self.assertEqual(result.llm_response["status"], "transactions")
        self.assertEqual(self.accounts.reads, ["A-CURRENT"])
        self.assertEqual(len(self.requests), 1)

    async def test_demo_identity_cannot_be_rebound(self):
        await self.tools.select_demo("111111")
        self.assertEqual((await self.tools.select_demo("222222")).llm_response,
                         {"status": "demo_identity_changed"})

    async def test_other_sender_has_no_inherited_binding(self):
        await self.tools.select_demo("111111")
        with patch("rasa.mantle.orchestration.turn_context.current_turn_context",
                   return_value=SimpleNamespace(sender_id="sender-b")):
            self.assertEqual((await self.tools.recent_transactions("Current")).llm_response,
                             {"status": "needs_demo_code"})

    async def test_worker_connection_error_does_not_invent_rows(self):
        from urllib.error import URLError
        await self.tools.select_demo("111111")
        with patch.object(self.tools, "urlopen", side_effect=URLError("scripted offline")):
            self.assertEqual((await self.tools.recent_transactions("Current")).llm_response,
                             {"status": "worker_unavailable"})


if __name__ == "__main__":
    unittest.main()
