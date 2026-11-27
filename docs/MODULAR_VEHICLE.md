# v0.2.0 — Modular Vehicle Generator (candidate)

This is an original geometry-only open-wheel profile, no racing behavior or licensed replica. Keep v1 request/legacy generator working. Schema 2 introduces three body profiles (balanced, low-drag, high-downforce, names describe appearance only) and two tire widths. Seed changes symmetric chassis geometry, not just paint. Geometry is designed directly in requested metres, without global anisotropic scale. Wheels are circular cylinders with centers at radius height, hub center and axle aligned; local Z rotation axis in Blender (glTF local Y axis checked after export). Exact analytic envelope and component names validated, 48 profile/dimension combinations in tests. Hubs are solid visual proxies, not mechanically detailed tire assemblies. The post-export QA checks wheel and hub positions, matching orientation, transverse axis, unit scale, actual radial geometry and axial width; it rejects defects before Godot import. UV overlap, Godot pivot articulation and visual/physical GPU review remain separate.

```sh
python3 -m unittest discover -s tools/tests -v
python3 tools/asset_factory/build.py tools/asset_factory/demo_modular.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-modular-020-new --capture
```

The build retains structural validator, Godot envelope test, isolated workspaces and blocked promotion. Report records component layout and generator dependencies. No LOD, texture maps, GT, animation or game integration implemented. AF-B009 and B017 partial until native mesh/pivot verification and visual acceptance. Original v0.1.5 native evidence remains historical; no native PASS for this candidate until executed.

## Evidence
34 Python tests (48 layout combinations); two complete final balanced native builds passed all stages including wheel/hub checks and produced equal GLB/PNG hashes. An earlier wide build passed and its GLB passed final standalone wheel QA. A subsequent batch timed out during final wide capture, so final wide, low-drag and legacy native rerun remain incomplete. Earlier comparison showed binary differences at 5.96e-8, so general byte determinism is not claimed. See [summary](../evidence/v0.2.0-native/summary.json). User visual acceptance and physical GPU remain pending.
