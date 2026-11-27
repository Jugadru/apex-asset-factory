"""Original low-poly open-wheel demonstrator. Blender trusted script."""
import argparse
import json
import math
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index("--")+1:])
    r = json.loads(a.request.read_text())
    if a.output.exists() or a.output.is_symlink() or a.output.suffix != ".glb":
        raise ValueError("new GLB required")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    rng = random.Random(r["seed"])
    def mat(name, rgb, metal, rough):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bs = m.node_tree.nodes.get("Principled BSDF")
        bs.inputs["Base Color"].default_value = (*rgb, 1)
        bs.inputs["Metallic"].default_value = metal
        bs.inputs["Roughness"].default_value = rough
        m.diffuse_color = (*rgb, 1)
        return m
    paint = mat("Paint", r["paint_rgb"], .35, .25)
    carbon = mat("Carbon_proxy", (.025,.027,.03), .15,.4)
    rubber = mat("Rubber", (.012,.013,.014), 0,.85)
    metal = mat("Metal", (.24,.26,.28), .8,.3)
    accent = mat("Accent", (.65, .42+rng.random()*.15, .08), .3,.32)
    def finish(name, material):
        ob = bpy.context.object
        ob.name = name
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ob.data.materials.append(material)
        return ob
    def box(name, loc, dims, material, bevel=.035):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        ob = bpy.context.object
        ob.dimensions = dims
        finish(name, material)
        if bevel:
            mod = ob.modifiers.new("Edge_bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 2
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return ob
    def loft(name, rings, material):
        # rings: y, half-width, lower z, upper z
        vertices = [(x,y,z) for y,w,lo,hi in rings
                    for x,z in [(-w,lo),(w,lo),(w,hi),(-w,hi)]]
        faces = [(0,1,2,3)]
        for i in range(len(rings)-1):
            for j in range(4):
                k = (j+1)%4
                faces.append((4*i+j,4*(i+1)+j,4*(i+1)+k,4*i+k))
        n = len(vertices)
        faces.append((n-1,n-2,n-3,n-4))
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(material)
        uv = mesh.uv_layers.new(name="UVMap")
        for poly in mesh.polygons:
            for idx in poly.loop_indices:
                x,y,z = mesh.vertices[mesh.loops[idx].vertex_index].co
                uv.data[idx].uv = ((x+1)/2, (y+2.5)/5) if abs(poly.normal.z) > .5 else ((y+2.5)/5,z/1.5)
        return ob
    loft("Chassis", [(-1.75,.28,.19,.66),(-1.2,.42,.18,.83),
         (-.2,.39,.17,.69),(.55,.27,.18,.55),(1.85,.10,.22,.37)], paint)
    box("Floor", (0,-.35,.16), (1.32,2.7,.10), carbon)
    for side in (-1,1):
        tag = "L" if side < 0 else "R"
        box("Sidepod_"+tag,(side*.49,-.45,.43),(.40,1.30,.43),paint)
        box("Sidepod_inlet_"+tag,(side*.49,.22,.48),(.27,.07,.20),carbon)
        box("Front_endplate_"+tag,(side*.84,2.0,.27),(.09,.43,.27),carbon)
        box("Rear_endplate_"+tag,(side*.64,-1.83,.86),(.09,.48,.52),carbon)
        for axle,y in (("F",1.25),("R",-1.3)):
            x = side*.79
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=.31, depth=.29,
                location=(x,y,.31), rotation=(0,math.pi/2,0))
            finish("Wheel_"+tag+"_"+axle,rubber)
            bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.19,depth=.035,
                location=(x+side*.15,y,.31),rotation=(0,math.pi/2,0))
            finish("Hub_"+tag+"_"+axle,metal)
            arm = box("Suspension_"+tag+"_"+axle,(side*.47,y,.31),(.62,.065,.07),metal,.01)
    box("FrontWing",(0,2.0,.20),(1.75,.40,.10),paint)
    box("RearWing",(0,-1.83,1.06),(1.33,.43,.10),paint)
    box("RearWing_support",(0,-1.83,.68),(.16,.18,.68),carbon)
    box("Cockpit",(0,.15,.67),(.34,.59,.14),carbon)
    box("Airbox",(0,-.62,.86),(.34,.35,.40),paint)
    box("Livery_stripe",(0,1.05,.49),(.10,.75,.025),accent,.005)
    # Scale evaluated geometry to requested envelope. Keep local wheel origins.
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    low = Vector(tuple(min(v[i] for v in pts) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in pts) for i in range(3)))
    d = r["dimensions_m"]
    scale = Vector((d["width"],d["length"],d["height"]))
    scale = Vector(tuple(scale[i]/(high[i]-low[i]) for i in range(3)))
    center = Vector(((low.x+high.x)/2,(low.y+high.y)/2,low.z))
    for ob in meshes:
        # Bake world anisotropic scaling into local geometry, preserving origin.
        rot = ob.rotation_euler.to_matrix()
        inv = rot.inverted()
        for v in ob.data.vertices:
            w = rot @ v.co
            v.co = inv @ Vector(tuple(w[i]*scale[i] for i in range(3)))
        pos = ob.location-center
        ob.location = Vector(tuple(pos[i]*scale[i] for i in range(3)))
        ob.data.update()
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(a.output),export_format="GLB",
                              export_yup=True,export_normals=True,export_texcoords=True)
    print("APEX_ASSET_EXPORTED", len(meshes), bpy.app.version_string)

if __name__ == "__main__":
    main()
