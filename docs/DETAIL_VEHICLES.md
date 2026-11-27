# v0.2.1.1 — Cockpit and Suspension Detail (candidate)
Schema 4 uses separate generator, preserving v1-v3. Replaces former solid cockpit proxy with a recessed chassis surface, seat/backrest, steering rim/display. 2020-inspired profile has a halo proxy; older eras do not. Four visual suspension links and a pushrod per wheel, with inboard mounts interpolated from chassis. No collision, physics, articulated suspension, driver rig or safety certification. New export QA verifies exact component coverage and samples recessed cockpit floor on the actual GLB; existing wheel QA retained. Shape geometry tested across 144 combinations; native evidence must be recorded separately. Asset version field remains three segments (demo ID apex-detail-demo version 0.2.1), factory version is 0.2.1.1. No production promotion.
```sh
python3 tools/asset_factory/build.py tools/asset_factory/demo_detail.json --blender /path/blender --godot /path/godot --workspace /tmp/apex-detail-new --capture
```
