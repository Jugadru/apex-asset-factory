extends SceneTree

# Standalone staging fixture; not a game runtime integration.
var variants: Array[Node3D] = []
var level := 0
var camera: Camera3D

func _initialize() -> void:
    call_deferred("_run")

func _select(distance: float) -> int:
    var thresholds := [25.0, 70.0]
    while level < 2 and distance >= thresholds[level] + 3.0:
        level += 1
    while level > 0 and distance <= thresholds[level - 1] - 3.0:
        level -= 1
    for i in range(variants.size()):
        variants[i].visible = (i == level)
    return level

func _run() -> void:
    for i in range(3):
        var packed := load("res://lod%d.glb" % i) as PackedScene
        if packed == null:
            quit(2)
            return
        var car := packed.instantiate() as Node3D
        if car == null or car.find_children("*", "MeshInstance3D", true, false).is_empty():
            quit(3)
            return
        root.add_child(car)
        variants.append(car)
    camera = Camera3D.new()
    root.add_child(camera)
    var distances := [0.0,26.0,29.0,72.0,74.0,68.0,66.0,23.0,21.0,100.0,0.0]
    var expected := [0,0,1,1,2,2,1,1,0,2,0]
    var observed: Array[int] = []
    for i in range(distances.size()):
        camera.position = Vector3(0,0,distances[i])
        var selected := _select(camera.global_position.distance_to(Vector3.ZERO))
        observed.append(selected)
        var visible_count := 0
        for j in range(variants.size()):
            if variants[j].visible:
                visible_count += 1
                if j != selected:
                    quit(4)
                    return
        if selected != expected[i] or visible_count != 1:
            quit(5)
            return
    print("APEX_LOD ", JSON.stringify({"status":"PASS","distances_m":distances,"levels":observed,"visible_roots":1}))
    quit(0)
