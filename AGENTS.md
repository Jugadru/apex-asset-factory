# AGENTS — Asset Factory

- Work here for graphical tooling; game repo is sole authority for sporting state, saves, physics and runtime integration. Never copy or modify runtime code here.
- Before changes inspect exact SHA, BLOCKERS, roadmap, existing code and source provenance. One main capability per version. Never invent PASS; use PASS/FAIL/NOT_RUN/INCONCLUSIVE/BLOCKED.
- JSON approved is permission to generate original demo only, not authentication or promotion. No arbitrary commands, third-party downloads, secrets or untrusted code; use trusted tools and disposable environments. No personal runner without owner consent and idle confirmation. No permanent services.
- New workspace outside checkout, no overwriting approved assets. No publication without documented rights. No voice cloning. Human review and approval tied to exact asset hash before promotion. No automatic merge.
- Unit tests and relevant native Blender/Godot fixtures; capture real evidence, distinguish software rendering vs physical GPU. Game integration requires its existing FAST on exact SHA; FULL only explicit owner request. Do not create competing game CI.
- Pinned shared helpers are upstream snapshots: reconcile with Foundation/Graphics Lab owners before changing shared semantics. No private Lab code copied.
- Preserve all IDs in BLOCKERS; close only with linked evidence. Keep history of failures. Revert PR/commit for rollback. Migration is not homologation.

- Read docs/HANDOFF.md and docs/RUNTIMES.md before native execution; upstream snapshots are read-only references, not a new source of truth. The source manifest covers original blobs and must not be rewritten to disguise an intentional change.
