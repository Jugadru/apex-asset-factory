# APEX Lab — technical knowledge index (1.2a)

Purpose: a durable entry point for agent-guided game development, not a second source of sporting rules. Read current AGENTS.md, the exact relevant code and regression fixture before changing a feature. See docs/APEX_AUTONOMOUS_ENGINEERING_LAB.md for engineering roadmap and policy. Record actual revisions and results; never turn historical INCONCLUSIVE into PASS.

## System map

| System | Source entry point | Existing evidence / relevant fixture |
|---|---|---|
| Sporting integration | scripts/race_engine.gd | tests/apex_lab_track_smoke.gd; tests/apex_lab_sporting_scenario_12_test.gd (305 checks PASS in #150) |
| Traffic and space | scripts/core/race_space_0655.gd | tests/overtaking_066912_test.gd; tests/traffic_mega_09201_test.gd |
| Driver personality | scripts/core/race_driver_soul_06694.gd | tests/driver_soul_06694_test.gd |
| Aerodynamic wake | scripts/core/race_aero_wake_091711.gd | tests/aero_wake_091711_test.gd |
| Weather setup | scripts/core/race_wet_setup_0918.gd | tests/wet_weather_setups_0918_test.gd |
| Pit strategy | scripts/core/race_pitwall_strategy_0649.gd | tests/pitwall_0649_strategy_test.gd; tests/pit_incidents_double_stack_test.gd |
| Replay and sporting state | scripts/core/race_replay_0660.gd; scripts/core/race_state_codec_0660.gd | tests/replay_0660_test.gd |
| Test routing | tools/apex_ci_tiers.py; .github/apex-quality-suites.json | tests are selected by changed paths; inspect exact plan |
| Performance | tools/apex_lab_perf_report.py; tools/apex_lab_perf_history.py | fixed synthetic LAB headless profile, not cross-host regression or GPU evidence |
| Engineering commands | tools/apex_lab_command.py | issue #141 receipts and exact revision logs; private analyzer uses its own hub |

## Decision record

- REV1 (PR #142) is the chosen game baseline; historical ABC verdict remains INCONCLUSIVE. No routine benchmark reruns.
- PR #145: command bridge validated end-to-end for audit.
- PR #146: bounded failure classification; evidence is not established root cause.
- PR #147: literal dependency graph and registered fixture inventory; metrics not mandatory refactoring.
- PR #148: on-demand failure/diff correlation; no automatic repair or all-CI failure listener.
- Private Lab PR #22: analyzer 0.2.1 integrated after multiline lexer correction; actual command 45864200406 PASS, 161 scripts, zero scan errors. Private source remains private.
- PR #149: observation collection passed and integrated; targeted artifact-only multi-run verification is available, result pending.
- PR #150: two real-track scenarios, 305 checks PASS; #151: five hosted captures and three graphics fixtures PASS, visual review NOT_RUN.
- PR #152: actual Linux export, adjacent PCK startup and archive verification PASS; no publication.

## New scenario contract (1.2a)

The new fixture exercises 90 fixed replay ticks on Monza dry and Silverstone heavy rain (seed 991321, 24 cars). It validates legal manual V3 pit booking, pace command acceptance, finite state, unique classification, and exact replay hash/seek parity. This does not prove overtaking, tyre evolution, successful pit completion, full-race behavior or visual fidelity. Existing domain fixtures remain necessary for these specific changes. Register the new test only against its own path initially, and allow the explicit simulation command; do not impose a full matrix on routine versions. Future scenarios should cover actual affected mechanics with deterministic assertions.

## Durable update procedure

For each meaningful feature, record its PR and exact validated SHA, modified system, intentional behavior change, regression fixture, actual result and unresolved limitation in the changelog or relevant design record. Link rather than duplicate code. Use existing roadmap and technical notes, and update this index only when ownership or test entry points change. Never claim a test passed from its filename or from an unexecuted plan.

Graphics: hosted software-rendered UI checks on demand. See [native graphics review](APEX_NATIVE_GRAPHICS_REVIEW.md) for historical REV1 evidence, current NOT_RUN status and focused owner-authorized review procedure. Release Automation: verified test exports, checksums and separate official publication decision. Performance history: optional artifact-only verification, no new Godot benchmark.
