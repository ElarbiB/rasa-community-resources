"""Print deterministic SDK/application controls, not a live conversation."""
import json
from typesafe_sdk import RetryPolicy, TypeSafeClient
from .accounts import Accounts
from .scripted import scripted_transport
from .selector import MODEL, Selector


def main():
    for mode in ("current", "retired_during_decision", "clarify"):
        accounts = Accounts()
        transport, requests = scripted_transport(
            "ask_customer" if mode == "clarify" else "A-CURRENT",
            (lambda: accounts.retire("A-CURRENT")) if mode == "retired_during_decision" else None)
        with TypeSafeClient(api_key="scripted-local-test", base_url="https://scripted.invalid",
                            model=MODEL, transport=transport, retry=RetryPolicy(max_retries=0)) as client:
            result = Selector(client, accounts).select("demo-a", "Show my current account transactions")
        print(json.dumps({"control": mode, "status": result["status"], "account_reads": accounts.reads,
                          "sdk_requests": len(requests), "external_provider_requests": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
