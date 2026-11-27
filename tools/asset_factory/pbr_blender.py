"""Native Blender import check for actual embedded PBR textures."""
import sys
import bpy

path,count,size,*options=sys.argv[sys.argv.index("--")+1:]
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=path)
materials={m for ob in bpy.context.scene.objects if ob.type=="MESH" for m in ob.data.materials}
assert len(materials)==int(count)
for m in materials:
    bs=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    assert all(bs.inputs[k].is_linked for k in ("Base Color","Metallic","Roughness")),m.name
    images={n.image for n in m.node_tree.nodes if n.type=="TEX_IMAGE" and n.image}
    assert len(images)==2 and all(tuple(im.size)==(int(size),int(size)) for im in images),m.name
if "--uv-clean" in options:
    total=0
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH":continue
        mesh=ob.data;mesh.calc_loop_triangles();uv=mesh.uv_layers.active.data
        for tri in mesh.loop_triangles:
            a,b,c=(uv[i].uv for i in tri.loops)
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,ob.name
            total+=1
    assert total>0
    print("APEX_UV_BLENDER PASS",total)
print("APEX_PBR_BLENDER PASS",len(materials))
