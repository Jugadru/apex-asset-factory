# v0.2.1 — Era Vehicle Profiles (candidate)

Original, stylized open-wheel silhouettes inspired by 1990, 2012 and 2020; not replicas or official specifications. Retains v1/v2 requests. New schema 3 and separate Blender adapter; rounded octagonal loft, tapered sidepods/airbox/cockpit proxy, profiled wings, smooth cylindrical tire tread. Geometry dimensions, wheel axes, registry and promotion controls remain. Names are visual only, no sporting changes. Tests cover 144 era/body/tire/dimension combinations and closed mesh topology. This is the first multi-era increment; GT/endurance, detailed cockpit cavity, true halo, decals, material maps, LOD and commercial-quality art remain pending.

```sh
python3 tools/asset_factory/build.py tools/asset_factory/demo_era.json --blender /absolute/path/blender --godot /absolute/path/godot --workspace /tmp/apex-era-021-new --capture
```

Native evidence pending until actual runs. No production approval or publication.

## Evidence
CI 46064098481: 37 tests PASS; 144 analytic combinations. Three separate actual Blender/Godot builds PASS with 19 exact Git blobs, all 3072 triangles and 36 meshes, radial error below 1e-6 m; real software-rendered 960×540 capture each. New schema repeatability, full local checkout, physical GPU, game integration and user visual acceptance remain NOT_RUN. Private raw evidence archive (115 files) provided in chat; no binaries published. [Summary](../evidence/v0.2.1-native/summary.json).
