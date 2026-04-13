"""
Модели данных для LUX
Аналогично Django-моделям из CRM_Hospital
"""

import sqlite3
import hashlib
import os
from datetime import datetime, date
from typing import Optional, List, Any
from dataclasses import dataclass


# ============================================================================
# КОНСТАНТЫ
# ============================================================================

DEPARTMENTS = [
    ("cardiology", "Кардиология"),
    ("therapy", "Терапия"),
    ("psychiatry", "Психиатрия"),
    ("neurology", "Неврология"),
]

PATIENT_TYPE_CHOICES = [
    ("adult", "Взрослый"),
    ("child", "Детский"),
    ("undefined", "Неопределённый"),
]

GENDER_CHOICES = [
    ("M", "Мужской"),
    ("F", "Женский"),
]

FACILITY_TYPES = [
    ("hospital", "Больница"),
    ("sanatorium", "Санаторий"),
    ("daycare", "Дневной стационар"),
]

EVENT_TYPES = [
    ("meeting", "Совещание"),
    ("training", "Обучение"),
    ("inspection", "Проверка"),
    ("report", "Отчёт"),
    ("other", "Другое"),
]

INTERACTION_ACTIONS = [
    ("visit_created", "Создан визит"),
    ("visit_closed", "Закрыт визит"),
    ("note_add", "Добавлена заметка"),
    ("rx_add", "Назначение лекарства"),
    ("patient_update", "Обновлена информация о пациенте"),
    ("facility_update", "Обновлена информация о месте размещения"),
    ("plan_item_add", "Добавлен пункт плана"),
    ("plan_item_delete", "Удалён пункт плана"),
    ("plan_item_toggle", "Изменён статус пункта плана"),
]

DOCUMENT_CLASSIFICATION_CHOICES = [
    ("NS", "НС"),
    ("DSP", "ДСП"),
    ("S", "С"),
    ("SS", "СС"),
]


# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================


class Database:
    _instance = None
    _connection = None

    def __new__(cls, db_path: str = "medcrm.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
        return cls._instance

    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._create_tables()
        return self._connection

    def _create_tables(self):
        cursor = self._connection.cursor()

        # Таблица пользователей
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT,
                middle_name TEXT DEFAULT '',
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'REG',
                department TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Таблица мест размещения
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                address TEXT
            )
        """
        )

        # Таблица пациентов
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                callsign TEXT NOT NULL,
                personal_number TEXT,
                birth_date DATE NOT NULL,
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
                address TEXT,
                emergency_contact TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES users(id),
                FOREIGN KEY (facility_id) REFERENCES facilities(id)
            )
        """
        )

        # Таблица визитов (Encounters)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS encounters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP,
                reason TEXT,
                status TEXT DEFAULT 'PLANNED',
                treatment_plan_item_id INTEGER,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES users(id)
            )
        """
        )

        # Таблица заметок
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encounter_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                text TEXT NOT NULL,
                FOREIGN KEY (encounter_id) REFERENCES encounters(id),
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        """
        )

        # Таблица диагнозов
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnoses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encounter_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (encounter_id) REFERENCES encounters(id)
            )
        """
        )

        # Таблица назначений
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encounter_id INTEGER NOT NULL,
                medication TEXT NOT NULL,
                dosage TEXT NOT NULL,
                frequency TEXT NOT NULL,
                duration_days INTEGER DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (encounter_id) REFERENCES encounters(id)
            )
        """
        )

        # Таблица вложений
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encounter_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                title TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (encounter_id) REFERENCES encounters(id)
            )
        """
        )

        # Таблица пунктов плана лечения
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS treatment_plan_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                order_num INTEGER DEFAULT 1,
                event TEXT NOT NULL,
                due_date DATE,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """
        )

        # Таблица взаимодействий
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patient_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                user_id INTEGER,
                action TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # Таблица мероприятий
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_type TEXT DEFAULT 'other',
                event_date DATE NOT NULL,
                event_time TIME,
                department TEXT,
                responsible_id INTEGER,
                is_completed BOOLEAN DEFAULT 0,
                year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_id INTEGER,
                FOREIGN KEY (responsible_id) REFERENCES users(id),
                FOREIGN KEY (created_by_id) REFERENCES users(id)
            )
        """
        )

        # Миграция: добавляем колонку year, если её нет
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN year INTEGER")
        except Exception:
            pass  # Колонка уже существует

        # Заполняем year из event_date для старых записей
        cursor.execute(
            """
            UPDATE events SET year = CAST(strftime('%Y', event_date) AS INTEGER)
            WHERE year IS NULL
        """
        )

        # Миграция пациентов: замена first_name/last_name/middle_name на callsign/personal_number
        try:
            cursor.execute("SELECT first_name FROM patients LIMIT 1")
            # Создаём временную таблицу с новой структурой
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS patients_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    callsign TEXT NOT NULL DEFAULT '',
                    personal_number TEXT,
                    birth_date DATE NOT NULL,
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
                    address TEXT,
                    emergency_contact TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES users(id),
                    FOREIGN KEY (facility_id) REFERENCES facilities(id)
                )
                """
            )
            # Копируем данные, объединяя ФИО в callsign
            cursor.execute(
                """
                INSERT OR IGNORE INTO patients_new
                (id, callsign, personal_number, birth_date, gender, patient_type,
                 department, doctor_id, facility_id, phone, email, document_id,
                 insurance_number, employer, address, emergency_contact, is_active, created_at)
                SELECT
                    id,
                    COALESCE(NULLIF(last_name, '') || ' ' || NULLIF(first_name, '') || ' ' || COALESCE(NULLIF(middle_name, ''), ''), 'Пациент') as callsign,
                    NULL as personal_number,
                    birth_date, gender, patient_type,
                    department, doctor_id, facility_id, phone, email, document_id,
                    insurance_number, employer, address, emergency_contact, is_active, created_at
                FROM patients
                """
            )
            cursor.execute("DROP TABLE patients")
            cursor.execute("ALTER TABLE patients_new RENAME TO patients")
        except Exception:
            pass  # Миграция уже выполнена или таблица ещё пуста

        # Миграция: добавление новых полей для документов пациента
        new_columns = [
            ("study_case_number", "TEXT DEFAULT ''"),
            ("study_sheet_numbers", "TEXT DEFAULT ''"),
            ("admission_report_number", "TEXT DEFAULT ''"),
            ("admission_report_date", "DATE"),
            ("admission_sanction_date", "DATE"),
            ("arrival_report_number", "TEXT DEFAULT ''"),
            ("arrival_report_date", "DATE"),
            ("arrival_sanction_date", "DATE"),
        ]

        for col_name, col_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE patients ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass  # Колонка уже существует

        # Таблица документов
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                classification TEXT NOT NULL DEFAULT 'NS',
                doc_date DATE NOT NULL,
                author_id INTEGER NOT NULL,
                doc_type TEXT NOT NULL,
                summary TEXT,
                location TEXT,
                patient_personal_number TEXT,
                doc_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        """
        )

        # Миграция: добавление колонки doc_number
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN doc_number TEXT")
        except Exception:
            pass  # Колонка уже существует

        # Таблица кэша статистики
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stats_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT '',
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(metric, department, month, year)
            )
        """
        )

        self._connection.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        if self._connection:
            self._connection.commit()

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def lastrowid(self) -> int:
        if self._connection:
            return self._connection.cursor().lastrowid
        return 0


# Глобальный экземпляр БД
db = Database()


# ============================================================================
# УТИЛИТЫ
# ============================================================================


def hash_password(password: str) -> str:
    """Хеширование пароля с солью"""
    salt = os.urandom(16).hex()
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()
    return f"{salt}${password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Проверка пароля"""
    try:
        salt, stored_hash = password_hash.split("$")
        new_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        ).hex()
        return new_hash == stored_hash
    except:
        return False


def calculate_age(birth_date: date) -> int:
    """Расчёт возраста в полных годах"""
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def is_child(birth_date: date) -> bool:
    """Проверка, является ли пациент несовершеннолетним"""
    return calculate_age(birth_date) < 18


# ============================================================================
# МОДЕЛИ
# ============================================================================


@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    middle_name: str = ""
    email: str = ""
    password_hash: str = ""
    role: str = "REG"
    department: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    # Роли
    ROLE_ADMIN = "ADMIN"
    ROLE_REGISTRAR = "REG"
    ROLE_LEAD = "LEAD"
    ROLE_DOCTOR = "DOC"
    ROLE_NURSE = "NUR"
    ROLE_PHARMACIST = "PHARM"
    ROLE_LAB = "LAB"

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p).strip()

    @property
    def role_display(self) -> str:
        roles = {
            self.ROLE_ADMIN: "Администратор",
            self.ROLE_REGISTRAR: "Регистратор",
            self.ROLE_LEAD: "Начальник отделения",
            self.ROLE_DOCTOR: "Врач",
            self.ROLE_NURSE: "Медсестра",
            self.ROLE_PHARMACIST: "Провизор",
            self.ROLE_LAB: "Лаборант",
        }
        return roles.get(self.role, self.role)

    @property
    def department_display(self) -> str:
        if not self.department:
            return ""
        dept_dict = dict(DEPARTMENTS)
        return dept_dict.get(self.department, self.department)

    def is_clinician(self) -> bool:
        return self.role in (self.ROLE_DOCTOR, self.ROLE_NURSE)

    def save(self):
        """Сохранение пользователя в БД"""
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO users
            (id, username, first_name, last_name, middle_name, email, password_hash, role, department, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.username,
                self.first_name,
                self.last_name,
                self.middle_name,
                self.email,
                self.password_hash,
                self.role,
                self.department,
                self.is_active,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Получение пользователя по логину"""
        row = db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Получение пользователя по ID"""
        row = db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        if row:
            return cls(**dict(row))
        return None

    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List["User"]:
        """Получение всех пользователей"""
        query = "SELECT * FROM users"
        if not include_inactive:
            query += " WHERE is_active = 1"
        query += " ORDER BY last_name, first_name"
        rows = db.fetchall(query)
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_role(cls, role: str) -> List["User"]:
        """Получение пользователей по роли"""
        rows = db.fetchall(
            "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY last_name",
            (role,),
        )
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_doctors_by_department(cls, department: str) -> List["User"]:
        """Получение врачей по отделению"""
        rows = db.fetchall(
            "SELECT * FROM users WHERE role = 'DOC' AND department = ? AND is_active = 1 ORDER BY last_name",
            (department,),
        )
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional["User"]:
        """Аутентификация пользователя"""
        user = cls.get_by_username(username)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    def delete(self):
        """Удаление пользователя"""
        if self.id:
            db.execute("DELETE FROM users WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Facility:
    id: Optional[int] = None
    name: str = ""
    type: str = "hospital"
    address: str = ""

    @property
    def type_display(self) -> str:
        type_dict = dict(FACILITY_TYPES)
        return type_dict.get(self.type, self.type)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO facilities (id, name, type, address)
            VALUES (?, ?, ?, ?)
        """,
            (self.id, self.name, self.type, self.address),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_all(cls) -> List["Facility"]:
        rows = db.fetchall("SELECT * FROM facilities ORDER BY name")
        return [cls(**dict(row)) for row in rows]

    @classmethod
    def get_by_id(cls, facility_id: int) -> Optional["Facility"]:
        row = db.fetchone("SELECT * FROM facilities WHERE id = ?", (facility_id,))
        if row:
            return cls(**dict(row))
        return None

    def delete(self):
        if self.id:
            db.execute("DELETE FROM facilities WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Patient:
    id: Optional[int] = None
    callsign: str = ""
    personal_number: str = ""
    birth_date: date = None
    gender: str = "M"
    patient_type: str = "adult"
    department: str = "therapy"
    doctor_id: Optional[int] = None
    facility_id: Optional[int] = None
    phone: str = ""
    email: str = ""
    document_id: str = ""
    insurance_number: str = ""
    employer: str = ""
    address: str = ""
    emergency_contact: str = ""
    # Справка об изучении
    study_case_number: str = ""
    study_sheet_numbers: str = ""
    # Рапорт на поступление
    admission_report_number: str = ""
    admission_report_date: Optional[date] = None
    admission_sanction_date: Optional[date] = None
    # Рапорт о поступлении
    arrival_report_number: str = ""
    arrival_report_date: Optional[date] = None
    arrival_sanction_date: Optional[date] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.birth_date is None:
            self.birth_date = date.today()

    @property
    def full_name(self) -> str:
        """Возвращает позывной как основное имя"""
        return self.callsign

    @property
    def age(self) -> int:
        return calculate_age(self.birth_date)

    @property
    def is_child(self) -> bool:
        return is_child(self.birth_date)

    @property
    def department_display(self) -> str:
        dept_dict = dict(DEPARTMENTS)
        return dept_dict.get(self.department, self.department)

    @property
    def doctor(self) -> Optional[User]:
        if self.doctor_id:
            return User.get_by_id(self.doctor_id)
        return None

    @property
    def facility(self) -> Optional[Facility]:
        if self.facility_id:
            return Facility.get_by_id(self.facility_id)
        return None

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO patients
            (id, callsign, personal_number, birth_date, gender, patient_type,
             department, doctor_id, facility_id, phone, email, document_id, insurance_number,
             employer, address, emergency_contact,
             study_case_number, study_sheet_numbers,
             admission_report_number, admission_report_date, admission_sanction_date,
             arrival_report_number, arrival_report_date, arrival_sanction_date,
             is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.callsign,
                self.personal_number,
                self.birth_date.isoformat(),
                self.gender,
                self.patient_type,
                self.department,
                self.doctor_id,
                self.facility_id,
                self.phone,
                self.email,
                self.document_id,
                self.insurance_number,
                self.employer,
                self.address,
                self.emergency_contact,
                self.study_case_number,
                self.study_sheet_numbers,
                self.admission_report_number,
                (
                    self.admission_report_date.isoformat()
                    if self.admission_report_date
                    else None
                ),
                (
                    self.admission_sanction_date.isoformat()
                    if self.admission_sanction_date
                    else None
                ),
                self.arrival_report_number,
                (
                    self.arrival_report_date.isoformat()
                    if self.arrival_report_date
                    else None
                ),
                (
                    self.arrival_sanction_date.isoformat()
                    if self.arrival_sanction_date
                    else None
                ),
                self.is_active,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def _from_row(cls, row: dict) -> "Patient":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)

        # Конвертация всех полей дат
        date_fields = [
            "birth_date",
            "admission_report_date",
            "admission_sanction_date",
            "arrival_report_date",
            "arrival_sanction_date",
        ]

        for field in date_fields:
            if data.get(field) and isinstance(data[field], str):
                try:
                    data[field] = datetime.strptime(data[field], "%Y-%m-%d").date()
                except ValueError:
                    try:
                        data[field] = datetime.strptime(
                            data[field][:10], "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        data[field] = None

        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_by_id(cls, patient_id: int) -> Optional["Patient"]:
        row = db.fetchone("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if row:
            return cls._from_row(row)
        return None

    @classmethod
    def get_all(
        cls,
        user: Optional[User] = None,
        include_inactive: bool = False,
        search_query: str = "",
        patient_type: str = "",
        facility_id: int = 0,
    ) -> List["Patient"]:
        """Получение пациентов с фильтрацией по ролям"""
        query = "SELECT * FROM patients WHERE 1=1"
        params = []

        # Фильтр по активности
        if not include_inactive:
            query += " AND is_active = 1"

        # Тип пациента
        if patient_type:
            query += " AND patient_type = ?"
            params.append(patient_type)

        # Место размещения
        if facility_id:
            query += " AND facility_id = ?"
            params.append(facility_id)

        # Ограничение по ролям
        if user:
            if user.role == User.ROLE_LEAD:
                query += " AND department = ?"
                params.append(user.department)
            elif user.role == User.ROLE_DOCTOR:
                query += " AND doctor_id = ?"
                params.append(user.id)
            elif user.role == User.ROLE_NURSE:
                query += " AND department = ?"
                params.append(user.department)

        query += " ORDER BY callsign"
        rows = db.fetchall(query, tuple(params))
        return [cls._from_row(row) for row in rows]

    def delete(self):
        """Мягкое удаление (скрытие)"""
        if self.id:
            db.execute("UPDATE patients SET is_active = 0 WHERE id = ?", (self.id,))
            db.commit()

    def restore(self):
        """Восстановление"""
        if self.id:
            db.execute("UPDATE patients SET is_active = 1 WHERE id = ?", (self.id,))
            db.commit()

    def hard_delete(self):
        """Полное удаление"""
        if self.id:
            db.execute("DELETE FROM patients WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Encounter:
    id: Optional[int] = None
    patient_id: int = 0
    doctor_id: int = 0
    started_at: datetime = None
    finished_at: Optional[datetime] = None
    reason: str = ""
    status: str = "PLANNED"
    treatment_plan_item_id: Optional[int] = None

    STATUS_PLANNED = "PLANNED"
    STATUS_INPROGRESS = "INPROGRESS"
    STATUS_FINISHED = "FINISHED"

    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()

    @property
    def status_display(self) -> str:
        statuses = {
            self.STATUS_PLANNED: "Запланирован",
            self.STATUS_INPROGRESS: "В процессе",
            self.STATUS_FINISHED: "Завершен",
        }
        return statuses.get(self.status, self.status)

    @property
    def doctor(self) -> Optional[User]:
        return User.get_by_id(self.doctor_id)

    @property
    def patient(self) -> Optional[Patient]:
        return Patient.get_by_id(self.patient_id)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO encounters
            (id, patient_id, doctor_id, started_at, finished_at, reason, status, treatment_plan_item_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.patient_id,
                self.doctor_id,
                self.started_at.isoformat() if self.started_at else None,
                self.finished_at.isoformat() if self.finished_at else None,
                self.reason,
                self.status,
                self.treatment_plan_item_id,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def _from_row(cls, row: dict) -> "Encounter":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("started_at") and isinstance(data["started_at"], str):
            # Пробуем разные форматы
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["started_at"] = datetime.strptime(data["started_at"], fmt)
                    break
                except ValueError:
                    continue
        if data.get("finished_at") and isinstance(data["finished_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["finished_at"] = datetime.strptime(data["finished_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_by_patient(cls, patient_id: int) -> List["Encounter"]:
        rows = db.fetchall(
            "SELECT * FROM encounters WHERE patient_id = ? ORDER BY started_at DESC",
            (patient_id,),
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_all(
        cls,
        user: Optional[User] = None,
        include_inactive: bool = False,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> List["Encounter"]:
        """Получение всех визитов с фильтрацией"""
        query = "SELECT * FROM encounters WHERE 1=1"
        params = []

        if not include_inactive:
            query += " AND status != 'CANCELLED'"

        if start_date:
            query += " AND started_at >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND started_at <= ?"
            params.append(end_date.isoformat())

        # Ограничение по ролям
        if user:
            if user.role == User.ROLE_LEAD:
                # Начальник отделения видит все визиты своего отделения
                query += """ AND patient_id IN (
                    SELECT id FROM patients WHERE department = ?
                )"""
                params.append(user.department)
            elif user.role == User.ROLE_DOCTOR:
                # Врач видит только свои визиты
                query += " AND doctor_id = ?"
                params.append(user.id)
            elif user.role == User.ROLE_NURSE:
                # Медсестра видит визиты своего отделения
                query += """ AND patient_id IN (
                    SELECT id FROM patients WHERE department = ?
                )"""
                params.append(user.department)

        query += " ORDER BY started_at DESC"
        rows = db.fetchall(query, tuple(params))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, encounter_id: int) -> Optional["Encounter"]:
        row = db.fetchone("SELECT * FROM encounters WHERE id = ?", (encounter_id,))
        if row:
            return cls._from_row(row)
        return None

    def close(self):
        """Закрытие визита"""
        self.finished_at = datetime.now()
        self.status = self.STATUS_FINISHED
        self.save()

    def delete(self):
        if self.id:
            db.execute("DELETE FROM encounters WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Note:
    id: Optional[int] = None
    encounter_id: int = 0
    author_id: int = 0
    text: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def author(self) -> Optional[User]:
        return User.get_by_id(self.author_id)

    @property
    def encounter(self) -> Optional[Encounter]:
        return Encounter.get_by_id(self.encounter_id)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO notes (id, encounter_id, author_id, text, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.encounter_id,
                self.author_id,
                self.text,
                self.created_at.isoformat() if self.created_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def _from_row(cls, row: dict) -> "Note":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_by_encounter(cls, encounter_id: int) -> List["Note"]:
        rows = db.fetchall(
            "SELECT * FROM notes WHERE encounter_id = ? ORDER BY created_at DESC",
            (encounter_id,),
        )
        return [cls._from_row(row) for row in rows]

    def delete(self):
        if self.id:
            db.execute("DELETE FROM notes WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Diagnosis:
    id: Optional[int] = None
    encounter_id: int = 0
    code: str = ""
    description: str = ""

    @property
    def encounter(self) -> Optional[Encounter]:
        return Encounter.get_by_id(self.encounter_id)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO diagnoses (id, encounter_id, code, description)
            VALUES (?, ?, ?, ?)
        """,
            (self.id, self.encounter_id, self.code, self.description),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_by_encounter(cls, encounter_id: int) -> List["Diagnosis"]:
        rows = db.fetchall(
            "SELECT * FROM diagnoses WHERE encounter_id = ? ORDER BY id",
            (encounter_id,),
        )
        return [cls(**dict(row)) for row in rows]

    def delete(self):
        if self.id:
            db.execute("DELETE FROM diagnoses WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Prescription:
    id: Optional[int] = None
    encounter_id: int = 0
    medication: str = ""
    dosage: str = ""
    frequency: str = ""
    duration_days: int = 1
    notes: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def encounter(self) -> Optional[Encounter]:
        return Encounter.get_by_id(self.encounter_id)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO prescriptions 
            (id, encounter_id, medication, dosage, frequency, duration_days, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.encounter_id,
                self.medication,
                self.dosage,
                self.frequency,
                self.duration_days,
                self.notes,
                self.created_at.isoformat() if self.created_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_by_encounter(cls, encounter_id: int) -> List["Prescription"]:
        rows = db.fetchall(
            "SELECT * FROM prescriptions WHERE encounter_id = ? ORDER BY created_at DESC",
            (encounter_id,),
        )
        return [cls(**dict(row)) for row in rows]

    def delete(self):
        if self.id:
            db.execute("DELETE FROM prescriptions WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class Attachment:
    id: Optional[int] = None
    encounter_id: int = 0
    file_path: str = ""
    title: str = ""
    uploaded_at: Optional[datetime] = None

    def __post_init__(self):
        if self.uploaded_at is None:
            self.uploaded_at = datetime.now()

    @property
    def encounter(self) -> Optional[Encounter]:
        return Encounter.get_by_id(self.encounter_id)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO attachments (id, encounter_id, file_path, title, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.encounter_id,
                self.file_path,
                self.title,
                self.uploaded_at.isoformat() if self.uploaded_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_by_encounter(cls, encounter_id: int) -> List["Attachment"]:
        rows = db.fetchall(
            "SELECT * FROM attachments WHERE encounter_id = ? ORDER BY uploaded_at DESC",
            (encounter_id,),
        )
        return [cls(**dict(row)) for row in rows]

    def delete(self):
        if self.id:
            db.execute("DELETE FROM attachments WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class TreatmentPlanItem:
    id: Optional[int] = None
    patient_id: int = 0
    order_num: int = 1
    event: str = ""
    due_date: Optional[date] = None
    is_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def patient(self) -> Optional[Patient]:
        return Patient.get_by_id(self.patient_id)

    def save(self):
        self.updated_at = datetime.now()
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO treatment_plan_items 
            (id, patient_id, order_num, event, due_date, is_completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.patient_id,
                self.order_num,
                self.event,
                self.due_date.isoformat() if self.due_date else None,
                self.is_completed,
                self.created_at.isoformat() if self.created_at else None,
                self.updated_at.isoformat() if self.updated_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def _from_row(cls, row: dict) -> "TreatmentPlanItem":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("due_date") and isinstance(data["due_date"], str):
            try:
                data["due_date"] = datetime.strptime(
                    data["due_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                data["due_date"] = datetime.strptime(
                    data["due_date"][:10], "%Y-%m-%d"
                ).date()
        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        if data.get("updated_at") and isinstance(data["updated_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["updated_at"] = datetime.strptime(data["updated_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_by_patient(cls, patient_id: int) -> List["TreatmentPlanItem"]:
        rows = db.fetchall(
            "SELECT * FROM treatment_plan_items WHERE patient_id = ? ORDER BY order_num, created_at",
            (patient_id,),
        )
        return [cls._from_row(row) for row in rows]

    def toggle(self):
        """Переключение статуса выполнения"""
        self.is_completed = not self.is_completed
        self.save()

    def delete(self):
        if self.id:
            db.execute("DELETE FROM treatment_plan_items WHERE id = ?", (self.id,))
            db.commit()


@dataclass
class PatientInteraction:
    id: Optional[int] = None
    patient_id: int = 0
    user_id: Optional[int] = None
    action: str = ""
    description: str = ""
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def patient(self) -> Optional[Patient]:
        return Patient.get_by_id(self.patient_id)

    @property
    def user(self) -> Optional[User]:
        return User.get_by_id(self.user_id) if self.user_id else None

    @property
    def action_display(self) -> str:
        action_dict = dict(INTERACTION_ACTIONS)
        return action_dict.get(self.action, self.action)

    def save(self):
        cursor = db.execute(
            """
            INSERT INTO patient_interactions (patient_id, user_id, action, description, created_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                self.patient_id,
                self.user_id,
                self.action,
                self.description,
                self.created_at.isoformat() if self.created_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def get_by_patient(cls, patient_id: int) -> List["PatientInteraction"]:
        rows = db.fetchall(
            "SELECT * FROM patient_interactions WHERE patient_id = ? ORDER BY created_at DESC LIMIT 50",
            (patient_id,),
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row: dict) -> "PatientInteraction":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)


@dataclass
class Document:
    id: Optional[int] = None
    patient_id: int = 0
    classification: str = "NS"
    doc_date: Optional[date] = None
    author_id: int = 0
    doc_type: str = ""
    summary: str = ""
    location: str = ""
    patient_personal_number: str = ""
    doc_number: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.doc_date is None:
            self.doc_date = date.today()
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def patient(self) -> Optional[Patient]:
        return Patient.get_by_id(self.patient_id)

    @property
    def author(self) -> Optional[User]:
        return User.get_by_id(self.author_id)

    @property
    def classification_display(self) -> str:
        class_dict = dict(DOCUMENT_CLASSIFICATION_CHOICES)
        return class_dict.get(self.classification, self.classification)

    def save(self):
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO documents
            (id, patient_id, classification, doc_date, author_id, doc_type, summary, location, patient_personal_number, doc_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.patient_id,
                self.classification,
                self.doc_date.isoformat() if self.doc_date else None,
                self.author_id,
                self.doc_type,
                self.summary,
                self.location,
                self.patient_personal_number,
                self.doc_number,
                self.created_at.isoformat() if self.created_at else None,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    def delete(self):
        db.execute("DELETE FROM documents WHERE id = ?", (self.id,))
        db.commit()

    @classmethod
    def _from_row(cls, row: dict) -> "Document":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("doc_date") and isinstance(data["doc_date"], str):
            try:
                data["doc_date"] = datetime.strptime(
                    data["doc_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                data["doc_date"] = datetime.strptime(
                    data["doc_date"][:10], "%Y-%m-%d"
                ).date()
        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_by_patient(cls, patient_id: int) -> List["Document"]:
        """Получение всех документов пациента"""
        rows = db.fetchall(
            "SELECT * FROM documents WHERE patient_id = ? ORDER BY doc_date DESC",
            (patient_id,),
        )
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, doc_id: int) -> Optional["Document"]:
        """Получение документа по ID"""
        row = db.fetchone("SELECT * FROM documents WHERE id = ?", (doc_id,))
        if row:
            return cls._from_row(row)
        return None


@dataclass
class Event:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    event_type: str = "other"
    event_date: date = None
    event_time: Optional[datetime] = None
    department: str = ""
    responsible_id: Optional[int] = None
    is_completed: bool = False
    year: int = 0
    created_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    def __post_init__(self):
        if self.event_date is None:
            self.event_date = date.today()
        if self.year == 0 or self.year is None:
            self.year = self.event_date.year
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def event_type_display(self) -> str:
        type_dict = dict(EVENT_TYPES)
        return type_dict.get(self.event_type, self.event_type)

    @property
    def department_display(self) -> str:
        if not self.department:
            return "Общее"
        dept_dict = dict(DEPARTMENTS)
        return dept_dict.get(self.department, self.department)

    @property
    def responsible(self) -> Optional[User]:
        return User.get_by_id(self.responsible_id) if self.responsible_id else None

    @property
    def created_by(self) -> Optional[User]:
        return User.get_by_id(self.created_by_id) if self.created_by_id else None

    def save(self, user: Optional[User] = None):
        if user and self.created_by_id is None:
            self.created_by_id = user.id
        cursor = db.execute(
            """
            INSERT OR REPLACE INTO events
            (id, title, description, event_type, event_date, event_time, department,
             responsible_id, is_completed, year, created_by_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.id,
                self.title,
                self.description,
                self.event_type,
                self.event_date.isoformat() if self.event_date else None,
                self.event_time.isoformat() if self.event_time else None,
                self.department,
                self.responsible_id,
                self.is_completed,
                self.year,
                self.created_by_id,
            ),
        )
        db.commit()
        if self.id is None:
            self.id = db.lastrowid()

    @classmethod
    def _from_row(cls, row: dict) -> "Event":
        """Создание объекта из строки БД с конвертацией дат"""
        data = dict(row)
        if data.get("event_date") and isinstance(data["event_date"], str):
            try:
                data["event_date"] = datetime.strptime(
                    data["event_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                data["event_date"] = datetime.strptime(
                    data["event_date"][:10], "%Y-%m-%d"
                ).date()
        if data.get("event_time") and isinstance(data["event_time"], str):
            for fmt in ["%H:%M:%S.%f", "%H:%M:%S"]:
                try:
                    data["event_time"] = datetime.strptime(
                        data["event_time"], fmt
                    ).time()
                    break
                except ValueError:
                    continue
        if data.get("created_at") and isinstance(data["created_at"], str):
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
            ]:
                try:
                    data["created_at"] = datetime.strptime(data["created_at"], fmt)
                    break
                except ValueError:
                    continue
        return cls(**data)

    @classmethod
    def get_all(
        cls,
        user: Optional[User] = None,
        department: str = "",
        include_completed: bool = True,
        year: int = 0,
    ) -> List["Event"]:
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if year:
            query += " AND year = ?"
            params.append(year)

        if not include_completed:
            query += " AND is_completed = 0"

        if department:
            query += " AND (department = ? OR department = '' OR department IS NULL)"
            params.append(department)

        # Ограничение по ролям
        if user and user.role not in (User.ROLE_ADMIN, User.ROLE_REGISTRAR):
            if user.role == User.ROLE_LEAD:
                query += " AND (department = ? OR department = '' OR department IS NULL OR created_by_id = ?)"
                params.extend([user.department, user.id])
            elif user.role in (User.ROLE_DOCTOR, User.ROLE_NURSE):
                query += " AND (department = ? OR department = '' OR department IS NULL OR created_by_id = ?)"
                params.extend([user.department, user.id])

        query += " ORDER BY event_date, event_time"
        rows = db.fetchall(query, tuple(params))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, event_id: int) -> Optional["Event"]:
        row = db.fetchone("SELECT * FROM events WHERE id = ?", (event_id,))
        if row:
            return cls._from_row(row)
        return None

    def toggle(self):
        """Переключение статуса выполнения"""
        self.is_completed = not self.is_completed
        self.save()

    def delete(self):
        if self.id:
            db.execute("DELETE FROM events WHERE id = ?", (self.id,))
            db.commit()


# ============================================================================
# КЭШ СТАТИСТИКИ
# ============================================================================


class StatsCache:
    """Кэш для хранения агрегированной статистики"""

    @staticmethod
    def _key(metric: str, department: str, month: int, year: int) -> tuple:
        return (metric, department or "", month, year)

    @classmethod
    def get(cls, metric: str, department: str, month: int, year: int) -> int | None:
        """Получение значения из кэша"""
        row = db.fetchone(
            "SELECT value FROM stats_cache WHERE metric = ? AND department = ? AND month = ? AND year = ?",
            (metric, department or "", month, year),
        )
        return row["value"] if row else None

    @classmethod
    def set(cls, metric: str, department: str, month: int, year: int, value: int):
        """Сохранение значения в кэш"""
        db.execute(
            """INSERT INTO stats_cache (metric, department, month, year, value, updated_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(metric, department, month, year)
               DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP""",
            (metric, department or "", month, year, value, value),
        )
        db.commit()

    @classmethod
    def get_all(cls, department: str, month: int, year: int) -> dict:
        """Получение всей статистики для отделения/месяца"""
        rows = db.fetchall(
            "SELECT metric, value FROM stats_cache WHERE department = ? AND month = ? AND year = ?",
            (department or "", month, year),
        )
        return {row["metric"]: row["value"] for row in rows}

    @classmethod
    def rebuild(cls, department: str = "", month: int = None, year: int = None):
        """Пересчёт кэша для указанных параметров"""
        from datetime import datetime

        current_month = month or datetime.now().month
        current_year = year or datetime.now().year

        # Период для запроса
        from_date = datetime(current_year, current_month, 1)
        if current_month == 12:
            to_date = datetime(current_year + 1, 1, 1)
        else:
            to_date = datetime(current_year, current_month + 1, 1)

        # Получаем пациентов
        all_patients = Patient.get_all(user=None)

        # Фильтруем по отделению если нужно
        if department:
            dept_patients = [p for p in all_patients if p.department == department]
        else:
            dept_patients = all_patients

        # Метрики
        metrics = {
            "patients_total": len(dept_patients),
            "patients_adult": len(
                [p for p in dept_patients if p.patient_type == "adult"]
            ),
            "patients_child": len(
                [p for p in dept_patients if p.patient_type == "child"]
            ),
            "patients_undefined": len(
                [p for p in dept_patients if p.patient_type == "undefined"]
            ),
        }

        # Визиты за месяц
        visits = Encounter.get_all(
            user=None,
            start_date=from_date,
            end_date=to_date,
        )
        if department:
            dept_patient_ids = {p.id for p in dept_patients}
            visits = [v for v in visits if v.patient_id in dept_patient_ids]
        metrics["visits"] = len(visits)

        # Сохраняем в кэш
        for metric, value in metrics.items():
            cls.set(metric, department, current_month, current_year, value)

        return metrics

    @classmethod
    def rebuild_all(cls):
        """Пересчёт кэша для всех отделений"""
        # Обновляем для всех без фильтра (пустое department)
        cls.rebuild(department="", month=None, year=None)

        # Обновляем для каждого отделения
        for dept_code, _ in DEPARTMENTS:
            cls.rebuild(department=dept_code, month=None, year=None)


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================================


def init_db(db_path: str = "medcrm.db"):
    """Инициализация БД и создание тестовых данных"""
    global db
    db = Database(db_path)
    db.connect()

    # Проверка наличия пользователей
    users_count = db.fetchone("SELECT COUNT(*) as cnt FROM users")["cnt"]
    if users_count == 0:
        create_test_data()


def create_test_data():
    """Создание тестовых данных"""

    # Создаём пользователей
    users_data = [
        (
            "admin",
            "Админ",
            "Админов",
            "admin@hospital.ru",
            User.ROLE_ADMIN,
            None,
            "admin123",
        ),
        (
            "reg1",
            "Регистратор",
            "Регистраторов",
            "reg@hospital.ru",
            User.ROLE_REGISTRAR,
            None,
            "reg123",
        ),
        (
            "lead1",
            "Начальник",
            "Отделенков",
            "lead@hospital.ru",
            User.ROLE_LEAD,
            "cardiology",
            "lead123",
        ),
        (
            "doc1",
            "Доктор",
            "Врачев",
            "doc@hospital.ru",
            User.ROLE_DOCTOR,
            "cardiology",
            "doc123",
        ),
        (
            "doc2",
            "Иван",
            "Петров",
            "doc2@hospital.ru",
            User.ROLE_DOCTOR,
            "therapy",
            "doc123",
        ),
        (
            "nur1",
            "Медсестра",
            "Сестринкина",
            "nur@hospital.ru",
            User.ROLE_NURSE,
            "cardiology",
            "nur123",
        ),
        (
            "nur2",
            "Анна",
            "Иванова",
            "nur2@hospital.ru",
            User.ROLE_NURSE,
            "therapy",
            "nur123",
        ),
    ]

    for username, first_name, last_name, email, role, dept, password in users_data:
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            department=dept,
            password_hash=hash_password(password),
            is_active=True,
        )
        user.save()

    # Создаём места размещения
    facilities_data = [
        ("Городская больница №1", "hospital", "ул. Ленина, 1"),
        ("Областной госпиталь", "hospital", "пр. Мира, 10"),
        ("Санаторий 'Здоровье'", "sanatorium", "пос. Лесной"),
        ("Дневной стационар", "daycare", "ул. Больничная, 5"),
    ]

    for name, ftype, address in facilities_data:
        facility = Facility(name=name, type=ftype, address=address)
        facility.save()

    # Создаём тестовых пациентов
    patients_data = [
        (
            "Иван",
            "Иванов",
            "Иванович",
            "1980-05-15",
            "M",
            "adult",
            "cardiology",
            3,
            1,
            "+79001234567",
        ),
        (
            "Петр",
            "Петров",
            "Петрович",
            "1975-08-20",
            "M",
            "adult",
            "cardiology",
            3,
            1,
            "+79001234568",
        ),
        (
            "Анна",
            "Сидорова",
            "Анновна",
            "1990-03-10",
            "F",
            "adult",
            "therapy",
            4,
            2,
            "+79001234569",
        ),
        (
            "Мария",
            "Смирнова",
            "",
            "2015-12-01",
            "F",
            "child",
            "cardiology",
            3,
            None,
            "+79001234570",
        ),
        (
            "Алексей",
            "Кузнецов",
            "Алексеевич",
            "1960-01-25",
            "M",
            "adult",
            "neurology",
            None,
            3,
            "+79001234571",
        ),
        (
            "Ольга",
            "Попова",
            "Сергеевна",
            "1985-07-30",
            "F",
            "adult",
            "psychiatry",
            None,
            4,
            "+79001234572",
        ),
    ]

    for fn, ln, mn, bd, gender, ptype, dept, doc_id, fac_id, phone in patients_data:
        patient = Patient(
            first_name=fn,
            last_name=ln,
            middle_name=mn,
            birth_date=datetime.strptime(bd, "%Y-%m-%d").date(),
            gender=gender,
            patient_type=ptype,
            department=dept,
            doctor_id=doc_id,
            facility_id=fac_id,
            phone=phone,
        )
        patient.save()

    # Создаём визиты
    patients = Patient.get_all()
    doctors = User.get_by_role(User.ROLE_DOCTOR)

    if patients and doctors:
        for i, patient in enumerate(patients[:3]):
            doctor = doctors[i % len(doctors)]
            encounter = Encounter(
                patient_id=patient.id,
                doctor_id=doctor.id,
                started_at=datetime.now(),
                reason="Плановый осмотр",
                status=(
                    Encounter.STATUS_INPROGRESS if i == 0 else Encounter.STATUS_FINISHED
                ),
            )
            encounter.save()

            # Добавляем заметку
            if encounter.id:
                note = Note(
                    encounter_id=encounter.id,
                    author_id=doctor.id,
                    text="Жалоб нет. Состояние удовлетворительное.",
                )
                note.save()

                # Добавляем назначение
                if i == 0:
                    rx = Prescription(
                        encounter_id=encounter.id,
                        medication="Аспирин",
                        dosage="100мг",
                        frequency="1 раз в день",
                        duration_days=10,
                        notes="После еды",
                    )
                    rx.save()

    # Создаём пункты плана лечения
    if patients:
        for patient in patients[:2]:
            plan_item = TreatmentPlanItem(
                patient_id=patient.id,
                event="ЭКГ мониторинг",
                due_date=date.today(),
                is_completed=False,
            )
            plan_item.save()

            plan_item2 = TreatmentPlanItem(
                patient_id=patient.id,
                event="Консультация кардиолога",
                due_date=date.today(),
                is_completed=True,
            )
            plan_item2.save()

    # Создаём мероприятия
    events_data = [
        (
            "Совещание отделения",
            "Обсуждение текущих вопросов",
            "meeting",
            "cardiology",
            3,
        ),
        ("Обучение персонала", "Курсы повышения квалификации", "training", None, None),
        (
            "Проверка документации",
            "Ежеквартальная проверка",
            "inspection",
            "therapy",
            4,
        ),
    ]

    admin = User.get_by_username("admin")
    admin_id = admin.id if admin else None

    for title, desc, etype, dept, resp_id in events_data:
        event = Event(
            title=title,
            description=desc,
            event_type=etype,
            event_date=date.today(),
            department=dept,
            responsible_id=resp_id,
            created_by_id=admin_id,
        )
        event.save()
