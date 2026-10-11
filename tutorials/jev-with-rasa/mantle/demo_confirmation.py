"""Controlled tutorial-code mutation: an old Yes cannot approve a new proposal.

Scripted SDK, fictional records, controlled actual UserUttered objects. The
unsafe variant exists only in memory; no Rasa engine or source file is changed.
"""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from rasa.shared.core.events import UserUttered

ROOT = Path(__file__).resolve().parents[1]


async def replay(remove_event_guard=False):
    spec = importlib.util.spec_from_file_location('confirmation_fixture', ROOT / 'tests/test_mantle_binding.py')
    fixture_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture_module)
    fixture = fixture_module.MantleBindings('test_same_user_event_cannot_confirm_its_own_proposal')
    await fixture.asyncSetUp()
    try:
        if remove_event_guard:
            path = ROOT / 'mantle/skills/recent_transactions/tools.py'
            original = path.read_text()
            guard = 'if user is None or user.timestamp <= created:'
            assert original.count(guard) == 1
            altered = original.replace(guard, 'if user is None:')
            variant = ModuleType('deliberately_unsafe_tutorial_tools')
            exec(compile(altered, str(path), 'exec'), variant.__dict__)
            variant.urlopen = fixture.tools.urlopen
            fixture.tools = variant
        fixture.tool_context.events = [UserUttered('Yes', timestamp=1)]
        await fixture.tools.select_demo('111111')
        proposal = await fixture.tools.propose_recent_transactions(context=fixture.tool_context)
        result = await fixture.tools.read_confirmed_transactions(context=fixture.tool_context)
        return {'control': 'removed_later_event_check' if remove_event_guard else 'checked_later_event',
                'user_events': [{'text': 'Yes', 'timestamp': 1}], 'proposal_created_from_event': 1,
                'later_user_reply': False, 'proposal_status': proposal.llm_response['status'],
                'read_status': result.llm_response['status'], 'account_reads': list(fixture.accounts.reads),
                'scripted_sdk_requests': len(fixture.requests), 'external_provider_requests': 0}
    finally:
        await fixture.asyncTearDown()


async def main():
    for remove_guard in [False, True]:
        print(json.dumps(await replay(remove_guard), sort_keys=True))


if __name__ == '__main__':
    asyncio.run(main())
