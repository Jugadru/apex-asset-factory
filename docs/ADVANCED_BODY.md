# v0.2.3 — Advanced body modeling (candidate)

Opt-in schema 6 for original closed-wheel GT and endurance. No change to schemas 1–5 or sporting code. Replaces the prior shell/canopy profiles using shape-bounded cubic Hermite interpolation, 16-point cross-sections, denser longitudinal sampling at LOD0, and smooth arch return transitions. The GT hood height, roof cross-section and painted roof area are revised; swept headlight proxies follow interpolated hood surface. Reduced paint gloss is a simple material adjustment, not PBR textures. Separate procedural LOD surface sample densities, plus existing wheel and bevel policy. Same named components and circular wheel/hub contracts; existing GLB sampled clearance and Godot dimensions enforced. Layout validation checks 84 sampled static clearances against the newly constructed shell. No full collision certification, texture/UV acceptance, actual glass/interior, detailed wheel/brake art, full mesh self-intersection analysis or artist approval.

```sh
PYTHONPATH="$PWD/tools" python3 -m asset_factory.lod tools/asset_factory/demo_curved_gt.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-curved-lod-new --capture
```

Tests cover 96 category/tire/dimension/LOD combinations, schema compatibility, interpolation bounds and preserved wheel geometry. Native validation and artistic acceptance are separate. Owner rejected earlier prototype appearance; current model is still stylized and remains in staging, not a finished asset. No automatic merge, publication or game runtime changes.
