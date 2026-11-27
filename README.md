# APEX Asset Factory — v0.1.0 candidate

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
