# Contact Center SonarCloud change log

Scans: 28 October 2026. Audit finalized: 29 October 2026 (Asia/Kolkata).

All repository writes target `ajitkumar0828-spec/widgets:next`. Changes were based on fork commit `c298215cc927c5c09cd19f7c540c8dbbb1264259` in an isolated checkout. Original working copies and archive artifacts were preserved. Application implementation and lockfiles were not changed.

## Files and reasons

| File | Change and reason |
|---|---|
| `.github/workflows/sonar-contact-center.yml` | Add manual-only fork/next guarded Widgets scan with locked dependencies, CC dependency builds, original unit commands, distinct LCOV, official scanner and verified report/artifact. Preserve failed build/test statuses. |
| `docs/sonar-change-log.md` | Record every changed file, setting, publication commit and workflow outcome, including invalid/failed attempts. |
| `docs/sonar-contact-center.md` | Document execution, scope, coverage methods, credentials, reports and failure interpretation. |
| `scripts/sonar/build.cjs` | Build the explicit CC dependencies; build fixtures solely for unit tests; emit ignored declarations at dependency type paths and retain existing build failures. |
| `scripts/sonar/coverage.cjs` | Run original workspace unit commands, retain their exits, isolate workspace LCOV and include untested production files; collect diagnostic Jest coverage after Widgets type-check failures without marking them passed. |
| `scripts/sonar/report.py` | Validate source/test allowlist and normalized LCOV; verify exact server task, commit and main branch; paginate issues/files, escape CSV, check coverage imports and export metrics/gate/warnings. |
| `scripts/sonar/test_report.py` | Five regression tests for pagination/count/duplicates, CSV escaping/formulas, LCOV ambiguity/traversal/incomplete records, and test filters hiding production source. |
| `sonar-project.properties` | Correct organization/project; explicit approved source/test roots, UTF-8, package TypeScript configs, exclusions and LCOV paths. Test patterns are prefixed with test roots to avoid excluding production files. |

## Service settings

| Setting | Before | After / evidence |
|---|---|---|
| Sonar project / organization | Existing cisco-projects dashboard; SDK CI previously published to a different project/organization | Correct cisco-projects project key in root properties; exact task and revision verified. |
| Automatic analysis | Enabled; Widgets failed out of memory | Disabled for both selected projects on 28 October; setting screenshots retained locally. |
| Main branch | next | next retained and verified isMain=true through the server API. |
| Quality gate | Sonar way | Retained; exact returned conditions saved in quality-gate.json. |
| New-code definition | Previous version | Retained; period/date saved with gate evidence. |
| Workflow trigger | SDK push/PR workflow and Sonar automatic analysis; no correct Widgets CI scan | workflow_dispatch only, exact fork and refs/heads/next guard. |
| Runtime | Inconsistent scan environment | Node 24 / checked-in Yarn 4.5.1. |
| Coverage thresholds | Existing workspace thresholds | Preserved; untested production files added to collection. |
| GitHub SONAR_TOKEN | Missing. | User saved it securely; final scan authorized successfully. No credential values were read or recorded. |
| Sonar project name | Repository dashboard name | Webex Contact Center Widgets via scanner configuration. |

## Scan and report outcome

Scanned commit: `0cb4bdf51543f432a7f5eb773d1072432722738a`. [Workflow](https://github.com/ajitkumar0828-spec/widgets/actions/runs/40674158063); [dashboard](https://sonarcloud.io/summary/overall?id=ajitkumar0828-spec_widgets&branch=next); [artifact](https://github.com/ajitkumar0828-spec/widgets/actions/runs/40674158063/artifacts/12810870155).

Analysis `938d8ec5-7ca5-497c-b0fc-501d513f458f` at `2026-10-28T10:48:39+0000`. Server processing SUCCESS; 139 production files and 90 separately classified test files; no unexpected or missing files and no production NCLOC assigned to tests. All tested-workspace LCOV imports verified.

Coverage 87.7%; line coverage 90.8%; branch coverage 83.1%; duplication 0.6%; 45 distinct open issues; 0 Sonar analysis warnings; quality gate OK. Workflow failure.

The retained quality gate evaluates four new-code rating/hotspot conditions. The returned gate does not evaluate overall coverage or duplication, and a passing gate does not mean all existing issues are resolved. Legacy reliability/security/maintainability ratings and overlapping software-quality issue counts are retained in the report.

The workflow deliberately remains failed: builds failed for cc-components, cc-ai-assistant and cc-widgets; the original cc-components and cc-ai-assistant unit commands failed their TypeScript prerequisite. Separate same-configuration Jest runs produced diagnostic coverage with the original failed status preserved. Local Jest totals: 1,712 passed, seven skipped, zero failed assertions. No test thresholds were lowered.

cc-widgets has no tests. Both source files remain analyzed, and all 14 executable lines are uncovered (0% line coverage). test-fixtures was built only as a test dependency and is absent from production analysis.

[Initial Widgets attempt](https://github.com/ajitkumar0828-spec/widgets/actions/runs/40670111027) analyzed only 19 CSS/SCSS files because the initial extension-only test inclusions also excluded TypeScript production. Scope validation rejected that result. Test inclusion patterns were corrected to test-directory prefixes, the exporter was corrected to classify FIL and UTS separately, and a regression guard was added. The final run above verified all 139 production files. The first attempt is invalid and is not a baseline.

## Publication and validation audit

Shell Git used a different account and was denied push access. With the user’s explicit approval, the signed-in Chrome account published these exact files to the two forks. Every setup/correction/documentation commit uses [skip ci]; manual scans were dispatched separately. No inherited release workflow was intentionally started.

Five report-contract regression tests pass. Scope, LCOV path normalization, pagination/count/duplicate checks, CSV round-trip row counts, exact server commit and stable analysis checks passed. Production/test files match the approved manifest.

GitHub emitted an action-runtime warning (checkout/upload-artifact Node 20 forced to Node 24) and an ubuntu-latest migration notice. These are distinct from the zero Sonar analysis warnings. SDK Jest also reported a worker teardown warning during local validation.

Reports and normalized coverage evidence are available in the linked CI artifact. The browser client blocked the artifact ZIP host. Markdown, CSV and JSON reports were instead downloaded locally from public SonarCloud APIs, with explicit download-provenance.json. Local task verification used the public ce/component endpoint; CI used its exact authenticated ce/task. The actual CI unit-command status JSON was also saved from the rendered GitHub summary.

Local bundle: reports/sonar/2026-10-28/ in the user’s Widgets checkout. Latest report, original SDK baseline, package coverage, scope/import evidence, run links, artifact metadata, publication commits, patches and setting screenshots are retained there. Personal tokens were created with a 30-day expiry; rotate GitHub secrets before expiry.

The final audit-document commits occur after the scans and do not change analyzed production source. Their own hashes are recorded in the local publication audit and repository history; the exact scanned SHA remains the one above.

## Published configuration and correction commits

- [12bc15fae9](https://github.com/ajitkumar0828-spec/widgets/commit/12bc15fae91f891961b3584d6bac91768a0086ad) — chore(sonar): add manual Contact Center widget scans [skip ci]
- [585c548072](https://github.com/ajitkumar0828-spec/widgets/commit/585c5480728f85ccc476580b9b018589f073075f) — chore(sonar): scope nine Contact Center widget packages [skip ci]
- [c430dd0ca9](https://github.com/ajitkumar0828-spec/widgets/commit/c430dd0ca9d99f5ffbfdc22ca188505283564bc6) — chore(sonar): add scripts/sonar/build.cjs [skip ci]
- [9cbf45dc14](https://github.com/ajitkumar0828-spec/widgets/commit/9cbf45dc14cb67d6ec04e2fdb370cd47d3babed0) — chore(sonar): add scripts/sonar/coverage.cjs [skip ci]
- [263e8ff992](https://github.com/ajitkumar0828-spec/widgets/commit/263e8ff992f3f778bb9c52d2d5044273ed8d93ab) — chore(sonar): add scripts/sonar/report.py [skip ci]
- [3d995e1a43](https://github.com/ajitkumar0828-spec/widgets/commit/3d995e1a43b9a4ba756c40186fd555680a14ef64) — chore(sonar): add scripts/sonar/test_report.py [skip ci]
- [5ade6debe0](https://github.com/ajitkumar0828-spec/widgets/commit/5ade6debe0f948306563d66429f62d95c067231b) — chore(sonar): add docs/sonar-contact-center.md [skip ci]
- [c8e99c2e20](https://github.com/ajitkumar0828-spec/widgets/commit/c8e99c2e20e532065865b9563cca799e2039d5b9) — chore(sonar): add docs/sonar-change-log.md [skip ci]
- [e25427a05e](https://github.com/ajitkumar0828-spec/widgets/commit/e25427a05ecce84f7b8a409e16e3862b5f576f09) — fix(sonar): constrain test inclusions to test directories [skip ci]
- [fcea5623cf](https://github.com/ajitkumar0828-spec/widgets/commit/fcea5623cfad39479c3fb8d718571976b71b18ce) — fix(sonar): verify source and unit-test components separately [skip ci]
- [0cb4bdf515](https://github.com/ajitkumar0828-spec/widgets/commit/0cb4bdf51543f432a7f5eb773d1072432722738a) — test(sonar): prevent test filters from hiding production code [skip ci]
