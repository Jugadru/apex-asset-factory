"""Foundation reviewed metadata adapter. Never evaluates registry methods."""
import json
import re

LIMIT = 2 * 1024 * 1024
VERSIONS = {"0.1.0", "0.2.1"}
REQUIRED = [
    "tools/apex_foundation.py",
    "docs/foundation/registry.json", "docs/foundation/schemas.json",
    "docs/foundation/upstream-entrypoints.json",
    "docs/references/references.json", "docs/references/possibilities.json",
    "docs/references/domains.json",
]
ID = re.compile(r"[a-z][a-z0-9_.-]{0,79}\Z")
# Explicit mapping only. Other declared methods are descriptive.
ADAPTERS = {"foundation.validate": ("1.0.0", "python3 tools/apex_foundation_registry.py validate", ["read.repository"])}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def pairs(rows):
    result = {}
    for k, v in rows:
        require(k not in result, "Duplicate Foundation key")
        result[k] = v
    return result


def invalid_constant(value):
    raise ValueError("Nonfinite Foundation constant")


def read(path):
    require(path.is_file() and not path.is_symlink(), "Missing Foundation result")
    with path.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT, "Foundation response too large")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def count(value, minimum=1):
    return type(value) is int and minimum <= value <= 100000


def validate(data):
    require(isinstance(data, dict) and data.get("status") == "PASS"
            and data.get("scope") == "structural metadata only", "Foundation validation scope mismatch")
    for k in ("modules", "capabilities", "active_contracts", "compatibility_pairs"):
        require(count(data.get(k)), "Invalid Foundation count")
    cat = data.get("catalog")
    require(isinstance(cat, dict) and cat.get("status") == "PASS"
            and cat.get("scope") == "catalog structure only"
            and count(cat.get("references"), 198) and count(cat.get("possibilities"), 120)
            and type(cat.get("domains")) is int and cat["domains"] == 8,
            "Foundation catalog acceptance failed")
    return {k: data[k] for k in ("modules", "capabilities", "active_contracts", "compatibility_pairs", "catalog")}


def discovery(data, validated, sha):
    require(isinstance(data, dict) and set(data) == {"foundation_version", "modules", "capabilities",
            "compatibility", "contracts"} and isinstance(data["foundation_version"], str) and data["foundation_version"] in VERSIONS,
            "Unsupported Foundation registry version or shape")
    modules, caps = data["modules"], data["capabilities"]
    require(isinstance(modules, list) and isinstance(caps, list)
            and len(modules) == validated["modules"] and len(caps) == validated["capabilities"],
            "Registry count mismatch")
    require(isinstance(data["contracts"], list) and isinstance(data["compatibility"], list)
            and len(data["compatibility"]) == validated["compatibility_pairs"]
            and sum(isinstance(x, dict) and x.get("status") == "active" for x in data["contracts"])
                == validated["active_contracts"], "Registry contract count mismatch")
    module_ids = set()
    for row in modules:
        require(isinstance(row, dict) and isinstance(row.get("id"), str)
                and ID.fullmatch(row["id"]) and row["id"] not in module_ids, "Invalid module ID")
        module_ids.add(row["id"])
    rows, seen = [], set()
    for cap in caps:
        require(isinstance(cap, dict) and set(cap) == {"id", "module", "version", "inputs",
                    "outputs", "method", "permissions", "restrictions"}, "Invalid capability shape")
        require(isinstance(cap["id"], str) and ID.fullmatch(cap["id"]) and cap["id"] not in seen,
                "Invalid or duplicate capability")
        require(isinstance(cap["module"], str) and cap["module"] in module_ids
                and isinstance(cap["version"], str) and 0 < len(cap["version"]) <= 80
                and isinstance(cap["method"], str) and 0 < len(cap["method"]) <= 2000,
                "Invalid capability metadata")
        for key in ("inputs", "outputs", "permissions", "restrictions"):
            require(isinstance(cap[key], list) and all(isinstance(x, str) for x in cap[key]),
                    "Invalid capability metadata list")
        seen.add(cap["id"])
        mapped = ADAPTERS.get(cap["id"]) == (cap["version"], cap["method"], cap["permissions"])
        rows.append({"id": cap["id"], "module": cap["module"], "version": cap["version"],
                     "permissions": cap["permissions"], "restrictions": cap["restrictions"],
                     "hub_adapter": "foundation.validate" if mapped else None,
                     "state": "ADAPTER_MATCH" if mapped else "DECLARED_ONLY",
                     "execution_authorized": False})
    return {"schema": 1, "scope": "metadata discovery only", "foundation_version": data["foundation_version"],
            "foundation_sha": sha, "execution_authorized": False,
            "capabilities": sorted(rows, key=lambda x: x["id"])}
