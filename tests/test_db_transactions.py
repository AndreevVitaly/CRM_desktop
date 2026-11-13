import sqlite3
import unittest
import uuid
from datetime import date
from pathlib import Path

from models import db_models as models


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EncounterTransactionTests(unittest.TestCase):
    def setUp(self):
        self.db_path = PROJECT_ROOT / f".test_encounter_transaction_{uuid.uuid4().hex}.db"
        instance = models.Database._instance
        if instance is not None and getattr(instance, "_connection", None) is not None:
            try:
                instance._connection.close()
            except Exception:
                pass
            instance._connection = None

        models.init_db(str(self.db_path), "")
        self.user = models.User.get_by_username("admin")
        self.patient = models.Patient(
            callsign="ТЕСТ-ТРАНЗАКЦИЯ",
            birth_date=date(1980, 1, 2),
            doctor_id=self.user.id,
        )
        self.patient.save()

    def tearDown(self):
        if getattr(models.db, "_connection", None) is not None:
            models.db._connection.close()
            models.db._connection = None
        self.db_path.unlink(missing_ok=True)

    def _new_encounter(self):
        return models.Encounter(
            patient_id=self.patient.id,
            doctor_id=self.user.id,
            meeting_result="message",
            patient_info="Тестовая информация",
            meeting_description="Описание встречи",
            status=models.Encounter.STATUS_FINISHED,
        )

    def test_rolls_back_encounter_and_informant_when_km_save_fails(self):
        encounter = self._new_encounter()
        informant = models.EncounterInformant(full_name="Иванов Иван")

        with self.assertRaises(sqlite3.IntegrityError):
            with models.db.transaction():
                encounter.save()
                informant.encounter_id = encounter.id
                informant.save()
                models.db.execute(
                    "INSERT INTO km_records (callsign, encounter_id) VALUES (?, ?)",
                    (None, encounter.id),
                )

        self.assertIsNone(
            models.db.fetchone(
                "SELECT id FROM encounters WHERE uuid = ?", (encounter.uuid,)
            )
        )
        self.assertEqual(
            models.db.fetchone(
                "SELECT COUNT(*) AS cnt FROM encounter_informants WHERE full_name = ?",
                (informant.full_name,),
            )["cnt"],
            0,
        )

    def test_commits_all_encounter_records_together(self):
        encounter = self._new_encounter()
        informant = models.EncounterInformant(full_name="Иванов Иван")
        km_record = models.KmRecord(
            callsign=self.patient.callsign,
            full_name=informant.full_name,
        )

        with models.db.transaction():
            encounter.save()
            informant.encounter_id = encounter.id
            informant.save()
            km_record.encounter_id = encounter.id
            km_record.save()

        self.assertIsNotNone(models.Encounter.get_by_id(encounter.id))
        self.assertEqual(len(models.EncounterInformant.get_by_encounter(encounter.id)), 1)
        self.assertEqual(len(models.KmRecord.get_by_encounter(encounter.id)), 1)


if __name__ == "__main__":
    unittest.main()
