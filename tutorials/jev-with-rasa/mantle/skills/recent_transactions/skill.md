---
name: recent_transactions
description: Read transactions through the bounded Jev account selector.
---

Ask which public demo to use: 111111 or 222222. These labels select fictional
fixtures and do not authenticate a customer. Call select_demo with the supplied
code. A selected demo cannot change within the conversation.

For a request for recent transactions, call recent_transactions with the user's
account request in their own words. The worker chooses the account from eligible
options; do not add an account ID or rewrite ambiguity into a definite choice.

For transactions, explain the returned account label, merchant, reference and
amount. For needs_account, ask the user which returned account label they mean,
then call the tool again with their answer. For stale_options, ask the user to
restate the account request; obtain a fresh decision on the next tool invocation.
For decision_unavailable or worker_unavailable, explain that the selection
service is unavailable. Never guess an account or substitute made-up rows.

For other refusal statuses, explain that the request could not be completed and
offer to stop or clarify. A confidence value is diagnostic metadata, not evidence
that an account was read. Only status transactions establishes a successful read.
