"""Explicit precision preset for UV atlas staging and controlled A/B captures."""
from pathlib import Path

PRESET = '[importer_defaults]\nscene={\n"meshes/force_disable_compression": true\n}\n'


def precise_project(text):
    """Do not silently overwrite an existing importer policy."""
    if PRESET in text and text.count('[importer_defaults]') == 1:
        return text
    if '[importer_defaults]' in text:
        raise ValueError("conflicting importer defaults")
    return text.rstrip() + "\n\n" + PRESET


def verify_precise_import(staging):
    path = Path(staging) / "asset.glb.import"
    if not path.is_file() or path.is_symlink():
        raise ValueError("missing regular import receipt")
    lines = path.read_text().splitlines()
    for key, expected in (("meshes/force_disable_compression", "true"), ("meshes/generate_lods", "true")):
        actual = [line.split("=", 1)[1] for line in lines if line.startswith(key + "=")]
        if actual != [expected]:
            raise ValueError("import policy mismatch: " + key)
    return {"mesh_compression_disabled": True, "generate_lods": True}
