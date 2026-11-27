"""Validate ledger completeness and evidence discipline, not external truth."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
def validate(data):
    assert type(data) is dict and data.get("schema")==1
    rows=data["blockers"]
    assert type(rows) is list and len(rows)==24
    assert {x["id"] for x in rows}=={f"AF-B{i:03}" for i in range(1,25)}
    for row in rows:
        assert row["priority"] in ("P0","P1","P2")
        assert row["status"] in ("PASS","FAIL","NOT_RUN","INCONCLUSIVE","BLOCKED")
        assert all(type(row[k]) is str and row[k].strip() for k in ("criterion","target_version","progress"))
        assert type(row["evidence"]) is list
        assert all(type(x) is str and x.startswith("https://github.com/Jugadru/") for x in row["evidence"])
        if row["status"]=="PASS":
            assert row["evidence"] and re.fullmatch(r"[0-9a-f]{40}",row["resolved_commit"] or "")
        else:
            assert row["resolved_commit"] is None
    return {"status":"PASS","scope":"ledger structure only","total":len(rows),"closed":sum(x["status"]=="PASS" for x in rows)}
if __name__=="__main__":
    print(json.dumps(validate(json.loads((ROOT/"docs/blockers.json").read_text())),indent=2))
