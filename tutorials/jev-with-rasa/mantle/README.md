# Jacaranda Bank conversation with a Jev account selector

Start with [the full walkthrough](../README.md). This project keeps Mantle's
ordinary orchestrator and calls a bounded local Laya or optional hosted Jev worker through decorated tools.
The account choices and transaction rows are fictional. Public demo labels do
not authenticate a customer.

**Author:** Rod Rivera
**Assessed on:** 2026-10-11
**Assessed by:** Scripted TypeSafe SDK controls and decorated Mantle tool bindings
**Verified with:** Rasa Pro 3.21.0.dev5, typesafe-sdk 0.7.4 and Python 3.12.13.
The initial offline run passed 22 controls; the cold-archive control needs
licensed training first. Jev responses were scripted through the actual SDK.

Run `make install`, `make demo` and `make test` here. `make worker` serves scripted
SDK responses; `make worker-local` uses the separately running pinned Laya model; `make worker-live` requires `TYPESAFE_API_KEY` and sends paid Jev
requests. `make train` requires an issued Rasa licence and `OPENAI_API_KEY`;
`make run` serves the REST conversation on loopback port 5030. Keep the selected
worker running on loopback port 5029. `.env.example` lists the variable names.

The tests check TypeSafe request/response wiring, account membership and revision
checks, sender binding, unavailable services and the loaded trained archive.
The archive test skips until you run training. Qualify actual model selection
and conversation behaviour separately with your own requests. Retain both
projects' locks, and create an environment only for the project you run.
