import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from utils import app_paths


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AppPathsTests(unittest.TestCase):
    def setUp(self):
        self.test_root = PROJECT_ROOT / f".test_app_paths_{uuid.uuid4().hex}"
        self.test_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_database_and_log_are_stored_in_local_app_data(self):
        local_app_data = self.test_root / "local"
        local_app_data.mkdir()
        with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}):
            expected = local_app_data.resolve() / "PULSAR"
            self.assertEqual(app_paths.get_db_path(), expected / "medcrm.db")
            self.assertEqual(app_paths.get_crash_log_path(), expected / "crash.log")
            self.assertTrue(expected.is_dir())

    def test_migrates_legacy_database_without_removing_source(self):
        legacy_dir = self.test_root / "legacy"
        local_app_data = self.test_root / "local"
        legacy_dir.mkdir()
        local_app_data.mkdir()
        source = legacy_dir / "medcrm.db"
        source.write_bytes(b"encrypted database contents")
        with patch.dict(os.environ, {"LOCALAPPDATA": str(local_app_data)}):
            with patch.object(app_paths, "get_app_base_dir", return_value=legacy_dir):
                migrated = app_paths.migrate_legacy_app_data()
                destination = local_app_data.resolve() / "PULSAR" / "medcrm.db"
                self.assertEqual(migrated, [(source, destination)])
                self.assertEqual(destination.read_bytes(), source.read_bytes())
                self.assertTrue(source.exists())

                self.assertEqual(app_paths.migrate_legacy_app_data(), [])
                self.assertEqual(destination.read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
