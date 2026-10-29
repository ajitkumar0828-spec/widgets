# Contact Center SonarCloud analysis

The manual workflow analyzes the existing `ajitkumar0828-spec_widgets` project in `cisco-projects` on `next`.
Run `.github/workflows/sonar-contact-center.yml` using **Actions > Run workflow > next**.
The job checks the exact fork and ref; there are no push or pull-request triggers.
Use Node 24 and the checked-in Yarn 4.5.1. Install with `--immutable`.

## Scope and coverage

`sonar-project.properties` is the authoritative scanner configuration. Production roots are explicit;
unit-test roots are separate. Test inclusion patterns are prefixed with their test directories: Sonar also uses these patterns to exclude production files. Broad extension-only test patterns would hide production code. A regression check rejects this overlap. The report script also checks the roots against a fixed approved allowlist.
Only JS, JSX, TS, TSX, CSS and SCSS under those production roots are analyzed. Type declarations,
test/spec files, mocks, dependencies, generated bundles and archives are excluded.
Other SDK plugins, meetings, sample applications and test-fixtures are not production scope.

Coverage runs before the scanner, includes untested executable source, and preserves existing thresholds.
Each tested workspace writes a separate `coverage/sonar/<directory>/lcov.info`.
LCOV source paths are resolved against the repository and owning workspace, verified against the
production manifest, and rewritten to unique repository-relative paths.
The server export checks that tests have no production NCLOC and that every analyzed production file
belongs to the allowlist, then checks covered-line metrics for each imported LCOV report.

The nine packages are cc-ai-assistant, cc-components, cc-digital-channels, cc-widgets,
cc-station-login, cc-store, cc-task, cc-ui-logging and cc-user-state (all under @webex).
cc-widgets has no tests and no fabricated LCOV output; its executable production code stays uncovered.
test-fixtures is built solely as a unit-test dependency and is excluded from analysis.

The build runner emits store declarations and ui-logging declarations at its package.json type path,
using ignored generated output. It does not change application code or dependencies.
Existing build/type-check failures are captured in `build-status.json` and `test-status.json`.
If a package's original `tsc && jest` script stops before Jest, the runner additionally invokes that
workspace's same Jest configuration only to obtain coverage. The original command stays failed and
the workflow ends red. This is diagnostic coverage from a run with failed build/type checks; it does not establish release readiness.
No test threshold is reduced and no failed unit test is labeled passed.

## Reports and validation

`scripts/sonar/report.py` uses the SonarCloud Web API. CI authenticates with SONAR_TOKEN from the environment only; the CE-task endpoint requires authenticated access. It waits for the exact scanner CE task, verifies SUCCESS and the exact
SCM revision on the main branch, exports all issue/file pages, and detects truncation or duplicates.
CSV fields are quoted with the standard CSV writer and protected against spreadsheet formulas.
SCM authors/assignees and credentials are omitted.

Artifacts named `contact-center-sonar-<sha>` contain `reports/sonar/` and `coverage/sonar/`, retained
30 days. `latest/SUMMARY.md`, `issues.csv`, `issues.json`, metrics, branch/commit metadata,
file lists, server task/warnings and scope/LCOV validation evidence are included.
The workflow summary links the dashboard and run. Download the artifact to retain a local copy. If the browser client blocks the artifact host, public SonarCloud metrics, issues and file evidence can be downloaded separately; record this provenance and obtain the current task from the public ce/component endpoint. Keep the CI artifact link as the authority for the run-generated LCOV and build/test files.
Quality gate ERROR fails the export step; NONE is reported as **Not computed**, never passed.
Test/build failures fail the workflow independently of the static analysis result.
Distinct issue counts differ from the sum of overlapping software-quality dimensions.

## Required service settings

Automatic analysis must be Off for this project; CI analysis reads sonar-project.properties and imports LCOV.
The existing main branch must be next. Keep the Sonar way gate and existing new-code definition.
Set SONAR_TOKEN only in this fork's GitHub Actions encrypted secrets. It must authorize analysis in
cisco-projects. Never put tokens in tracked files, reports, scanner arguments or chat.
Personal token expiry must be managed in SonarCloud; renew the secret before expiry.

See [the change log](sonar-change-log.md) for before/after settings, files and execution evidence.
Official references: [CI analysis](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/ci-based-analysis/github-actions-for-sonarcloud),
[JS/TS coverage](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/test-coverage/javascript-typescript-test-coverage).
