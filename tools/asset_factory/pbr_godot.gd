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
    print("APEX_PBR_GODOT PASS ",materials.size())
    quit(0)
