# APEX — Native graphics evidence and review

Native GPU and human visual inspection are separate from hosted Xvfb software capture tests. The existing native run is historical, not a new test of the current main commit.

## Recorded native baseline (REV1)

Evidence: [native execution report, Hub #141](https://github.com/Jugadru/APEX-Simulation/issues/141#issuecomment-7196817474) and [owner visual confirmation / integration record](https://github.com/Jugadru/APEX-Simulation/issues/141#issuecomment-7196859152).

- Exact tested candidate: `947c400bd3174558768a228baed80d183ca7e588`; merged via #142 at `abc8f8618c856c951decf15eadae09cdc036e13a`.
- Godot 4.7.2.stable.official.ed1daf0bf, GTX 1650, Forward+, 1280×720 window / 1920×1080 subviewport; Monza, dry, seed 660.
- Execution: PASS, eight cases, no reported errors. Human review: owner reported no observed visual problems for those cases. No independent visual reviewer or image-by-image acceptance record.
- One approximately eight-second observation per case; CPU/GPU causation not established. Default profile retained.

| Requested | Default FPS | Effective acceleration | Frame p95 (ms) |
|---|---:|---:|---:|
| 1x forced 3D | 83.84 | 1.00 | 17.219 |
| 10x Auto 2D | 132.28 | 9.82 | 14.625 |
| 16x Auto 2D | 38.48 | 13.99 | 37.383 |
| 32x Auto 2D | 38.52 | 13.81 | 37.532 |

Known limitation: throughput near 14x in this workload, not a fulfilled 32x target; isolated 195.618 ms frame at 1x. Historical ABC remains INCONCLUSIVE. These figures are not current version measurements.

## Review procedure — only for relevant visual or native runtime changes

1. Identify exact trusted revision, affected interface/3D system and intended behavior. Use FAST and targeted hosted /lab graphics first when relevant. Never equate hosted screenshots to native approval.
2. Obtain explicit owner permission and confirmation the personal machine is idle/available before any native runner dispatch. Do not schedule personal-runner jobs from PR events; no unattended persistent service. If the owner prefers, use the normal game on the authorized machine instead.
3. Run a short focused check of the affected view, at the normal renderer/settings, with disposable test save/user data when using automation. Check HUD visibility, readability, layout, clipping, motion, input and transitions relevant to the change. Do not rerun the historical 8-case benchmark merely to check visuals. Record actual window/viewport and rendering method.
4. Preserve original screenshot/log references in an authorized location; never expose private paths, private assets or credentials. An image capture by itself is not human visual approval.
5. Record execution and human observation independently using the template below. If there is no new native execution or no reviewer, keep the respective status NOT_RUN. If a visual problem is observed, mark FAIL, describe reproduction and link a targeted regression. If evidence is insufficient, mark INCONCLUSIVE/BLOCKED as appropriate.

## Copyable review record

```text
Candidate full SHA:
Game version / engine version:
GPU / driver / OS:
Rendering method / graphics profile:
Window / viewport:
Track / weather / seed / affected view:
Owner authorization / idle confirmation (if automated):
Native execution: NOT_RUN | PASS | FAIL | BLOCKED | INCONCLUSIVE
Human visual review: NOT_RUN | PASS | FAIL | INCONCLUSIVE
Reviewer / date:
Observed issues and limitations:
Evidence links:
```

Current Lab closing revision: no new native GPU test or human review was performed by the Lab's hosted runs. Keep both NOT_RUN for that revision until evidence exists. Future ordinary nonvisual game changes do not require new native checks. This record complements AGENTS.md, the technical knowledge index and the Graphics Lab; it does not create a new universal merge gate.
