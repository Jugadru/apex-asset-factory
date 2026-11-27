# Foundation v0.1.0 — Shared Contracts & Capability Registry

Candidate; independent version. Source of truth remains AGENTS.md, the existing Lab index, Core 2 and Hyper roadmaps and runtime code. Read [references](../references/README.md), [Lab index](../APEX_LAB_KNOWLEDGE_INDEX.md), [SaveGuard](../APEX_SAVEGUARD_CROSS_VERSION.md). No runtime or game version change.

## Run from repository root (Python 3.10+ target)
```sh
python3 tools/apex_foundation_registry.py validate
python3 tools/apex_foundation_registry.py list
python3 tools/apex_foundation_registry.py search REF-001
python3 tools/apex_foundation_registry.py check artifact.v1 docs/foundation/artifact.example.json
python3 tools/apex_foundation_registry.py compatibility core2 03a73242b21854c22c9e0067f3192847be570de6 godot 4.7.2
python3 -m unittest discover -s tools/tests -p 'test_apex_foundation*.py' -v
python3 -m unittest discover -s tools/tests -p 'test_apex_asset_build.py' -v
```
Exit 0 structural success or recorded compatible pair; 1 incompatible/unknown pair; 2 invalid input. No execution authorization. Capability methods are descriptive, never executed by this CLI. Registry and schemas are trusted repository metadata; external JSON is bounded to 2 MiB, duplicate keys and nonfinite values rejected. No network, subprocess, write, secret or shell evaluation in this CLI. Existing Lab owner authorization and isolated staging remain mandatory. Unknown versions are blocked, not guessed. Compatibility PASS is scoped to the recorded exact pair, not other versions or all subsystems. Version null means unverified.

## Contracts
schemas.json implements a small closed JSON-schema-like dialect (type, enum, pattern via Python fullmatch, minLength, properties, required, additionalProperties=false, items, uniqueItems). It is **not** a general JSON Schema validator. Only registered metadata shapes are active; runtime commands, snapshots, events, telemetry, assets, saves, replays, benchmark/report/job payloads are deferred pending reconciliation with their owners. No runtime event bus, writer or migration engine. artifact.example.json is synthetic, not evidence. Evidence PASS must come from executed tests, not shape validation.

## Architecture and onboarding
registry.json maps module responsibility and dependencies at a coarse level; it is not an exhaustive import graph. Existing version and runtime ownership must be verified before changes. Read AGENTS, then registry, linked source and test evidence; check exact SHA, choose one change, use existing FAST, report status and rollback. Search retains REF/IDEA IDs and original records; append new IDs, never recycle. No licenses were revalidated.

## Roadmap (independent, provisional)
0.1.x: catalog provenance, explicit module versions and contract ownership; 0.2: content/data and configuration contracts with historical/fictitious/estimated/scientific origin; 0.3: SaveGuard/replay adapters, evidence registry and migration records; 0.4: modding metadata and scoped permissions. Do not implement runtime features or duplicate current tools. Split repository only after two independent consumers need pinned releases, contract format stabilizes, independent CI/ownership exists and migration/rollback are proven; publish immutable versioned artifacts and keep links in main. No split now.

## Acceptance / rollback
Validate historical IDs and cross-links, schemas and registry, reject invalid inputs and unknown pairs, run legacy Foundation and Asset Factory unit tests and exact-SHA FAST. Native Blender/GLB import and cross-revision SaveGuard are not proven by metadata validation. Logs retained by existing CI. Revert the increment commit to restore prior PR; no runtime or saves touched. Original FAST run 45920592893 passed on 03a73242b21854c22c9e0067f3192847be570de6; new revision results must be checked separately.
