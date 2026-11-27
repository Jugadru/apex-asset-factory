# v0.1.1 — Advanced Asset Validator (candidate)

AF-B007, AF-B008, AF-B009 (partial), AF-B021 (partial). The new validator runs before Godot import and fails closed on unsupported GLB features. The supported subset is static, untextured, indexed triangles with POSITION/NORMAL/TEXCOORD_0, one embedded BIN buffer, no extensions, four named wheel nodes, one reachable scene. It bounds file/JSON size, records and decoded rows; checks chunks, duplicate keys, finite binary data, ranges, offsets, stride/alignment, actual declared min/max, indices, counts, unit normals, zero-area triangles, basic PBR values, node references, cycles and coverage. It is not a full Khronos validator; future textured/skinned/animated assets require additional profiles. UV overlap, winding vs normals, near-degenerate thresholds, wheel pivots, geometry scale/placement, material quality, and physical GPU remain NOT_RUN.

```sh
python3 tools/asset_factory/validate_glb.py /path/asset.glb --budget 8000
python3 tools/asset_factory/validate_glb.py /path/first.glb --compare /path/second.glb --budget 8000
python3 -m unittest discover -s tools/tests -v
```
Comparison reports binary identity separately from same-layout numeric equivalence (absolute tolerance default 1e-6, capped at 1e-4; integer indices exact). No arbitrary mesh equivalence, no canonicalization or byte reproducibility claim. Changes to ordering/metadata can fail comparison intentionally. Native repeat execution and representative multiple seeds still needed. Original migration manifest retained: intentionally evolved build.py verified against historical Git object; all other imported blobs verified in current checkout. CI fetches full history, tests stacked PR base migration/v0.1.0 and main. No automatic promotion, no game change.
