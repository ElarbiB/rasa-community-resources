# Jev account selection with a Rasa conversation

This extends the fictional Jacaranda Bank examples with a read-only transaction
request. The TypeSafe SDK sends a bounded account question to Jev. Python builds
the eligible choices and checks them again before reading. Mantle asks for missing
input and explains the returned facts through its ordinary tool interface.

The existing Mantle orchestrator still chooses when to invoke tools and writes
the conversation. This application adds Jev inside a tool workflow. It uses the
public Rasa package and public TypeSafe SDK, with no Rasa engine patch or private
feature flag. The worker's SDK client is retained across requests and closed on
shutdown. This single-threaded loopback service is a development example.

## Run the offline exercise

Use Python 3.12 and uv. From this repository root:

```sh
cd tutorials/jev-with-rasa/mantle
uv sync --locked --prerelease=allow
make demo
make test
```

The demo passes scripted HTTP replies through the actual TypeSafe SDK. It prints
an accepted read, a refused stale choice and a clarification with no read. The
scripted confidence is deliberately 1.0. The tests also invoke real decorated
Mantle tools through a loopback worker. The cold-archive test skips until trained.

Pins checked on 11 October 2026: Rasa Pro 3.21.0.dev5, typesafe-sdk 0.7.4,
Jev model `jev-1.13.0`. The locks record dependency distributions and hashes.
See [TypeSafe's Python SDK](https://docs.typesafe.ai/sdk/python) and
[model reference](https://docs.typesafe.ai/models).

## Add the Rasa conversation

In one terminal, from `mantle`, keep the worker running:

```sh
make worker
```

This mode scripts the account selection. It does not interpret arbitrary phrases.
In another terminal in the same directory, supply your issued Rasa licence and
writer provider key as environment variables. `.env.example` lists their names;
these commands do not automatically load an `.env` file.

```sh
make validate
make train
make run
```

The REST server listens on loopback port 5030. Send a public fictional demo code,
then request transactions. These are proposed user messages, not a recorded run:

```sh
curl -s http://127.0.0.1:5030/webhooks/rest/webhook \
  -H 'Content-Type: application/json' \
  -d '{"sender":"jev-demo-a","message":"Use demo 111111"}'
curl -s http://127.0.0.1:5030/webhooks/rest/webhook \
  -H 'Content-Type: application/json' \
  -d '{"sender":"jev-demo-a","message":"Show my current account transactions"}'
```

## Use the actual Jev service

Stop the scripted worker with Ctrl-C. Supply `TYPESAFE_API_KEY` to the worker's
environment and run `make worker-live`. Only this explicit mode sends paid Jev
requests. The model and API origin are fixed in source; ambient model/base-URL
overrides cannot redirect the request. A two-second SDK HTTP timeout and disabled
automatic retries bound each attempt. This is not a total conversational deadline.

Each admitted worker request makes one SDK call. Mantle may make additional
model/tool calls: this project does not promise one writer call per turn.
The returned decision includes the resolved model, confidence, probabilities and
provider token counts when present. Missing counts remain null. Keep measured
runs and billing records in private storage, not this public example repository.
Measure first useful answer separately from an acknowledgement.

## Where the checks belong

`worker/jacaranda_jev/accounts.py` filters account options for the selected demo
and rechecks their revision and eligibility inside the read. `selector.py` checks
the returned choice, probability keys, numerical bounds and model identity.
The account IDs never become tool arguments supplied by Mantle's model.

These public fixture codes and REST sender labels do not authenticate a person.
The worker has no authentication and contains only fictional rows. Use it only
on loopback. A real service needs an authenticated principal from the channel,
an authorised data service and durable state with atomic checks. Restarting the
worker or Rasa process resets their in-memory demo state.

Confidence summarises a distribution; it does not authorise a read or prove that
the customer meant the selected account. There is no unqualified global cutoff
in this example. Jev can pick `ask_customer`; real model evaluation must check
whether it does so appropriately on ambiguous requests.

## Stop and rebuild

Ctrl-C stops each foreground service and closes the worker's SDK client. Retain
the source, `pyproject.toml` and `uv.lock`; recreate only the selected environment
with `uv sync --locked --prerelease=allow`. Never copy `.venv`, models or local
credentials into another tutorial or backup. Readers who only want the native
exercise can install `worker` separately; Mantle's environment already includes it.
