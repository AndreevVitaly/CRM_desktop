import tempfile
import unittest
from datetime import date
from pathlib import Path

from models import db_models as models


class PlansTableTests(unittest.TestCase):
    def setUp(self):
        if models.Database._connection is not None:
            models.Database._connection.close()
        models.Database._connection = None
        models.Database._instance = None
        self.db_path = Path(tempfile.mktemp(suffix=".sqlite"))
        models.init_db(str(self.db_path), "")
        self.user = models.User(username="plan_user", password_hash="x", role="admin")
        self.user.save()
        self.patient = models.Patient(callsign="Планов", personal_number="TEST-PLAN")
        self.patient.save()

    def tearDown(self):
        if models.Database._connection is not None:
            models.Database._connection.close()
        models.Database._connection = None
        models.Database._instance = None

    def test_plan_round_trip(self):
        columns = {row[1] for row in models.db.fetchall("PRAGMA table_info(plans)")}
        self.assertTrue({"patient_id", "author_id", "plan_type", "title", "status"}.issubset(columns))

        plan = models.Plan(
            patient_id=self.patient.id,
            author_id=self.user.id,
            plan_type="ANNUAL",
            title="План на 2026 год",
            period_year=2026,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 12, 31),
            status="ACTIVE",
        )
        plan.save()

        loaded = models.Plan.get_by_id(plan.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.title, "План на 2026 год")
        self.assertEqual(loaded.period_start, date(2026, 1, 1))
        self.assertEqual(loaded.status, "ACTIVE")


if __name__ == "__main__":
    unittest.main()
