"""Native agent-as-tool context controls with scripted text, not provider evidence."""
import copy
import json
import unittest
from strands import Agent
from strands.models.model import Model

class ScriptedTextModel(Model):
    def __init__(self):
        self.inputs = []
    def update_config(self, **kwargs):
        pass
    def get_config(self):
        return {}
    async def structured_output(self, *args, **kwargs):
        raise AssertionError("Not used")
        yield
    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        self.inputs.append(copy.deepcopy(messages))
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "Synthetic read-only reply."}}}
        yield {"contentBlockStop": {"contentBlockIndex": 0}}
        yield {"messageStop": {"stopReason": "end_turn"}}

class NativeAgentToolContexts(unittest.TestCase):
    def call_pair(self, preserve_context=False):
        model = ScriptedTextModel()
        specialist = Agent(model=model, name="network_specialist", callback_handler=None, load_tools_from_directory=False)
        tool = specialist.as_tool(preserve_context=preserve_context)
        orchestrator = Agent(model=ScriptedTextModel(), tools=[tool], callback_handler=None, load_tools_from_directory=False)
        first = orchestrator.tool.network_specialist(input="Caller A private fixture", record_direct_tool_call=False)
        second = orchestrator.tool.network_specialist(input="Caller B private fixture", record_direct_tool_call=False)
        self.assertEqual(first["status"], "success", first)
        self.assertEqual(second["status"], "success", second)
        return model, orchestrator, first, second

    def test_default_agent_as_tool_resets_specialist_history(self):
        model, _, first, second = self.call_pair()
        self.assertEqual(first["status"], "success")
        self.assertEqual(second["status"], "success")
        self.assertEqual(len(model.inputs), 2)
        self.assertIn("Caller A private fixture", json.dumps(model.inputs[0]))
        self.assertNotIn("Caller A private fixture", json.dumps(model.inputs[1]))
        self.assertIn("Caller B private fixture", json.dumps(model.inputs[1]))

    def test_preserved_context_includes_previous_caller_fixture(self):
        model, _, _, _ = self.call_pair(preserve_context=True)
        self.assertIn("Caller A private fixture", json.dumps(model.inputs[1]))
        self.assertIn("Caller B private fixture", json.dumps(model.inputs[1]))

    def test_nonrecording_wrapper_leaves_orchestrator_history_empty(self):
        _, orchestrator, _, _ = self.call_pair()
        self.assertEqual(orchestrator.messages, [])

if __name__ == "__main__":
    unittest.main()
