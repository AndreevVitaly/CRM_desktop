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


if __name__ == "__main__":
    unittest.main()
