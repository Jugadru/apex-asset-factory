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
    for item in car.find_children("*", "MeshInstance3D", true, false):
        var mesh := item as MeshInstance3D
        for i in range(mesh.mesh.get_surface_count()):
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
    print("APEX_PBR_GODOT PASS ",materials.size())
    quit(0)
