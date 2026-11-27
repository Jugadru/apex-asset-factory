# v0.2.2 — Automatic procedural LOD (candidate)

Schemas 2–5 (modular, era, detail, GT/endurance) generate independent LOD0/1/2 GLBs. The original schema 1 remains a primary-only generator. This is procedural regeneration, not arbitrary third-party mesh decimation. LOD0 retains the original geometry. LOD1 reduces cylinder tessellation to at most 24 sides and bevel segments to one; LOD2 uses at most 12 cylinder sides and removes bevels from box primitives. The main shaped shell, cockpit geometry, named components, wheel/hub pivots and material assignment are retained. No global scaling or node deletion. The wheel polygon silhouette is intentionally simpler at distance; existing wheel QA verifies radius at vertices, not perfectly circular edges.

```sh
export PYTHONPATH="$PWD/tools"
python3 -m asset_factory.lod tools/asset_factory/demo_gt.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-lod-gt-new --capture
```

Each build runs existing GLB and category QA plus Godot import; manifest stores hashes, triangle counts, bytes and report hashes. Set gate requires monotonic triangle counts, at least 10% reduction at LOD1 and 25% at LOD2, same named component set, Godot mesh/material counts and envelope within 0.5% of LOD0. The separate staging Godot test imports all three variants, changes one visible root using camera distance with 25/70 m nominal thresholds and ±3 m hysteresis, and verifies 11 distance transitions including teleport. These are illustrative thresholds, not a tuned gameplay setting. All variants are instantiated in the fixture; no memory savings, real GPU, FPS, in-game integration or production visibility behavior is claimed. No automatic publication. Individual derived LOD reports are rejected by the primary registry; asset-set packaging and owner approval for all variant hashes are still pending. This is not a renderer benchmark and does not fix artistic quality. No textures, UV packing or generic mesh simplification yet.

A timeout or failed gate leaves the partial workspace for inspection; use a new workspace for a full rerun. Do not overwrite existing results. Native test evidence must be distinguished from synthetic unit tests.

## Native evidence
51 CI tests PASS (46069667234), 33 exact source blobs checked. Nine Blender/Godot builds and three 11-step standalone switch fixtures PASS. GT 3888→2480→1712; endurance 3956→2548→1780; openwheel 3608→2712→2072. GT all three captures PASS; other sets headless only. Openwheel full orchestrator PASS. GT and endurance outer timeouts recovered via separate exact scripts/new workspace; no claim all three orchestrators ran uninterrupted. Schema 2/3 native LOD not yet run; policy unit tests PASS. Raw private archive 146 files, CRC checked. See [summary](../evidence/v0.2.2-native/summary.json).
