# v0.2.3 review

The previous exact-code run 46071164548 passed 55 tests. The subsequent documentation-only run 46071339915 failed twice, with no accessible job logs (HTTP 404 BlobNotFound); root cause cannot be attributed to a particular code line. Preserve that failure. The 24-row ledger was independently checked for its existing structural constraints, with six scoped PASS IDs and no invalid rows.

This revision tightens LOD acceptance: require complete staging reports, positive finite three-axis envelope, exact integer level/count fields, actual GLB/request receipt hashes, and compare named nodes, local transforms, hierarchy, material definitions and per-node material sets independent of material order. This is not proof of identical per-face material assignments or general collision freedom. No geometry generator is changed. Unit tests cover malformed receipts, material drift, duplicate component names, transform drift and hierarchy drift. Native follow-up checks must be recorded separately. No game integration or asset promotion.

## Review follow-up
Native schema 2/3 and curved endurance lower LODs completed. Four numeric repeat comparisons PASS (one binary identical). 15 new builds, 55 switch steps and 12 exact targeted unit tests PASS. Current remote CI remains FAIL with inaccessible logs and no recorded steps; no complete current suite or CI success claim. See https://github.com/Jugadru/apex-asset-factory/blob/feature/v0.2.3-advanced-body/evidence/v0.2.3-review/summary.json. No new blocker closed; no promotion.
