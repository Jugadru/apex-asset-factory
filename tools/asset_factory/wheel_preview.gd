extends SceneTree

# Isolated native visual review of the actual right-front GLB assembly.
func _initialize() -> void:
    call_deferred("_run")

func _run() -> void:
    var packed := load("res://asset.glb") as PackedScene
    if packed == null:
        quit(2)
        return
    var car := packed.instantiate() as Node3D
    root.add_child(car)
    var target := Vector3.ZERO
    var count := 0
    var wheel_radius := 0.0
    for item in car.find_children("*", "MeshInstance3D", true, false):
        var mesh := item as MeshInstance3D
        mesh.visible = String(mesh.name).ends_with("_R_F")
        if mesh.visible:
            count += 1
            if mesh.name == "Wheel_R_F":
                target = mesh.global_position
                wheel_radius = mesh.get_aabb().size.x / 2.0
    if count != 7 or wheel_radius <= 0.0:
        quit(3)
        return
    var cam := Camera3D.new()
    root.add_child(cam)
    cam.position = target + Vector3(2.0, 0.65, -0.8)
    cam.look_at(target)
    cam.projection = Camera3D.PROJECTION_ORTHOGONAL
    cam.size = 2.8 * wheel_radius
    cam.current = true
    var light := DirectionalLight3D.new()
    root.add_child(light)
    light.rotation_degrees = Vector3(-35, 65, 0)
    light.light_energy = 2.0
    var env := WorldEnvironment.new()
    env.environment = Environment.new()
    env.environment.background_mode = Environment.BG_COLOR
    env.environment.background_color = Color(.12,.15,.19)
    env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.environment.ambient_light_color = Color(.85,.87,1)
    env.environment.ambient_light_energy = .85
    root.add_child(env)
    for i in range(4):
        await process_frame
    await RenderingServer.frame_post_draw
    var err := root.get_texture().get_image().save_png("res://wheel-preview.png")
    if err != OK:
        quit(4)
        return
    print("APEX_WHEEL_PREVIEW ", JSON.stringify({"parts":count,"status":"PASS","scope":"isolated imported right-front assembly"}))
    quit(0)
