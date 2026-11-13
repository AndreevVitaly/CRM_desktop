import sqlite3
import unittest
import uuid
from pathlib import Path

from models.db_models import Database


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ForeignKeyIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.db_path = PROJECT_ROOT / f".test_fk_{uuid.uuid4().hex}.db"
        self.database = Database(str(self.db_path), "")

    def tearDown(self):
        connection = getattr(self.database, "_connection", None)
        if connection is not None:
            connection.close()
            self.database._connection = None
        self.db_path.unlink(missing_ok=True)

    def _seed_user_and_patient(self, connection):
        user_id = connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES ('doctor', 'x', 'DOCTOR')"
        ).lastrowid
        patient_id = connection.execute(
            """
            INSERT INTO patients (callsign, birth_date, doctor_id)
            VALUES ('TEST', '2000-01-01', ?)
            """,
            (user_id,),
        ).lastrowid
        return user_id, patient_id

    def _reopen(self):
        self.database._connection.close()
        self.database._connection = None
        return self.database.connect()

    def test_enables_foreign_keys_on_every_connection(self):
        connection = self.database.connect()
        self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_replaces_invalid_nullable_zero_with_null(self):
        connection = self.database.connect()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO patients (callsign, birth_date, doctor_id) VALUES ('ZERO', '2000-01-01', 0)"
        )
        connection.commit()

        reopened = self._reopen()
        self.assertIsNone(
            reopened.execute(
                "SELECT doctor_id FROM patients WHERE callsign = 'ZERO'"
            ).fetchone()[0]
        )
        self.assertEqual(reopened.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_repairs_required_zero_from_related_record(self):
        connection = self.database.connect()
        user_id, patient_id = self._seed_user_and_patient(connection)
        document_id = connection.execute(
            """
            INSERT INTO documents (patient_id, classification, doc_date, author_id, doc_type)
            VALUES (?, 'NS', '2026-01-01', ?, 'MEETING')
            """,
            (patient_id, user_id),
        ).lastrowid
        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        encounter_id = connection.execute(
            """
            INSERT INTO encounters (patient_id, doctor_id, started_at, document_id)
            VALUES (?, 0, '2026-01-01', ?)
            """,
            (patient_id, document_id),
        ).lastrowid
        connection.commit()

        reopened = self._reopen()
        repaired_id = reopened.execute(
            "SELECT doctor_id FROM encounters WHERE id = ?", (encounter_id,)
        ).fetchone()[0]
        self.assertEqual(repaired_id, user_id)

    def test_stops_on_unresolvable_required_reference(self):
        connection = self.database.connect()
        _, patient_id = self._seed_user_and_patient(connection)
        connection.execute(
            "UPDATE patients SET doctor_id = NULL WHERE id = ?", (patient_id,)
        )
        connection.commit()
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            INSERT INTO encounters (patient_id, doctor_id, started_at)
            VALUES (?, 0, '2026-01-01')
            """,
            (patient_id,),
        )
        connection.commit()
        self.database._connection.close()
        self.database._connection = None

        with self.assertRaisesRegex(RuntimeError, "encounters"):
            self.database.connect()
        self.assertIsNone(self.database._connection)

        preserved = sqlite3.connect(self.db_path)
        try:
            self.assertEqual(preserved.execute("SELECT doctor_id FROM encounters").fetchone()[0], 0)
        finally:
            preserved.close()


if __name__ == "__main__":
    unittest.main()
