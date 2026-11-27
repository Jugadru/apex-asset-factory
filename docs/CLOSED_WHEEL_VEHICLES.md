# v0.2.1.2 — Closed-wheel GT and Endurance (candidate)

New schema 5 adds two original closed-wheel categories with different continuous body and canopy profiles. Existing schemas 1–4 remain unchanged. Longitudinal stations include wheel-arch contours; shell, canopy and wing are closed shaped meshes. GT painted roof panel, prototype dorsal fin, grille, lights, splitter and diffuser are stylized proxies. Static sampled shell clearance is checked analytically and on the exported GLB (up to 84 vertical samples), and circular wheel/hub QA is retained. The test does not certify collisions, moving suspension, aerodynamics or every point of the shell. The glass material is opaque, no interior, decals, detailed rims, textures, UV packing, LOD or production-quality art. No licensed replica or sporting changes.

```sh
python3 tools/asset_factory/build.py tools/asset_factory/demo_gt.json --blender /path/blender --godot /path/godot --workspace /tmp/apex-gt-new --capture
python3 tools/asset_factory/build.py tools/asset_factory/demo_endurance.json --blender /path/blender --godot /path/godot --workspace /tmp/apex-endurance-new --capture
```

Original geometry dimensions restricted to width 1.7–2.3 m, length 4–5.5 m and height 1–1.5 m. Tests cover 32 category/tire/dimension extrema and reject deliberate shell penetration. Factory version 0.2.1.2; distinct asset IDs use three-segment asset version 0.2.1. No promotion or release without human review.

## Native evidence
45 CI tests PASS (run 46067553615); both final native Blender/Godot builds PASS with 16 exact Git source/request blobs verified, 84 wheel-arch samples each. Min sampled clearances: GT 0.039618 m; endurance 0.035640 m. 3888/3956 triangles, 26/27 meshes. Private evidence ZIP contains 45 files, CRC verified; SHA in [summary](../evidence/v0.2.1.2-native/summary.json). Previous user visual rejection is recorded; new models are not artistic-approved. No full local clone, repeatability, physical GPU, game integration, actual collision or publication.
