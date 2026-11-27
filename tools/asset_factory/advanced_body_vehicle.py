"""Blender adapter for original curved closed-wheel profiles."""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from advanced_body_layout import design,validate_layout

from lod_policy import apply_policy, bevel_segments

def main():
    import bpy
    p=argparse.ArgumentParser()
    p.add_argument("--request",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--derived-lod",type=int,choices=(0,1,2),default=0)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    r=json.loads(a.request.read_text())
    if a.output.exists() or a.output.is_symlink() or a.output.suffix!=".glb":
        raise ValueError("new GLB required")
    parts=design(r,a.derived_lod)
    qa=validate_layout(parts,r)
    parts=apply_policy(parts,a.derived_lod)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mats={}
    for name,rgb,metal,rough in (
        ("paint",r["paint_rgb"],.18,.42),("carbon",(.025,.027,.03),.15,.4),
        ("rubber",(.012,.013,.014),0,.85),("metal",(.24,.26,.28),.8,.3),
        ("accent",(.65,.45,.08),.3,.32),("glass",(.018,.035,.055),.40,.16),
        ("light",(.72,.84,.96),.25,.18),("tail",(.55,.015,.025),.15,.25)):
        m=bpy.data.materials.new(name)
        m.use_nodes=True
        bs=m.node_tree.nodes.get("Principled BSDF")
        bs.inputs["Base Color"].default_value=(*rgb,1)
        bs.inputs["Metallic"].default_value=metal
        bs.inputs["Roughness"].default_value=rough
        m.diffuse_color=(*rgb,1)
        mats[name]=m
    for part in parts:
        kind=part["kind"]
        if kind=="box":
            bpy.ops.mesh.primitive_cube_add(size=1,location=part["center"])
            ob=bpy.context.object
            ob.dimensions=part["size"]
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            if part["bevel"]:
                mod=ob.modifiers.new("Edge_bevel","BEVEL")
                mod.width=min(part["bevel"],min(part["size"])*.2)
                mod.segments=bevel_segments(a.derived_lod)
                bpy.ops.object.modifier_apply(modifier=mod.name)
        elif kind=="cylinder":
            bpy.ops.mesh.primitive_cylinder_add(vertices=part["sides"],radius=part["radius"],
                depth=part["width"],location=part["center"],rotation=(0,math.pi/2,0))
            ob=bpy.context.object
            # Local Z is rotation axle, origin is at the hub center.
        else:
            verts,faces=part["vertices"],part["faces"]
            # Recalculate consistent outward normals explicitly.
            mesh=bpy.data.meshes.new(part["name"])
            mesh.from_pydata(verts,[],faces)
            mesh.update()
            import bmesh
            bm=bmesh.new()
            bm.from_mesh(mesh)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(mesh)
            bm.free()
            ob=bpy.data.objects.new(part["name"],mesh)
            bpy.context.collection.objects.link(ob)
            if part.get("smooth"):
                for poly in mesh.polygons:
                    poly.use_smooth=len(poly.vertices)==4
            uv=mesh.uv_layers.new(name="UVMap")
            for poly in mesh.polygons:
                for idx in poly.loop_indices:
                    x,y,z=mesh.vertices[mesh.loops[idx].vertex_index].co
                    uv.data[idx].uv=((x+2)/4,(y+4)/8) if abs(poly.normal.z)>.5 else ((y+4)/8,z/2)
        if kind=="cylinder":
            for poly in ob.data.polygons:
                if len(poly.vertices)==4:
                    poly.use_smooth=True
        ob.name=part["name"]
        ob.data.materials.append(mats[part["material"]])
        if part["name"]=="Canopy" and r["category"]=="gt":
            ob.data.materials.append(mats["paint"])
            for poly in ob.data.polygons:
                if poly.normal.z>.52 and -.17*r["dimensions_m"]["length"]<poly.center.y<.075*r["dimensions_m"]["length"]:
                    poly.material_index=1
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(a.output),export_format="GLB",export_yup=True,
                             export_normals=True,export_texcoords=True)
    print("APEX_ADVANCED_BODY_LAYOUT",json.dumps(qa,sort_keys=True))

if __name__=="__main__":
    main()
