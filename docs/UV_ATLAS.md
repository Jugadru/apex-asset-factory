# v0.3.0.3 — Secondary UV atlas (candidate)

Opt-in `--uv-atlas` with `--repair-uv`; existing PBR texture size and texture coordinates remain unchanged. GLB TEXCOORD_1 maps to Blender's second UV layer and Godot UV2. The source is the repaired GLB, not a replacement for the original generator. The strict old validator still rejects secondary layers unless explicitly opted in.

Every indexed triangle gets a deterministic separate grid cell, with 2 px minimum padding on each edge at the selected reference resolution (1024/2048/4096). Triangle-local planar projection preserves shape within floating-point tolerance, but uniform cells do not preserve global texel density. The audit validates serialized UV2 cell bounds, triangle count and positive area, records coverage, minimum altitude/edge, subpixel counts, local texels per unit and repeated mesh instances. Non-overlap covers unique mesh primitives only, not multiple instances of a mesh. Splitting corners increases vertices and may affect tangent smoothing; native import gates do not prove visual equivalence or imported non-overlap. Existing textures still use TEXCOORD_0. No high-poly baking, artistic unwrap, AO, GPU performance, or game integration claimed.

```sh
PYTHONPATH="$PWD/tools" python3 -m asset_factory.stage_pbr /tmp/original-build --source-sha256 EXACT_SHA --blender /absolute/blender --godot /absolute/godot --workspace /tmp/new-atlas --repair-uv --normal-maps --uv-atlas --atlas-resolution 2048 --size 256
```

Native evidence: NOT_RUN. CI: pending on candidate commit. Promotion BLOCKED. Before baking, improve continuous chart packing, density, seam behavior and validate imported precision and visual A/B across all vehicle LODs. Rollback by closing/reverting this stacked PR; no game repo modifications.
