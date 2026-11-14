import unittest
import uuid
from datetime import date
from pathlib import Path
from types import MethodType, SimpleNamespace
from unittest.mock import Mock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QTableWidget

from models import db_models as models
from ui.document_form import DocumentFormDialog
from ui.encounter_edit_form import EncounterEditDialog
from ui.patient_detail import PatientDetailDialog


class PatientEncounterRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.path = Path(__file__).resolve().parents[1] / f'.test_refresh_{uuid.uuid4().hex}.db'
        if getattr(models.db, '_connection', None) is not None:
            models.db._connection.close()
            models.db._connection = None
        models.init_db(str(self.path), '')
        self.user = models.User.get_by_username('admin')
        self.patient = models.Patient(callsign='TEST', birth_date=date(1980, 1, 1),
                                      doctor_id=self.user.id)
        self.patient.save()
        self.card = SimpleNamespace(
            user=self.user, patient=self.patient,
            encounters_table=QTableWidget(0, 9), documents_table=QTableWidget(0, 7),
            _load_plans=Mock(), _log_interaction=Mock(),
        )
        for name in ('_load_documents', '_load_encounters', '_refresh_document_views',
                     '_get_encounter_status_color'):
            method = getattr(PatientDetailDialog, name)
            setattr(self.card, name, MethodType(method, self.card))

    def tearDown(self):
        models.db._connection.close()
        models.db._connection = None
        self.path.unlink(missing_ok=True)

    def test_new_meeting_appears_in_existing_card_from_either_add_button(self):
        for action in ('_add_document', '_add_encounter'):
            with self.subTest(action=action):
                dialog = DocumentFormDialog(self.user, self.patient)
                dialog.doc_type_selector.setCurrentIndex(
                    dialog.doc_type_selector.findData(models.DOCUMENT_TYPE_MEETING)
                )
                dialog.summary_input.setPlainText(action)

                def save():
                    with patch('ui.document_form.QMessageBox.information'):
                        dialog._save()
                    self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
                    return dialog.result()

                with patch('ui.document_form.DocumentFormDialog', return_value=dialog), patch.object(
                    dialog, 'exec', side_effect=save
                ):
                    getattr(PatientDetailDialog, action)(self.card)
                ids = [self.card.encounters_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                       for row in range(self.card.encounters_table.rowCount())]
                self.assertIn(dialog.document.id, ids)
                self.assertEqual(self.card.documents_table.rowCount(), len(ids))

    def test_cancel_does_not_reload_lists(self):
        with patch('ui.document_form.DocumentFormDialog') as dialog:
            dialog.return_value.exec.return_value = QDialog.DialogCode.Rejected
            PatientDetailDialog._add_document(self.card)
        self.card._load_plans.assert_not_called()
        self.assertEqual(self.card.encounters_table.rowCount(), 0)

    def test_edit_meeting_twice_and_reopen_from_database(self):
        self._edit_meeting_twice(link_document=True)

    def test_edit_meeting_with_missing_document_backlink(self):
        self._edit_meeting_twice(link_document=False)

    def _edit_meeting_twice(self, link_document):
        document = models.Document(patient_id=self.patient.id, author_id=self.user.id,
                                   doc_type=models.DOCUMENT_TYPE_MEETING)
        document.save()
        encounter = models.Encounter(patient_id=self.patient.id, doctor_id=self.user.id,
                                     document_id=document.id)
        encounter.save()
        if link_document:
            document.encounter_id = encounter.id
            document.save()
        for text in ('first edit', 'second edit'):
            current = models.Document.get_by_id(document.id).encounter
            dialog = EncounterEditDialog(self.user, self.patient, current)
            dialog.meeting_result_combo.setCurrentIndex(1)
            dialog.status_combo.setCurrentIndex(1)
            dialog.patient_info_input.setPlainText(text)
            dialog.meeting_description_input.setPlainText(text)
            dialog.patient_tasks_input.setPlainText(text)
            dialog.general_measures_input.setPlainText(text)
            dialog.information_relevance_input.setText(text)
            dialog.information_importance_input.setText(text)
            for name in ('timeliness', 'completeness', 'novelty', 'reliability'):
                getattr(dialog, f'information_{name}_combo').setCurrentIndex(1)
            dialog.informants = [models.EncounterInformant(full_name=text)]
            expected_result = dialog.meeting_result_combo.currentData()
            expected_status = dialog.status_combo.currentData()
            with patch('ui.encounter_edit_form.QMessageBox.information'), patch(
                'ui.encounter_edit_form.QMessageBox.exec', return_value=0
            ) as error:
                dialog._save()
            error.assert_not_called()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
            models.db._connection.close()
            models.db._connection = None
            saved_document = models.Document.get_by_id(document.id)
            self.assertEqual(saved_document.encounter_id, encounter.id)
            saved = saved_document.encounter
            self.assertEqual(saved.meeting_result, expected_result)
            self.assertEqual(saved.status, expected_status)
            for field in ('patient_info', 'meeting_description', 'patient_tasks',
                          'general_measures', 'information_relevance', 'information_importance'):
                self.assertEqual(getattr(saved, field), text, field)
            for name in ('timeliness', 'completeness', 'novelty', 'reliability'):
                self.assertEqual(getattr(saved, f'information_{name}'),
                                 getattr(dialog, f'information_{name}_combo').currentData())
            self.assertIn(text, [i.full_name for i in models.EncounterInformant.get_by_encounter(saved.id)])
            self.card._load_encounters()
            self.assertEqual(self.card.encounters_table.item(0, 6).text(), text)
            self.assertEqual(len(models.Encounter.get_by_patient(self.patient.id)), 1)


if __name__ == '__main__':
    unittest.main()
