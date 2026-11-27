extends SceneTree

func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://asset.glb") as PackedScene
    if packed == null:
        quit(2)
        return
    var car := packed.instantiate() as Node3D
    root.add_child(car)
    var meshes := car.find_children("*", "MeshInstance3D", true, false)
    if meshes.is_empty():
        quit(3)
        return
    var bounds: AABB
    var first := true
    for item in meshes:
        var mesh := item as MeshInstance3D
        if mesh.mesh == null:
            quit(4)
            return
        var b := mesh.global_transform * mesh.get_aabb()
        bounds = b if first else bounds.merge(b)
        first = false
    print("APEX_IMPORT ", JSON.stringify({"meshes":meshes.size(),"size":[bounds.size.x,bounds.size.y,bounds.size.z]}))
    if "--capture" in OS.get_cmdline_user_args():
        var cam := Camera3D.new()
        root.add_child(cam)
        cam.position = bounds.get_center() + Vector3(6, 4.5, -7)
        cam.look_at(bounds.get_center())
        cam.projection = Camera3D.PROJECTION_ORTHOGONAL
        cam.size = bounds.size.z * .72
        cam.current = true
        var light := DirectionalLight3D.new()
        root.add_child(light)
        light.rotation_degrees = Vector3(-45, -35, 0)
        light.light_energy = 1.5
        var env := WorldEnvironment.new()
        env.environment = Environment.new()
        env.environment.background_mode = Environment.BG_COLOR
        env.environment.background_color = Color(.12,.15,.19)
        env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
        env.environment.ambient_light_color = Color(.8,.84,1)
        env.environment.ambient_light_energy = .65
        root.add_child(env)
        for i in range(4):
            await process_frame
        await RenderingServer.frame_post_draw
        var err := root.get_texture().get_image().save_png("res://capture.png")
        if err != OK:
            quit(5)
            return
    quit(0)
