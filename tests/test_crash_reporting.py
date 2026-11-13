import shutil
import unittest
import uuid
from datetime import datetime
from pathlib import Path

from utils.crash_reporting import write_crash_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CrashReportingTests(unittest.TestCase):
    def setUp(self):
        self.test_root = PROJECT_ROOT / f".test_crash_report_{uuid.uuid4().hex}"
        self.test_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_writes_primary_crash_report_with_diagnostics(self):
        primary = self.test_root / "primary" / "crash.log"
        result = write_crash_report(
            "Traceback: test failure",
            occurred_at=datetime(2026, 11, 13, 15, 30, 0),
            primary_path=primary,
            fallback_paths=(),
        )

        self.assertEqual(result.path, primary.resolve())
        self.assertEqual(result.errors, ())
        report = primary.read_text(encoding="utf-8")
        self.assertIn("2026-11-13 15:30:00", report)
        self.assertIn("Executable:", report)
        self.assertIn("Traceback: test failure", report)

    def test_uses_fallback_and_reports_primary_write_error(self):
        blocked_parent = self.test_root / "blocked"
        blocked_parent.write_text("not a directory", encoding="utf-8")
        primary = blocked_parent / "crash.log"
        fallback = self.test_root / "fallback" / "crash.log"

        result = write_crash_report(
            "fallback test",
            primary_path=primary,
            fallback_paths=(fallback,),
        )

        self.assertEqual(result.path, fallback.resolve())
        self.assertTrue(result.errors)
        self.assertIn(str(primary), result.errors[0])
        self.assertIn("fallback test", fallback.read_text(encoding="utf-8"))

    def test_returns_all_errors_when_no_location_is_writable(self):
        blocked = self.test_root / "blocked"
        blocked.write_text("not a directory", encoding="utf-8")

        result = write_crash_report(
            "cannot save",
            primary_path=blocked / "first.log",
            fallback_paths=(blocked / "second.log",),
        )

        self.assertIsNone(result.path)
        self.assertEqual(len(result.errors), 2)


if __name__ == "__main__":
    unittest.main()
