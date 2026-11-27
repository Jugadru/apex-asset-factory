# Hyper infrastructure update — v0.1.2 through v0.1.5 (candidate)

Owner asked for a combined update; retain one main capability per commit and independent acceptance. Stacked on #3 and #1, no automatic merge. This is not a production release or a claim that all blockers are solved.

## Commands (Linux, repository root, clean checkout)
Use an external private workspace. Keep binaries and keys outside Git.

```sh
export PYTHONPATH="$PWD/tools"
python3 -m unittest discover -s tools/tests -v
python3 tools/check_blockers.py
python3 -m asset_factory.native_acceptance --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-native-015-new --capture
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite register /tmp/apex-native-015-new/seed-2012-run-1
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite audit
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite list
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite backup /tmp/apex-assets-snapshot.sqlite
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite select apex-openwheel-demo 0.1.0 'manual selection'
python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite current apex-openwheel-demo
```

The native harness does two seeds × two builds, verifies exact source checkout, stores receipts and compares the outputs with numeric tolerance while preserving individual hashes. Do not register both repeated outputs as the same id/version if their binary hashes differ. New version required for a different approved artifact. Test physical GPU separately in game; native harness uses Compatibility/Xvfb for capture and does not benchmark physical GPU.

## Local approval (only when owner has reviewed rights and the exact model)
Create the signing key outside repository, never send the private key or credentials in chat. Example with OpenSSL 3:
```sh
umask 077
mkdir -p "$HOME/.apex-asset-keys"
openssl genpkey -algorithm ED25519 -out "$HOME/.apex-asset-keys/owner.pem"
openssl pkey -in "$HOME/.apex-asset-keys/owner.pem" -pubout -out "$HOME/.apex-asset-keys/owner-public.pem"
sha256sum "$HOME/.apex-asset-keys/owner-public.pem"
```
Record the public-key fingerprint separately as a trusted owner decision; never accept an arbitrary key supplied by a job. Create an approval statement using `python3 -m asset_factory.release --db /tmp/apex-assets.sqlite statement apex-openwheel-demo 0.1.0 --rights 'actual rights record' --review 'actual review record'`, save JSON privately, inspect it, sign the exact bytes with `openssl pkeyutl -sign -inkey "$HOME/.apex-asset-keys/owner.pem" -rawin -in approval.json -out approval.sig`. Run the release module's package subcommand with `--approval`, `--signature`, `--key`, `--key-sha256`, `--out`. This prepares only a local integration package; publication and game integration remain blocked. Approval is scoped to asset hash, request hash, revision, identity, version and license. Revocation appends an immutable event and blocks future packaging, but cannot recall already exported bytes. SQLite is local, trusted OS user only, not tamper-proof against privileged DB modifications; backup/restore and explicit local version selection are tested; prebuild reservations are append-only and released explicitly after a failed job; multi-host registry remains pending.

## Lab and safety
`python3 -m asset_factory.bridge plan tools/asset_factory/demo.json --revision EXACT_SHA --job-id example` yields a non-executing plan. Receipt correlation checks repo, job, SHA, request hash, evidence URL/hash; it does not authenticate agent or verify evidence online. Foundation #177 closed unmerged, #192 is a documentary successor not a runtime integration. Keep canonical contracts with upstream. No remote dispatch or permanent services. Secure runner filters inherited env, uses isolated HOME, resource/file/CPU limits, timeout and process-group cleanup; **not** a hostile-code sandbox, RAM/global disk/network limits are still required, only trusted executables. Hosted CI is Python + synthetic fixtures, native acceptance requires supplied verified Blender/Godot paths; no GPU claims.

## Ledger
`docs/blockers.json` preserves 24 IDs, scopes, target versions, historical evidence and current limitations; CI checks structure, not truth of linked results. [Issue #2](https://github.com/Jugadru/apex-asset-factory/issues/2) remains discussion log. No new asset library, models, sounds or game code published. No hidden service, no personal runner.

## Native evidence
[Summary](../evidence/v0.1.5-native/summary.json): four native builds from ten exact source blobs; both seeds and historical numeric comparison PASS. Wrapper and full local checkout remain pending; raw logs and generated assets retained in private evidence ZIP. CI 46018529079 (27 tests) validates local registry and backup/recovery separately.

Before building, reserve identity using `python3 -m asset_factory.registry --db /tmp/apex-assets.sqlite reserve tools/asset_factory/demo.json`. Registration consumes the reservation (or creates one atomically for backward compatibility). A failed build can be released by `release-reservation REQUEST REASON` from the same source revision; conflicting request/version rejected. Inspect history with `reservations ID VERSION`. No lease expiry or distributed scheduling implied.

Registry follow-up: prebuild reservation, release and consumption verified in CI 46019032367 (28 tests). AF-B012 PASS for the single-host scope; no distributed scheduler or automatic remote execution.
