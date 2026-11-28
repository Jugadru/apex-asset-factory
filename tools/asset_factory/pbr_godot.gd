extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var args := OS.get_cmdline_user_args()
    var expected := int(args[0])
    var resolution := int(args[1])
    var packed := load("res://asset.glb") as PackedScene
    if packed == null:
        quit(2)
        return
    var car := packed.instantiate() as Node3D
    root.add_child(car)
    var materials := {}
    var uv_total := 0
    var tangent_total := 0
    var uv2_total := 0
    for item in car.find_children("*", "MeshInstance3D", true, false):
        var mesh := item as MeshInstance3D
        for i in range(mesh.mesh.get_surface_count()):
            if "--uv-clean" in args:
                var arrays := mesh.mesh.surface_get_arrays(i)
                var uv: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
                var ids: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
                if ids.is_empty() or ids.size() % 3 != 0:
                    quit(7)
                    return
                for j in range(0, ids.size(), 3):
                    var a := uv[ids[j]]
                    var b := uv[ids[j+1]]
                    var c := uv[ids[j+2]]
                    if absf((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)) <= 1e-12:
                        print("collapsed imported UV ",mesh.name)
                        quit(8)
                        return
                    uv_total += 1
            if "--uv-atlas" in args:
                var arrays := mesh.mesh.surface_get_arrays(i)
                var uv2: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV2]
                var ids: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
                var positions: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
                if uv2.size() != positions.size() or ids.is_empty() or ids.size() % 3 != 0:
                    quit(14)
                    return
                for q in uv2:
                    if not q.is_finite() or q.x < 0.0 or q.y < 0.0 or q.x > 1.0 or q.y > 1.0:
                        quit(15)
                        return
                for j in range(0, ids.size(), 3):
                    var a := uv2[ids[j]]
                    var b := uv2[ids[j+1]]
                    var c := uv2[ids[j+2]]
                    if absf((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)) <= 1e-12:
                        quit(16)
                        return
                    uv2_total += 1
            if "--normal-maps" in args:
                var arrays := mesh.mesh.surface_get_arrays(i)
                var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
                var tangents: PackedFloat32Array = arrays[Mesh.ARRAY_TANGENT]
                if tangents.size() != normals.size() * 4 or normals.is_empty():
                    quit(10)
                    return
                for j in range(normals.size()):
                    var t := Vector3(tangents[4*j], tangents[4*j+1], tangents[4*j+2])
                    if not t.is_finite() or absf(t.length()-1.0) > .005 or absf(t.dot(normals[j])) > .005 or absf(absf(tangents[4*j+3])-1.0) > .005:
                        print("invalid tangent ", mesh.name)
                        quit(11)
                        return
                    tangent_total += 1
            var m := mesh.get_active_material(i) as BaseMaterial3D
            if m == null:
                quit(3)
                return
            for t in [m.albedo_texture, m.roughness_texture, m.metallic_texture]:
                if t == null or t.get_width() != resolution or t.get_height() != resolution:
                    print("bad texture ",m.resource_name)
                    quit(4)
                    return
            if m.roughness_texture_channel != BaseMaterial3D.TEXTURE_CHANNEL_GREEN or m.metallic_texture_channel != BaseMaterial3D.TEXTURE_CHANNEL_BLUE:
                quit(5)
                return
            if "--normal-maps" in args and (not m.normal_enabled or m.normal_texture == null or m.normal_texture.get_width() != resolution or m.normal_texture.get_height() != resolution):
                quit(12)
                return
            materials[m.resource_name] = true
    if materials.size() != expected:
        print(materials)
        quit(6)
        return
    if "--uv-clean" in args:
        if uv_total <= 0:
            quit(9)
            return
        print("APEX_UV_GODOT PASS ",uv_total)
    if "--normal-maps" in args:
        if tangent_total <= 0:
            quit(13)
            return
        print("APEX_TANGENT_GODOT PASS ",tangent_total)
    if "--uv-atlas" in args:
        if uv2_total <= 0:
            quit(17)
            return
        print("APEX_UV2_GODOT PASS ",uv2_total)
    print("APEX_PBR_GODOT PASS ",materials.size())
    quit(0)
