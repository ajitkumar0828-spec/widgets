"""Contract checks for pagination, CSV escaping and monorepo LCOV resolution."""
import csv
import io
from pathlib import Path
import tempfile
import unittest
from report import csv_text, normalize_lcov, paginate, validate_test_inclusions


class ReportChecks(unittest.TestCase):
    def test_pagination_and_duplicates(self):
        records = [{"key": str(i)} for i in range(1001)]
        calls = []
        def get(endpoint, **params):
            calls.append(params["p"])
            start = (params["p"] - 1) * params["ps"]
            return {"paging": {"total": len(records)}, "issues": records[start:start + params["ps"]]}
        self.assertEqual(paginate(get, "/issues", "issues", {}), records)
        self.assertEqual(calls, [1, 2, 3])
        records[-1] = records[0]
        with self.assertRaises(ValueError):
            paginate(get, "/issues", "issues", {})

    def test_test_inclusions_do_not_hide_production(self):
        paths = ["packages/contact-center/store/src/index.ts",
                 "packages/contact-center/cc-components/src/widget.tsx"]
        with self.assertRaises(ValueError):
            validate_test_inclusions(paths, ["**/*.ts", "**/*.tsx"])
        validate_test_inclusions(paths, ["packages/contact-center/*/tests/**/*.ts",
                                         "packages/contact-center/*/tests/**/*.tsx"])

    def test_csv_quotes_newlines_and_formula(self):
        message = 'comma, quote " and\nnewline'
        data = csv_text([{"key": "issue", "message": message},
                         {"key": "formula", "message": "=1+1"}])
        rows = list(csv.DictReader(io.StringIO(data)))
        self.assertEqual(rows[0]["message"], message)
        self.assertEqual(rows[1]["message"], "'=1+1")

    def test_same_filename_in_two_workspaces_and_reject_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for pkg in ("a", "b"):
                source = root / pkg / "src/index.ts"
                source.parent.mkdir(parents=True)
                source.write_text("export const value = 1;")
                report = root / (pkg + ".info")
                report.write_text("SF:src/index.ts\nDA:1,1\nend_of_record\n")
                paths = normalize_lcov(root, pkg, report, {pkg + "/src/index.ts"})
                self.assertEqual(paths, [pkg + "/src/index.ts"])
                self.assertIn("SF:" + pkg + "/src/index.ts", report.read_text())
            report.write_text("SF:../outside.ts\nDA:1,1\nend_of_record\n")
            with self.assertRaises(ValueError):
                normalize_lcov(root, "a", report, {"a/src/index.ts"})

    def test_incomplete_lcov_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "src").mkdir()
            (root / "src/index.ts").write_text("export {};")
            report = root / "bad.info"
            report.write_text("SF:src/index.ts\nDA:1,1\n")
            with self.assertRaises(ValueError):
                normalize_lcov(root, ".", report, {"src/index.ts"})


if __name__ == "__main__":
    unittest.main()
