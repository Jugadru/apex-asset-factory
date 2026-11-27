# v0.2.3 — Advanced body modeling (candidate)

Opt-in schema 6 for original closed-wheel GT and endurance. No change to schemas 1–5 or sporting code. Replaces the prior shell/canopy profiles using shape-bounded cubic Hermite interpolation, 16-point cross-sections, denser longitudinal sampling at LOD0, and smooth arch return transitions. The GT hood height, roof cross-section and painted roof area are revised; swept headlight proxies follow interpolated hood surface. Reduced paint gloss is a simple material adjustment, not PBR textures. Separate procedural LOD surface sample densities, plus existing wheel and bevel policy. Same named components and circular wheel/hub contracts; existing GLB sampled clearance and Godot dimensions enforced. Layout validation checks 84 sampled static clearances against the newly constructed shell. No full collision certification, texture/UV acceptance, actual glass/interior, detailed wheel/brake art, full mesh self-intersection analysis or artist approval.

```sh
PYTHONPATH="$PWD/tools" python3 -m asset_factory.lod tools/asset_factory/demo_curved_gt.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-curved-lod-new --capture
```

Tests cover 96 category/tire/dimension/LOD combinations, schema compatibility, interpolation bounds and preserved wheel geometry. Native validation and artistic acceptance are separate. Owner rejected earlier prototype appearance; current model is still stylized and remains in staging, not a finished asset. No automatic merge, publication or game runtime changes.

## Native results
55 CI tests PASS (46071164548), 38 exact local Git source files verified. GT LOD0/1/2 6888/3944/2600 triangles and 26 components, endurance LOD0 6924 triangles/27 components. Four independent builds PASS including sampled wheel clearance; GT LOD0 and endurance captures PASS. Separate GT Godot import/switch and compare_levels gates PASS, not a full uninterrupted build_set run. Endurance lower native LODs and repeatability NOT_RUN. Initial GT capture retained as pre-revision history; final shape remains stylized. Private raw evidence archive 114 files, CRC checked, excludes runtime cache. [Summary](../evidence/v0.2.3-native/summary.json).
