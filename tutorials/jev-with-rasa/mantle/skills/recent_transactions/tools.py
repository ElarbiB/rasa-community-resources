"""The model supplies words; the current Rasa sender owns the fixture binding."""
import asyncio
import json
from urllib.error import URLError
from urllib.request import Request, urlopen
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

DEMO_CODES = {"111111": "demo-a", "222222": "demo-b"}
BINDINGS = {}


def sender():
    from rasa.mantle.orchestration.turn_context import current_turn_context
    return current_turn_context().sender_id


@tool(description="Select public fictional fixture 111111 or 222222 supplied by the user. This does not authenticate anyone.")
async def select_demo(code: str, context: ToolContext = None) -> ToolResult:
    owner = DEMO_CODES.get(code)
    if owner is None:
        return ToolResult(llm_response={"status": "unknown_demo"})
    key = sender()
    if key in BINDINGS and BINDINGS[key] != owner:
        return ToolResult(llm_response={"status": "demo_identity_changed"})
    BINDINGS[key] = owner
    return ToolResult(llm_response={"status": "demo_ready"})


def request_worker(owner, message):
    request = Request("http://127.0.0.1:5029/select", method="POST",
                      data=json.dumps({"owner": owner, "message": message}).encode(),
                      headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=3) as response:
            result = json.load(response)
        if not isinstance(result, dict) or not isinstance(result.get("status"), str):
            raise ValueError()
        return result
    except (URLError, OSError, ValueError):
        return {"status": "worker_unavailable"}


@tool(description="Read fictional recent transactions using the user's account request. The application chooses demo identity and Jev chooses only among the offered accounts.")
async def recent_transactions(message: str, context: ToolContext = None) -> ToolResult:
    owner = BINDINGS.get(sender())
    if owner is None:
        return ToolResult(llm_response={"status": "needs_demo_code"})
    result = await asyncio.to_thread(request_worker, owner, message)
    return ToolResult(llm_response=result)
