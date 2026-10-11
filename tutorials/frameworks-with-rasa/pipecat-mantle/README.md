# Rasa dialogue for an existing Pipecat pipeline

**Author:** Rod Rivera
**Assessed on:** 2026-10-11
**Assessed by:** Cedar (Codex)
**Verified with:** pipecat-ai 1.12.0, Rasa Pro 3.21.0.dev5 and Python 3.12.13.
Seventeen native Pipecat/REST controls and five decorated Mantle controls pass.
Project validation, licensed training and cold archive loading pass separately;
see `../pipecat-verification.json` for source and dated evidence hashes.

Juniper Mobile is fictional. This public example asks the caller to choose
north or central and explains a fixed maintenance observation. It keeps
speech input, output, transport and turn aggregation in the companion
[`../pipecat`](../pipecat) project. Rasa exposes one checked public-area tool.

Use Python 3.12 and the separate locked environment:

```sh
# From the repository root:
python3 scripts/workspace.py start tutorials/frameworks-with-rasa/pipecat-mantle --owner juniper-dialogue-demo
cd tutorials/frameworks-with-rasa/pipecat-mantle
make test
make validate
```

Set `RASA_PRO_LICENSE` and `OPENAI_API_KEY` using `.env.example` as the variable
list, then run `make train` and `make run`. The REST server binds to localhost
port 5020. The Pipecat companion includes a reader-run text-frame client and a
composition function that preserves existing voice services. Compare your
model's replies with public records JM-N-101 and JM-C-102 and test missing-area
recovery before adding actual speech acceptance.

The configured REST sender is public demo state. Bind customer identity through
your actual channel's authentication and authorization before using private
records. The tool implements public lookup and a supported-choice result;
account and subscription actions need their own separately authorized tools.

After your server and requests finish, keep needed model/state/recording output,
then retire only the selected environment, from the repository root:

```sh
python3 scripts/workspace.py retire tutorials/frameworks-with-rasa/pipecat-mantle --owner juniper-dialogue-demo --inactive
```

Source, dependency manifests and the lock remain. Pipecat's lock/environment is
separate so existing media dependencies can be retained independently.
