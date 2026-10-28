# Contact Center SonarCloud change log — 2026-10-28

All repository changes target the user's fork and next branch. Setup commits use [skip ci].
Application implementation and lockfiles are outside this change.

| File | Change and reason |
|---|---|
| sonar-project.properties | Target cisco-projects/ajitkumar0828-spec_widgets; restrict production/test roots, UTF-8, TS configs and LCOV. |
| .github/workflows/sonar-contact-center.yml | Manual-only, fork/next guard, full history, pinned Node/Yarn, locked install, builds, coverage, official scanner, processing verification and report artifacts. |
| scripts/sonar/coverage.cjs | Run original workspace unit commands, preserve exit status and isolate coverage output. |
| scripts/sonar/report.py | Validate scope and LCOV, verify server commit/main branch, paginate exports, escape CSV, record metrics/gate/warnings. |
| scripts/sonar/test_report.py | Validate multi-page export, duplicate detection, CSV quoting/formulas and same-named LCOV sources. |
| docs/sonar-contact-center.md | Explain scope, commands, failure semantics and report interpretation. |
| docs/sonar-change-log.md | Maintain this file/setting/execution audit. |
| scripts/sonar/build.cjs | Build the CC allowlist plus fixtures needed for tests; emit generated dependency declarations and record existing compilation failures. |

| Setting | Before | After / verification |
|---|---|---|
| Sonar automatic analysis | On | Off; changed in project Analysis method on 2026-10-28. |
| Sonar main branch | next | next; verified isMain=true via API. |
| Project organization | cisco-projects dashboard | cisco-projects retained. |
| Quality gate | Sonar way | Retained. |
| New-code definition | Existing project setting | Retained. |
| Analysis trigger | automatic, failed out of memory | Manual workflow only. |
| Runtime | No CI scan workflow | Node 24, Yarn 4.5.1. |
| GitHub SONAR_TOKEN | Missing | Credential values never recorded; execution evidence below tracks authorization. |

## Execution evidence

Base fork next: `c298215cc927c5c09cd19f7c540c8dbbb1264259`.
Configuration commit and workflow run URLs are added after publication.
Local isolated validation: Original TypeScript build errors recorded; coverage collection is diagnostic and preserves failed statuses.

Snapshots of settings and final downloaded run evidence are retained locally under reports/sonar.

## Published setup commits

The system Git account was denied push access (403). With explicit user approval, the same tested files were committed using the signed-in Chrome account. Every setup commit includes [skip ci].

- [12bc15fae9](https://github.com/ajitkumar0828-spec/widgets/commit/12bc15fae91f891961b3584d6bac91768a0086ad) — chore(sonar): add manual Contact Center widget scans [skip ci]
- [585c548072](https://github.com/ajitkumar0828-spec/widgets/commit/585c5480728f85ccc476580b9b018589f073075f) — chore(sonar): scope nine Contact Center widget packages [skip ci]
- [c430dd0ca9](https://github.com/ajitkumar0828-spec/widgets/commit/c430dd0ca9d99f5ffbfdc22ca188505283564bc6) — chore(sonar): add scripts/sonar/build.cjs [skip ci]
- [9cbf45dc14](https://github.com/ajitkumar0828-spec/widgets/commit/9cbf45dc14cb67d6ec04e2fdb370cd47d3babed0) — chore(sonar): add scripts/sonar/coverage.cjs [skip ci]
- [263e8ff992](https://github.com/ajitkumar0828-spec/widgets/commit/263e8ff992f3f778bb9c52d2d5044273ed8d93ab) — chore(sonar): add scripts/sonar/report.py [skip ci]
- [3d995e1a43](https://github.com/ajitkumar0828-spec/widgets/commit/3d995e1a43b9a4ba756c40186fd555680a14ef64) — chore(sonar): add scripts/sonar/test_report.py [skip ci]

The user confirmed saving SONAR_TOKEN securely in GitHub. Scanner authorization remains to be verified by the manual run.
Local Jest: 1,712 passed, seven skipped. Two original workspace commands failed TypeScript checks; three build commands failed. Diagnostic Jest coverage retains these failures.
