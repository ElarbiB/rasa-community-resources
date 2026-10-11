"""Observe the real Agno model input; replies are scripted and memories seeded."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from agno.db.schemas.memory import UserMemory
from agno.db.sqlite import SqliteDb
from agno.models.base import Model
from agno.models.response import ModelResponse
from shop_adviser.adviser import PREFERENCE, create_adviser

FIRST_QUESTION = "Synthetic conversation A1: tell me about the public hand cream."


@dataclass
class ObservedModel(Model):
    id: str = "scripted-native-observer"
    provider: str = "offline-fixture"
    inputs: list = field(default_factory=list)

    def invoke(self, messages, **kwargs):
        self.inputs.append([{"role": m.role, "content": m.content} for m in messages])
        if not any(m.role == "tool" for m in messages):
            return ModelResponse(
                role="assistant",
                tool_calls=[
                    {
                        "id": "fixture-product",
                        "type": "function",
                        "function": {"name": "lookup_product", "arguments": "{}"},
                    }
                ],
            )
        return ModelResponse(
            role="assistant",
            content=json.dumps(
                {
                    "product_id": "WS-HAND-01",
                    "explanation": "Scripted public product response.",
                }
            ),
        )

    async def ainvoke(self, *args, **kwargs):
        raise NotImplementedError("This fixture tests synchronous native execution")

    def invoke_stream(self, *args, **kwargs):
        raise NotImplementedError("This fixture tests non-streaming execution")

    def ainvoke_stream(self, *args, **kwargs):
        raise NotImplementedError("This fixture tests non-streaming execution")

    def _parse_provider_response(self, response, **kwargs):
        return response

    def _parse_provider_response_delta(self, response):
        return response


def observe_memory_strategy(
    db_path: Path, strategy: str, *, reuse_agent: bool = True
) -> dict:
    """Two fresh conversations after A1; hold history and seeded wording fixed.

    correct: stable user IDs; session-as-user: use the thread ID as memory key;
    omitted: store under the documented fallback and omit all run user IDs.
    This configured exercise observes SDK inputs, not model accuracy or auth.
    """
    if strategy not in {"correct", "session-as-user", "omitted"}:
        raise ValueError("Unknown memory strategy")
    db = SqliteDb(db_file=str(db_path))
    owner = {"correct": "customer-a", "session-as-user": "a1", "omitted": "default"}[
        strategy
    ]
    db.upsert_user_memory(
        UserMemory(memory=PREFERENCE, memory_id="synthetic-preference", user_id=owner)
    )
    model = ObservedModel()
    agent = create_adviser(db_path, model)
    first_owner = {"correct": "customer-a", "session-as-user": "a1", "omitted": None}[
        strategy
    ]
    agent.run(FIRST_QUESTION, session_id="a1", user_id=first_owner)
    observations = []
    for session, customer in [("a2", "customer-a"), ("b1", "customer-b")]:
        if not reuse_agent:
            model = ObservedModel()
            agent = create_adviser(db_path, model)
        selected_owner = {
            "correct": customer,
            "session-as-user": session,
            "omitted": None,
        }[strategy]
        model.inputs.clear()
        output = agent.run(
            f"Synthetic conversation {session}: tell me about the public hand cream.",
            session_id=session,
            user_id=selected_owner,
        )
        initial = model.inputs[0]
        initial_text = json.dumps(initial)
        tool_messages = [m for m in model.inputs[-1] if m["role"] == "tool"]
        observations.append(
            {
                "customer": customer,
                "session": session,
                "preference_in_initial_input": PREFERENCE in initial_text,
                "previous_question_in_initial_input": FIRST_QUESTION in initial_text,
                "user_messages_in_initial_input": sum(
                    message["role"] == "user" for message in initial
                ),
                "native_product_tool_seen": any(
                    "WS-HAND-01" in str(m["content"]) for m in tool_messages
                ),
                "final_output_present": bool(output.content),
            }
        )
    return {
        "strategy": strategy,
        "agent_lifetime": "reused" if reuse_agent else "fresh",
        "observations": observations,
    }
