# v0.2.4.1 — Open-wheel era-specific wheel assemblies

Opt-in schema 8 extends the detailed schema 4 body, preserves the cockpit/halo and suspension geometry, axle centers, tire envelope and prior schemas 1–7. Seven named parts per wheel. Three original visual profiles: 1990-inspired 5 spokes and rim radius 0.56 of tire radius; 2012-inspired 6 and 0.60; 2020-inspired 8 and 0.64. These are artistic parameters, not actual historical specifications. The inward hub sleeve reaches the existing visual suspension end points; this is not a mechanical articulation or contact certification. LOD0/1/2 use 48/24/12 radial samples and 3/2/1 spoke sector steps. Existing exact exported vertex, pivot, material, chassis cavity and semantic LOD identity gates reused.

The isolated wheel preview now selects the seven exact names rather than a suffix shared with suspension nodes. The original failed preview remains in private evidence. No texture, UV packing, dynamic movement, sporting, licensed replicas, artist approval, physical GPU or game integration claims. No automatic merge or asset promotion.

```sh
PYTHONPATH="$PWD/tools" python3 -m asset_factory.lod tools/asset_factory/demo_wheel_2012.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-openwheel-lod-new
```

432 analytic combinations (three eras, three body profiles, two tire widths, eight dimension extrema and three LODs); native test results are separately recorded. Existing CI branch filter expanded to the stacked base only.
