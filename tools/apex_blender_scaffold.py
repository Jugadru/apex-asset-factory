"""Original geometric test asset; run only in a disposable Blender process."""
import argparse
from pathlib import Path
import sys
import bpy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    out = args.output
    if out.suffix.lower() != ".glb" or out.exists() or out.is_symlink():
        raise ValueError("new .glb required; never overwrite")
    if not out.parent.is_dir():
        raise ValueError("existing staging directory required")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    def box(name, loc, dims):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        ob = bpy.context.object
        ob.name = name
        ob.dimensions = dims
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    box("Body", (0,0,.44), (1.4,3.4,.42))
    box("Nose", (0,1.85,.38), (.5,.7,.3))
    box("FrontWing", (0,2.1,.25), (1.8,.35,.12))
    box("RearWing", (0,-1.7,.95), (1.5,.35,.12))
    for x in (-.86,.86):
        for y in (-1.23,1.25):
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=.31, depth=.28, location=(x,y,.31), rotation=(0,1.57079632679,0))
            bpy.context.object.name = "Wheel_%s_%s" % ("L" if x<0 else "R","F" if y>0 else "R")
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB")
    if not out.is_file() or out.stat().st_size < 20:
        raise RuntimeError("export absent")
    print("APEX_DEMO_EXPORTED; Godot import and visual QA NOT_RUN")
if __name__ == "__main__":
    main()
