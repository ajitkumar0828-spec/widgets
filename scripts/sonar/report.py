#!/usr/bin/env python3
"""Auditable Contact Center scope, LCOV and SonarCloud exports (stdlib only)."""
import argparse
import csv
import fnmatch
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HOST = "https://sonarcloud.io"
CODE = {".ts", ".tsx", ".js", ".jsx", ".css", ".scss"}
COVERABLE = {".ts", ".tsx", ".js", ".jsx"}
METRICS = [
    "ncloc", "lines", "coverage", "line_coverage", "branch_coverage",
    "lines_to_cover", "uncovered_lines", "conditions_to_cover", "uncovered_conditions",
    "duplicated_lines_density", "duplicated_lines", "duplicated_blocks",
    "bugs", "vulnerabilities", "code_smells", "security_hotspots",
    "reliability_rating", "security_rating", "sqale_rating",
    "software_quality_reliability_issues", "software_quality_security_issues",
    "software_quality_maintainability_issues", "software_quality_reliability_rating",
    "software_quality_security_rating", "software_quality_maintainability_rating",
    "security_hotspots_reviewed", "alert_status"
]


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def properties(path):
    result = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def inside(path, roots):
    return any(path.startswith(root.rstrip("/") + "/") for root in roots)


def production(path, roots):
    return (inside(path, roots) and Path(path).suffix in CODE
            and not path.endswith(".d.ts")
            and not any(part in {"__tests__", "__mocks__", "node_modules", "dist", "coverage"}
                        for part in Path(path).parts)
            and not any(fnmatch.fnmatch(Path(path).name, pattern)
                        for pattern in ("*.test.*", "*.spec.*")))


def scope(root):
    props = properties(root / "sonar-project.properties")
    sources = props["sonar.sources"].split(",")
    tests = props["sonar.tests"].split(",")
    if props["sonar.projectKey"] == "ajitkumar0828-spec_webex-js-sdk":
        approved = ["packages/@webex/contact-center/src"]
        approved_tests = ["packages/@webex/contact-center/test/unit"]
    elif props["sonar.projectKey"] == "ajitkumar0828-spec_widgets":
        modules = ["ai-assistant", "cc-components", "cc-digital-channels", "cc-widgets",
                   "station-login", "store", "task", "ui-logging", "user-state"]
        approved = ["packages/contact-center/" + m + "/src" for m in modules]
        approved_tests = ["packages/contact-center/" + m + "/tests" for m in modules
                          if m != "cc-widgets"]
    else:
        raise ValueError("Project is outside the two approved forks")
    if sources != approved or tests != approved_tests or props["sonar.organization"] != "cisco-projects":
        raise ValueError("Configured scope differs from the approved Contact Center scope")
    if any("*" in p or ".." in Path(p).parts for p in sources + tests):
        raise ValueError("Scope roots must be explicit repository-relative directories")
    if any(inside(t + "/", sources) or inside(s + "/", tests) for s in sources for t in tests):
        raise ValueError("Production and test roots overlap")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    prod = sorted(p for p in tracked if production(p, sources))
    test = sorted(p for p in tracked if inside(p, tests) and Path(p).suffix in COVERABLE)
    if not prod or not test:
        raise ValueError("Empty production or unit-test scope")
    for p in prod + test:
        (root / p).read_text(encoding="utf-8")
    for config in props["sonar.typescript.tsconfigPaths"].split(","):
        if not (root / config).is_file():
            raise ValueError("Missing TypeScript configuration: " + config)
    return {"sourceRoots": sources, "testRoots": tests,
            "productionFiles": prod, "testFiles": test, "encoding": "UTF-8"}


def normalize_lcov(root, package, report, allowed):
    text = report.read_text(encoding="utf-8")
    records = 0
    paths = []
    output = []
    for line in text.splitlines():
        if line.startswith("SF:"):
            value = line[3:].replace("\\", "/")
            candidates = set()
            for candidate in (root / value, root / package / value):
                candidate = candidate.resolve()
                try:
                    relative = candidate.relative_to(root.resolve()).as_posix()
                except ValueError:
                    continue
                if relative in allowed:
                    candidates.add(relative)
            if len(candidates) != 1:
                raise ValueError("Unresolved or ambiguous LCOV source: " + value)
            path = candidates.pop()
            if path in paths:
                raise ValueError("Duplicate LCOV source: " + path)
            paths.append(path)
            output.append("SF:" + path)
        else:
            output.append(line)
        if line == "end_of_record":
            records += 1
    if not paths or records != len(paths):
        raise ValueError("Missing/incomplete LCOV records: " + str(report))
    report.write_text("\n".join(output) + "\n", encoding="utf-8")
    return paths


def paginate(get, endpoint, field, params):
    items, page, total = [], 1, None
    while total is None or len(items) < total:
        data = get(endpoint, **params, p=page, ps=500)
        batch = data[field]
        reported = data.get("paging", {}).get("total", data.get("total"))
        if reported is None:
            raise ValueError("Missing pagination total: " + endpoint)
        if total is not None and total != reported:
            raise ValueError("Results changed during export; rerun for a consistent snapshot")
        total = reported
        if not batch and len(items) < total:
            raise ValueError("Truncated paginated response: " + endpoint)
        items.extend(batch)
        page += 1
    if len(items) != total:
        raise ValueError("Pagination count mismatch: " + endpoint)
    keys = [x.get("key", x.get("id")) for x in items]
    if all(k is not None for k in keys) and len(set(keys)) != len(keys):
        raise ValueError("Duplicate entries during pagination: " + endpoint)
    return items


class API:
    def __call__(self, endpoint, **params):
        request = Request(HOST + endpoint + "?" + urlencode(params))
        token = os.environ.get("SONAR_TOKEN")
        if token:
            request.add_header("Authorization", "Bearer " + token)
        for attempt in range(4):
            try:
                with urlopen(request, timeout=45) as response:
                    return json.load(response)
            except HTTPError as error:
                if error.code not in {429, 502, 503, 504} or attempt == 3:
                    raise RuntimeError("Sonar API HTTP " + str(error.code) + ": " + endpoint) from None
                time.sleep(2 ** attempt)
        raise RuntimeError("Sonar API retries exhausted")


def csv_text(issues):
    stream = io.StringIO(newline="")
    columns = ["key", "rule", "type", "severity", "status", "component", "line",
               "message", "effort", "impacts", "url"]
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for issue in issues:
        row = {key: issue.get(key, "") for key in columns}
        row["impacts"] = json.dumps(row["impacts"], ensure_ascii=False) if row["impacts"] else ""
        # Preserve CSV escaping and prevent spreadsheet formula execution.
        row = {key: "'" + value if isinstance(value, str) and value[:1] in "=+-@\t\r"
               else value for key, value in row.items()}
        writer.writerow(row)
    return stream.getvalue()


def export(args):
    root, out = Path.cwd().resolve(), Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    api = API()
    props = properties(root / "sonar-project.properties")
    key, branch = args.project or props["sonar.projectKey"], args.branch
    task, analysis = None, None
    if not args.snapshot:
        metadata = properties(root / ".scannerwork/report-task.txt")
        if metadata.get("projectKey") != key:
            raise ValueError("Scanner task belongs to a different project")
        for _ in range(100):
            task = api("/api/ce/task", id=metadata["ceTaskId"], additionalFields="warnings")["task"]
            if task["status"] in {"SUCCESS", "FAILED", "CANCELED"}:
                break
            time.sleep(5)
        save(out / "ce-task.json", task)
        if task["status"] != "SUCCESS":
            raise ValueError("Server processing: " + task["status"])
        analysis = task["analysisId"]
    analyses = api("/api/project_analyses/search", project=key, branch=branch, ps=100)["analyses"]
    selected = next((a for a in analyses if a["key"] == analysis), None) if analysis else analyses[0]
    if selected is None:
        raise ValueError("Processed analysis not found on requested branch")
    sha = args.sha or os.environ.get("GITHUB_SHA")
    if not args.snapshot and (not sha or selected.get("revision") != sha):
        raise ValueError("Server revision does not equal the requested scanned commit")
    branches = api("/api/project_branches/list", project=key)["branches"]
    # Omit SCM author/contact data from evidence.
    branch_data = [{k: b.get(k) for k in ("name", "isMain", "type", "analysisDate")} for b in branches]
    if not args.snapshot and not any(b["name"] == branch and b["isMain"] for b in branches):
        raise ValueError("The scanned branch must be the Sonar main branch")
    available = {m["key"] for m in paginate(api, "/api/metrics/search", "metrics", {})}
    measured = api("/api/measures/component", component=key, branch=branch,
                   metricKeys=",".join(m for m in METRICS if m in available))
    metrics = {m["metric"]: m.get("value") for m in measured["component"]["measures"]}
    gate = api("/api/qualitygates/project_status", analysisId=selected["key"])["projectStatus"]
    issues = paginate(api, "/api/issues/search", "issues",
                      {"componentKeys": key, "branch": branch, "resolved": "false"})
    safe_issues = []
    for issue in issues:
        safe = {k: issue[k] for k in ("key", "rule", "type", "severity", "status", "component",
                "line", "message", "effort", "impacts", "tags", "textRange", "creationDate",
                "updateDate") if k in issue}
        safe["url"] = HOST + "/project/issues?" + urlencode({"id": key, "branch": branch,
                                                          "open": issue["key"]})
        safe_issues.append(safe)
    components = paginate(api, "/api/components/tree", "components",
                           {"component": key, "branch": branch, "qualifiers": "FIL", "strategy": "all"})
    validation = {"snapshotOnly": args.snapshot}
    if not args.snapshot:
        manifest = json.loads((root / "reports/sonar/scope.json").read_text())
        test_paths = set(manifest["testFiles"])
        expected = set(manifest["productionFiles"])
        actual = {c["path"] for c in components}
        outside = sorted(actual - expected - test_paths)
        missing = sorted(expected - actual)
        validation = {"unexpectedFiles": outside, "missingProductionFiles": missing,
                      "productionFiles": len(actual & expected), "testFiles": len(actual & test_paths),
                      "sourceAndTestRootsDisjoint": True}
        save(out / "scope-validation.json", validation)
        if outside or missing:
            raise ValueError("Server file scope differs from the approved source/test manifest")
        coverage = json.loads((root / "reports/sonar/coverage-validation.json").read_text())
        validation["lcov"] = coverage
        if "coverage" not in metrics or "lines_to_cover" not in metrics:
            raise ValueError("Server has no imported coverage/lines-to-cover metrics")
        file_measures = paginate(api, "/api/measures/component_tree", "components", {
            "component": key, "branch": branch, "qualifiers": "FIL", "strategy": "all",
            "metricKeys": "ncloc,lines_to_cover,uncovered_lines,coverage"})
        save(out / "file-measures.json", file_measures)
        measured_files = {f["path"]: {m["metric"]: m.get("value") for m in f.get("measures", [])}
                          for f in file_measures}
        wrongly_counted_tests = [p for p in test_paths
                                if float(measured_files.get(p, {}).get("ncloc", 0)) > 0]
        if wrongly_counted_tests:
            raise ValueError("Unit tests were counted as production code")
        imported = []
        for entry in coverage:
            if "lcov" not in entry:
                continue
            current, hit_files = None, set()
            for line in (root / entry["lcov"]).read_text().splitlines():
                if line.startswith("SF:"):
                    current = line[3:]
                elif line.startswith("DA:") and int(line.split(",")[1]) > 0:
                    hit_files.add(current)
            confirmed = [p for p in hit_files if
                         float(measured_files.get(p, {}).get("lines_to_cover", 0)) -
                         float(measured_files.get(p, {}).get("uncovered_lines", 0)) > 0]
            if not confirmed:
                raise ValueError("LCOV import could not be verified for " + entry["package"])
            imported.append({"package": entry["package"], "filesWithServerCoveredLines": len(confirmed)})
        validation["coverageImports"] = imported
        validation["testsCountedAsProduction"] = wrongly_counted_tests
        save(out / "scope-validation.json", validation)
        # Ensure we export a stable analysis rather than mixing two scans.
        latest = api("/api/project_analyses/search", project=key, branch=branch, ps=1)["analyses"][0]
        if latest["key"] != selected["key"]:
            raise ValueError("A newer analysis arrived during export")
    warnings = (task or {}).get("warnings", [])
    report = {"project": key, "organization": "cisco-projects", "branch": branch,
              "commit": selected.get("revision"), "analysisId": selected["key"],
              "analysisTime": selected["date"], "exportedAt": datetime.now(timezone.utc).isoformat(),
              "baseline": args.snapshot, "metrics": metrics, "qualityGate": gate,
              "distinctOpenIssues": len(safe_issues), "warnings": warnings,
              "warningCount": (task or {}).get("warningCount"), "scopeValidation": validation,
              "workflowRun": os.environ.get("GITHUB_RUN_URL"),
              "dashboard": HOST + "/summary/overall?" + urlencode({"id": key, "branch": branch})}
    save(out / "summary.json", report)
    save(out / "issues.json", {"total": len(safe_issues), "issues": safe_issues})
    save(out / "files.json", components)
    save(out / "branches.json", branch_data)
    save(out / "analysis.json", {k: selected.get(k) for k in ("key", "date", "revision", "projectVersion")})
    (out / "issues.csv").write_text(csv_text(safe_issues), encoding="utf-8")
    lines = ["# Contact Center SonarCloud report", "",
             "**Historical whole-repository baseline. Not comparable to the new Contact Center scope.**"
             if args.snapshot else "Contact Center production scope; unit tests are classified separately.",
             "", "| Field | Value |", "|---|---|"]
    fields = {"Project": key, "Organization": "cisco-projects", "Branch": branch,
              "Commit": selected.get("revision"), "Analysis time": selected["date"],
              "Quality gate": gate["status"] + (" (Not computed)" if gate["status"] == "NONE" else ""),
              "Distinct open issues": len(safe_issues), "Server warning count": report["warningCount"],
              "Dashboard": report["dashboard"], "Workflow": report["workflowRun"]}
    fields.update(metrics)
    fields.setdefault("coverage", "No coverage data")
    fields.setdefault("line_coverage", "No coverage data")
    for name in list(fields):
        if name.endswith("_rating") and fields[name] is not None:
            fields[name] = "ABCDE"[min(4, max(0, int(float(fields[name])) - 1))]
    for name, value in fields.items():
        lines.append("| " + name + " | " + str(value if value is not None else "Unavailable").replace("|", "\\|") + " |")
    lines += ["", "Quality dimensions may overlap: do not sum their issue counts as distinct issues.",
              "Missing coverage means unavailable, not 0% or passed. Gate NONE means Not computed.",
              "", "## Analysis warnings", ""] + [str(w) for w in warnings]
    if args.snapshot:
        lines += ["Baseline warnings observed in the dashboard: Python version unspecified; source encoding; unresolved tsconfig; architecture analysis errors.",
                  "The prior automatic analysis ignored sonar-project.properties and imported no coverage."]
    else:
        status = root / "reports/sonar/test-status.json"
        tests = json.loads(status.read_text()) if status.exists() else []
        save(out / "test-status.json", tests)
        lines += ["", "## Unit test outcomes", "",
                  "Thresholds are preserved. A failed test/build is not a passing scan.",
                  "cc-widgets has no tests; its production files remain in the coverage denominator."] if "widgets" in key else ["", "## Unit test outcomes", ""]
        build_status = root / "reports/sonar/build-status.json"
        if build_status.exists():
            builds = json.loads(build_status.read_text())
            save(out / "build-status.json", builds)
            lines += ["", "Build commands that failed: " + str(sum(b["status"] == "failed" for b in builds)),
                      "Original workspace test failures stay failed even if a separate Jest invocation produced LCOV."]
        lines += ["", "```json", json.dumps(tests, indent=2), "```"]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Report exported:", out, "gate:", gate["status"], "open issues:", len(safe_issues))
    return 1 if not args.snapshot and gate["status"] == "ERROR" else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["scope", "normalize", "export"])
    parser.add_argument("--project")
    parser.add_argument("--branch", default="next")
    parser.add_argument("--sha")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--output", default="reports/sonar/latest")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if args.command == "scope":
        manifest = scope(root)
        save(root / "reports/sonar/scope.json", manifest)
        print("Production files:", len(manifest["productionFiles"]), "test files:", len(manifest["testFiles"]))
        return 0
    if args.command == "normalize":
        manifest = scope(root)
        results = []
        for source in manifest["sourceRoots"]:
            package = str(Path(source).parent)
            name = Path(package).name
            report = root / "coverage/sonar" / name / "lcov.info"
            if name == "cc-widgets":
                results.append({"package": package, "status": "no tests; uncovered code remains in analysis"})
                continue
            allowed = {p for p in manifest["productionFiles"]
                       if p.startswith(source + "/") and Path(p).suffix in COVERABLE}
            paths = normalize_lcov(root, package, report, allowed)
            results.append({"package": package, "lcov": report.relative_to(root).as_posix(),
                            "files": paths, "sourceCount": len(paths)})
        save(root / "reports/sonar/coverage-validation.json", results)
        return 0
    return export(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # Do not print URLs, request headers or response bodies containing credentials.
        message = type(error).__name__ + ": " + str(error)
        print(message, file=sys.stderr)
        if len(sys.argv) > 1 and sys.argv[1] == "export":
            failure = Path("reports/sonar/latest")
            save(failure / "validation-failure.json", {"status": "unverified", "error": message,
                 "commit": os.environ.get("GITHUB_SHA"), "workflowRun": os.environ.get("GITHUB_RUN_URL")})
            (failure / "SUMMARY.md").write_text(
                "# Sonar report validation failed\n\n" + message +
                "\n\nDo not treat this run as a verified passing analysis.\n", encoding="utf-8")
        sys.exit(1)
