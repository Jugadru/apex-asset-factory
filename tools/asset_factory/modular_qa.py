"""Post-export wheel geometry and axle QA for the static modular profile."""
import math

TOL = 1e-6


def verify_wheels(doc, decoded, layout):
    def check(ok, name):
        if not ok:
            raise ValueError("modular wheel QA: " + name)

    parts = {p["name"]: p for p in layout}
    nodes = {n["name"]: n for n in doc["nodes"] if "name" in n}
    roots = {doc["nodes"][i].get("name") for i in doc["scenes"][doc["scene"]]["nodes"]}
    rows = []
    for tag in ("L_F", "L_R", "R_F", "R_R"):
        wheel, hub = (nodes.get(prefix + tag) for prefix in ("Wheel_", "Hub_"))
        check(wheel is not None and hub is not None, tag + " missing wheel/hub")
        check(wheel.get("translation") == hub.get("translation") and
              wheel.get("rotation") == hub.get("rotation"), tag + " hub misalignment")
        for node in (wheel, hub):
            name = node["name"]
            part = parts[name]
            check(name in roots, name + " nested pivot")
            check(node.get("scale", [1,1,1]) == [1,1,1], name + " unbaked scale")
            x,y,z = part["center"]
            center = node.get("translation", [])
            check(len(center)==3 and max(abs(a-b) for a,b in zip(center,[x,z,-y])) <= TOL,
                  name + " pivot translation")
            q = node.get("rotation", [])
            check(len(q)==4, name + " missing rotation")
            qx,qy,qz,qw = q
            axis = [2*(qx*qy-qz*qw), 1-2*(qx*qx+qz*qz), 2*(qy*qz+qx*qw)]
            check(abs(abs(axis[0])-1)<=TOL and abs(axis[1])<=TOL and abs(axis[2])<=TOL,
                  name + " transverse axle")
            mesh = doc["meshes"][node["mesh"]]
            pos = [pt for prim in mesh["primitives"]
                   for pt in decoded[prim["attributes"]["POSITION"]]]
            check(bool(pos), name + " empty positions")
            error = max(abs(math.hypot(pt[0],pt[2])-part["radius"]) for pt in pos)
            axial = [min(pt[1] for pt in pos),max(pt[1] for pt in pos)]
            check(error<=TOL, name + " radial distortion")
            check(abs(axial[0]+part["width"]/2)<=TOL and abs(axial[1]-part["width"]/2)<=TOL,
                  name + " axial width")
            rows.append({"component":name,"center":center,"axis":axis,
                         "max_radial_error_m":error,"axial_extent_m":axial})
    return {"status":"PASS","tolerance_m":TOL,"components":rows,
            "scope":"GLB local geometry and pivots, not Godot articulation"}
