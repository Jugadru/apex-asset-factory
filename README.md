# APEX Asset Factory — v0.2.1 era vehicle candidate

Independent graphics production infrastructure for APEX. Owner: Jugadru. Original procedural assets only until license and promotion gates pass. Source: [APEX-Simulation #184](https://github.com/Jugadru/APEX-Simulation/pull/184), exact SHA `f878b09aa5d66ef7d8302b2d94aa2a8d7db9c59b`. Foundation and Graphics Lab helpers are pinned copies for offline execution, not separate authorities.

## Run
Python 3.10+, trusted Blender 5.3.x and Godot 4.7.2.x supplied locally. Use a new workspace outside checkout.

```sh
python3 -m unittest discover -s tools/tests -v
python3 tools/apex_foundation.py validate
python3 tools/asset_factory/build.py tools/asset_factory/demo.json --blender /path/to/blender --godot /path/to/godot --workspace /tmp/apex-asset-demo-new --capture
```

Capture requires Xvfb or working display; software rendering is not physical GPU QA. Produces original low-poly GLB, isolated Godot project, logs, optional PNG and per-run registry; no automatic promotion. Prior native evidence is historical. No executables or unapproved asset binaries stored here. No public distribution license selected yet.

Read [AGENTS](AGENTS.md), [BLOCKERS](BLOCKERS.md), [ROADMAP](ROADMAP.md), [upstream provenance](docs/UPSTREAM.md), [pipeline](docs/references/ASSET_FACTORY_010.md), [catalog](docs/references/README.md). This repository is public: no private data, credentials, proprietary or unapproved assets.

## Continue development
Read [handoff](docs/HANDOFF.md), [runtime inventory and archive SHA256](docs/RUNTIMES.md), [read-only upstream contract snapshots](docs/upstream-snapshot/README.md), [native migration evidence](evidence/v0.1.0-migration/README.md) and [live blockers](https://github.com/Jugadru/apex-asset-factory/issues/2).

## v0.1.1 validation
See [advanced validator](docs/ADVANCED_VALIDATOR.md). The new GLB checks run before Godot import. Original v0.1.0 migration proof is retained in Git history. Native validation of this candidate is pending.

## Hyper infrastructure
[Operator procedures](docs/HYPER_UPDATE.md) · [blocker tracker](docs/blockers.json) · [native evidence](evidence/v0.1.5-native/summary.json). Four native builds passed with exact source subset; full local checkout and physical GPU remain pending. No asset promotion.

## Modular vehicles
[New vehicle profile and commands](docs/MODULAR_VEHICLE.md) · [native results](evidence/v0.2.0-native/summary.json). Legacy request v1 remains supported. No production promotion.

## Era profiles
[Era geometry and requests](docs/ERA_VEHICLES.md) · [native evidence](evidence/v0.2.1-native/summary.json). Three original stylized open-wheel eras; no replicas, GT or sporting changes.

## Cockpit & suspension detail
[Schema 4 and native evidence](docs/DETAIL_VEHICLES.md) · [summary](evidence/v0.2.1.1-native/summary.json). Visual geometry only, no sporting changes.

## Closed-wheel vehicles
[GT and endurance schema 5](docs/CLOSED_WHEEL_VEHICLES.md) · [native evidence](evidence/v0.2.1.2-native/summary.json). Original visual prototypes only.

## Automatic LOD
[Procedure and scope](docs/AUTOMATIC_LOD.md) · [native evidence](evidence/v0.2.2-native/summary.json). Three detail levels; no game integration or promotion.
