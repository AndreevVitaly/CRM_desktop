import shutil
import sqlite3
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from utils.db_encryption import (
    _install_encrypted_database,
    encrypt_existing_database,
    is_encrypted_database,
    is_sqlcipher_available,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DatabaseEncryptionFileInstallTests(unittest.TestCase):
    def setUp(self):
        self.test_root = PROJECT_ROOT / f".test_db_encryption_{uuid.uuid4().hex}"
        self.test_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_root, ignore_errors=True)

    def test_failed_final_replace_keeps_original_database(self):
        destination = self.test_root / "medcrm.db"
        encrypted = self.test_root / "medcrm.encrypted_tmp.db"
        destination.write_bytes(b"original database")
        encrypted.write_bytes(b"encrypted database")

        with patch(
            "utils.db_encryption.os.replace",
            side_effect=OSError("simulated replace failure"),
        ):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                _install_encrypted_database(encrypted, destination)

        self.assertEqual(destination.read_bytes(), b"original database")
        self.assertEqual(encrypted.read_bytes(), b"encrypted database")

    def test_successful_final_replace_installs_encrypted_database(self):
        destination = self.test_root / "medcrm.db"
        encrypted = self.test_root / "medcrm.encrypted_tmp.db"
        destination.write_bytes(b"original database")
        encrypted.write_bytes(b"encrypted database")

        _install_encrypted_database(encrypted, destination)

        self.assertEqual(destination.read_bytes(), b"encrypted database")
        self.assertFalse(encrypted.exists())

    @unittest.skipUnless(is_sqlcipher_available(), "SQLCipher is not installed")
    def test_encrypts_database_and_keeps_verified_plain_backup(self):
        destination = self.test_root / "medcrm.db"
        connection = sqlite3.connect(destination)
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample (value) VALUES ('important data')")
        connection.commit()
        connection.close()

        backup = encrypt_existing_database(destination, "strong test password")

        self.assertTrue(destination.exists())
        self.assertTrue(is_encrypted_database(destination, "strong test password"))
        self.assertTrue(backup.exists())
        backup_connection = sqlite3.connect(backup)
        try:
            value = backup_connection.execute("SELECT value FROM sample").fetchone()[0]
        finally:
            backup_connection.close()
        self.assertEqual(value, "important data")


if __name__ == "__main__":
    unittest.main()
