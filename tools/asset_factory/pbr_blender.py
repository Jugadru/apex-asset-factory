"""Native Blender import check for actual embedded PBR textures."""
import sys
import bpy

path,count,size=sys.argv[sys.argv.index("--")+1:]
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
print("APEX_PBR_BLENDER PASS",len(materials))
