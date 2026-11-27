# v0.2.1.1 — Cockpit and Suspension Detail (candidate)
Schema 4 uses separate generator, preserving v1-v3. Replaces former solid cockpit proxy with a recessed chassis surface, seat/backrest, steering rim/display. 2020-inspired profile has a halo proxy; older eras do not. Four visual suspension links and a pushrod per wheel, with inboard mounts interpolated from chassis. No collision, physics, articulated suspension, driver rig or safety certification. New export QA verifies exact component coverage and samples recessed cockpit floor on the actual GLB; existing wheel QA retained. Shape geometry tested across 144 combinations; native evidence must be recorded separately. Asset version field remains three segments (demo ID apex-detail-demo version 0.2.1), factory version is 0.2.1.1. No production promotion.
```sh
python3 tools/asset_factory/build.py tools/asset_factory/demo_detail.json --blender /path/blender --godot /path/godot --workspace /tmp/apex-detail-new --capture
```

## Native results
CI 46065737135: 41 tests PASS; 144 analytic combinations. Four separate actual Blender/Godot builds PASS using 24 exact source blobs, 3436–3608 triangles, 51–53 meshes. Three sampled cavity depths per build, all pass; halo only 2020. Two 2020 GLBs and PNGs byte-identical; no broader determinism claim. Private evidence ZIP 89 files, CRC checked, SHA in [summary](../evidence/v0.2.1.1-native/summary.json). Full local clone, GPU physical, visual acceptance, UV overlap and game integration remain pending.
