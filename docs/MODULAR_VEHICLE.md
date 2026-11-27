# v0.2.0 — Modular Vehicle Generator (candidate)

This is an original geometry-only open-wheel profile, no racing behavior or licensed replica. Keep v1 request/legacy generator working. Schema 2 introduces three body profiles (balanced, low-drag, high-downforce, names describe appearance only) and two tire widths. Seed changes symmetric chassis geometry, not just paint. Geometry is designed directly in requested metres, without global anisotropic scale. Wheels are circular cylinders with centers at radius height, hub center and axle aligned; local Z rotation axis in Blender (export transforms must still be inspected in Godot). Exact analytic envelope and component names validated, 48 profile/dimension combinations in tests. Hubs are solid visual proxies, not mechanically detailed tire assemblies. UV overlap, mesh QA after import, native generation and visual/physical GPU inspection require real runs.

```sh
python3 -m unittest discover -s tools/tests -v
python3 tools/asset_factory/build.py tools/asset_factory/demo_modular.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-modular-020-new --capture
```

The build retains structural validator, Godot envelope test, isolated workspaces and blocked promotion. Report records component layout and generator dependencies. No LOD, texture maps, GT, animation or game integration implemented. AF-B009 and B017 partial until native mesh/pivot verification and visual acceptance. Original v0.1.5 native evidence remains historical; no native PASS for this candidate until executed.
