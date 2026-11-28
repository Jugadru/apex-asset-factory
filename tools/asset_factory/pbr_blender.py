"""Native Blender import check for actual embedded PBR textures."""
import sys
import math
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
    assert len(images)==(3 if "--normal-maps" in options else 2) and all(tuple(im.size)==(int(size),int(size)) for im in images),m.name
    if "--normal-maps" in options:
        assert bs.inputs["Normal"].is_linked,m.name
        normal=bs.inputs["Normal"].links[0].from_node
        assert normal.type=="NORMAL_MAP" and normal.space=="TANGENT" and normal.inputs["Color"].is_linked,m.name
        image=normal.inputs["Color"].links[0].from_node.image
        assert image.colorspace_settings.name=="Non-Color",m.name
if "--uv-clean" in options:
    total=0
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH":continue
        mesh=ob.data;mesh.calc_loop_triangles();uv=mesh.uv_layers[0].data
        for tri in mesh.loop_triangles:
            a,b,c=(uv[i].uv for i in tri.loops)
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,ob.name
            total+=1
    assert total>0
    print("APEX_UV_BLENDER PASS",total)
if "--normal-maps" in options:
    count=0
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH":continue
        mesh=ob.data;mesh.calc_tangents(uvmap=mesh.uv_layers[0].name)
        for loop in mesh.loops:
            t=loop.tangent;n=mesh.corner_normals[loop.index].vector
            assert all(math.isfinite(v) for v in t) and abs(t.length-1)<.005 and abs(t.dot(n))<.005 and abs(abs(loop.bitangent_sign)-1)<.005,ob.name
            count+=1
        mesh.free_tangents()
    assert count>0
    print("APEX_TANGENT_BLENDER PASS",count)
if "--uv-atlas" in options:
    total=0
    for ob in bpy.context.scene.objects:
        if ob.type!="MESH":continue
        mesh=ob.data;mesh.calc_loop_triangles()
        assert len(mesh.uv_layers)==2,ob.name
        uv=mesh.uv_layers[1].data
        for tri in mesh.loop_triangles:
            a,b,c=(uv[i].uv for i in tri.loops)
            assert all(math.isfinite(x) and 0<=x<=1 for q in (a,b,c) for x in q),ob.name
            assert abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))>1e-12,ob.name
            total+=1
    assert total>0
    print("APEX_UV2_BLENDER PASS",total)
print("APEX_PBR_BLENDER PASS",len(materials))
