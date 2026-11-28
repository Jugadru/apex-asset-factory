extends "res://staging.gd"

# Isolate the explicit source LOD in A/B capture, without changing import settings.
func _run() -> void:
    root.mesh_lod_threshold = 0.0
    await super._run()
