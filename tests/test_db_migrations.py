import sqlite3
import unittest
import uuid
from pathlib import Path

from models.db_models import Database


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.db_path = PROJECT_ROOT / f".test_patient_migration_{uuid.uuid4().hex}.db"

    def tearDown(self):
        instance = Database._instance
        if instance is not None and getattr(instance, "_connection", None) is not None:
            try:
                instance._connection.close()
            except Exception:
                pass
            instance._connection = None
        self.db_path.unlink(missing_ok=True)

    def _create_legacy_table(self, birth_date_not_null=True):
        connection = sqlite3.connect(self.db_path)
        nullability = "NOT NULL" if birth_date_not_null else ""
        connection.execute(
            f"""
            CREATE TABLE patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                middle_name TEXT,
                birth_date DATE {nullability},
                gender TEXT(1),
                patient_type TEXT DEFAULT 'adult',
                department TEXT,
                doctor_id INTEGER,
                facility_id INTEGER,
                phone TEXT,
                email TEXT,
                document_id TEXT,
                insurance_number TEXT,
                employer TEXT,
                callsign TEXT,
                address TEXT,
                emergency_contact TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        return connection

    def test_migrates_legacy_patients_and_is_idempotent(self):
        connection = self._create_legacy_table()
        connection.execute(
            """
            INSERT INTO patients
            (first_name, last_name, middle_name, birth_date, patient_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Иван", "Иванов", "Иванович", "1980-01-02", "adult"),
        )
        connection.commit()
        connection.close()

        database = Database(str(self.db_path), "")
        migrated = database.connect()
        columns = {
            row[1] for row in migrated.execute("PRAGMA table_info(patients)").fetchall()
        }

        self.assertNotIn("first_name", columns)
        self.assertNotIn("email", columns)
        self.assertTrue({"uuid", "callsign", "personal_number", "updated_at"} <= columns)
        row = migrated.execute(
            "SELECT callsign, birth_date, updated_at FROM patients"
        ).fetchone()
        self.assertEqual(row[0], "Иванов Иван Иванович")
        self.assertEqual(row[1], "1980-01-02")
        self.assertTrue(row[2])
        self.assertEqual(
            migrated.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE name='patients_new'"
            ).fetchone()[0],
            0,
        )

        database._create_tables()
        self.assertEqual(
            migrated.execute("SELECT COUNT(*) FROM patients").fetchone()[0], 1
        )

    def test_failed_migration_rolls_back_and_preserves_source(self):
        connection = self._create_legacy_table(birth_date_not_null=False)
        connection.execute(
            """
            INSERT INTO patients (first_name, last_name, birth_date)
            VALUES ('Иван', 'Иванов', NULL)
            """
        )
        connection.commit()
        connection.close()

        database = Database(str(self.db_path), "")
        with self.assertRaisesRegex(RuntimeError, "Исходная таблица сохранена"):
            database.connect()
        self.assertIsNone(database._connection)

        preserved = sqlite3.connect(self.db_path)
        try:
            columns = {
                row[1]
                for row in preserved.execute("PRAGMA table_info(patients)").fetchall()
            }
            self.assertIn("first_name", columns)
            self.assertEqual(
                preserved.execute("SELECT COUNT(*) FROM patients").fetchone()[0], 1
            )
            self.assertEqual(
                preserved.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE name='patients_new'"
                ).fetchone()[0],
                0,
            )
        finally:
            preserved.close()

    def test_adds_all_columns_required_to_save_legacy_encounter(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute(
            """
            CREATE TABLE encounters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                reason TEXT,
                status TEXT DEFAULT 'PLANNED',
                treatment_plan_item_id INTEGER
            )
            """
        )
        connection.commit()
        connection.close()

        database = Database(str(self.db_path), "")
        migrated = database.connect()
        columns = {
            row[1]
            for row in migrated.execute("PRAGMA table_info(encounters)").fetchall()
        }
        required = {
            "id",
            "uuid",
            "patient_id",
            "doctor_id",
            "started_at",
            "finished_at",
            "reason",
            "status",
            "treatment_plan_item_id",
            "document_id",
            "group_id",
            "meeting_result",
            "patient_info",
            "meeting_description",
            "information_relevance",
            "information_importance",
            "information_timeliness",
            "information_completeness",
            "information_novelty",
            "information_reliability",
            "patient_tasks",
            "patient_measures",
            "general_measures",
            "updated_at",
        }
        self.assertTrue(required <= columns)

    def test_removes_email_from_existing_plain_and_encrypted_databases(self):
        from utils.sync_exchange import _apply_users

        for password in ('', 'migration-test-password'):
            with self.subTest(encrypted=bool(password)):
                database = Database(str(self.db_path), password)
                connection = database.connect()
                connection.execute('ALTER TABLE users ADD COLUMN email TEXT')
                connection.execute('ALTER TABLE patients ADD COLUMN email TEXT')
                user_id = connection.execute(
                    "INSERT INTO users (username, password_hash, role, email) "
                    "VALUES ('test', 'saved-hash', 'DOCTOR', 'old@example.com')"
                ).lastrowid
                patient_id = connection.execute(
                    "INSERT INTO patients (callsign, birth_date, doctor_id, phone, email) "
                    "VALUES ('TEST', '1980-01-01', ?, '12345', 'patient@example.com')",
                    (user_id,),
                ).lastrowid
                connection.commit()
                connection.close()
                database._connection = None

                migrated = database.connect()
                for table in ('users', 'patients'):
                    columns = {r[1] for r in migrated.execute(f'PRAGMA table_info({table})')}
                    self.assertNotIn('email', columns)
                self.assertEqual(tuple(migrated.execute(
                    'SELECT username, password_hash FROM users WHERE id = ?', (user_id,)
                ).fetchone()), ('test', 'saved-hash'))
                self.assertEqual(tuple(migrated.execute(
                    'SELECT callsign, doctor_id, phone FROM patients WHERE id = ?', (patient_id,)
                ).fetchone()), ('TEST', user_id, '12345'))
                summary = _apply_users([{'username': 'old-package', 'email': 'ignored@example.com'}])
                self.assertEqual(summary['new'], 1)
                database.commit()
                database._create_tables()  # Migration may safely run again.
                self.assertEqual(migrated.execute('PRAGMA foreign_key_check').fetchall(), [])
                migrated.close()
                database._connection = None
                self.db_path.unlink()

    def test_email_migration_rolls_back_all_tables_on_failure(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute('CREATE TABLE first_table (id INTEGER PRIMARY KEY, email TEXT)')
        connection.execute('CREATE TABLE second_table (id INTEGER PRIMARY KEY, email TEXT)')
        connection.execute("INSERT INTO first_table VALUES (1, 'preserved@example.com')")
        connection.commit()

        class FailingCursor:
            def execute(self, statement, parameters=()):
                if statement.startswith('ALTER TABLE "second_table"'):
                    raise sqlite3.OperationalError('simulated migration failure')
                return connection.execute(statement, parameters)

        database = Database(str(self.db_path), '')
        with self.assertRaisesRegex(sqlite3.OperationalError, 'simulated migration failure'):
            database._remove_email_columns(FailingCursor())
        self.assertEqual(connection.execute('SELECT email FROM first_table').fetchone()[0],
                         'preserved@example.com')
        connection.close()

    def test_column_migration_surfaces_real_sqlite_error_and_rolls_back(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")

        class FailingCursor:
            def __init__(self, wrapped):
                self.wrapped = wrapped

            def execute(self, statement, parameters=()):
                if statement.startswith("ALTER TABLE sample"):
                    raise sqlite3.OperationalError("simulated disk I/O error")
                return self.wrapped.execute(statement, parameters)

        database = Database(str(self.db_path), "")
        cursor = FailingCursor(connection.cursor())
        with self.assertRaisesRegex(
            RuntimeError,
            r"sample.*new_field.*simulated disk I/O error",
        ):
            database._ensure_table_columns(
                cursor, "sample", [("new_field", "TEXT")]
            )

        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(sample)").fetchall()
        }
        self.assertNotIn("new_field", columns)
        connection.close()


if __name__ == "__main__":
    unittest.main()
