from datetime import datetime, date
from .extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, index=True)

    doctor = db.relationship("Doctor", backref="user", uselist=False, cascade="all, delete-orphan")
    patient = db.relationship("Patient", backref="user", uselist=False, cascade="all, delete-orphan")


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    doctors = db.relationship("Doctor", backref="department", lazy=True)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
    specialization = db.Column(db.String(100), index=True)
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True)
    availabilities = db.relationship("Availability", backref="doctor", lazy=True, cascade="all, delete-orphan")
    treatments = db.relationship("Treatment", backref="doctor", lazy=True)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    date_of_birth = db.Column(db.Date)
    blood_group = db.Column(db.String(5))
    gender = db.Column(db.String(10))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    insurance_id = db.Column(db.String(100))
    insurance_provider = db.Column(db.String(200))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)

    appointments = db.relationship("Appointment", backref="patient", lazy=True)
    treatments = db.relationship("Treatment", backref="patient", lazy=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    time_slot = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)
    reason = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    treatment = db.relationship("Treatment", backref="appointment", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "time_slot", name="uq_doctor_slot"),
    )


class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    diagnosis = db.Column(db.String(500))
    prescription = db.Column(db.String(500))
    medicines = db.Column(db.String(500))
    visit_type = db.Column(db.String(100))
    notes = db.Column(db.Text)
    visit_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescribed_medicines = db.relationship(
        "TreatmentMedication",
        backref="treatment",
        lazy=True,
        cascade="all, delete-orphan",
    )


class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    generic_name = db.Column(db.String(200), index=True)
    form = db.Column(db.String(80))  # tablet/capsule/syrup/injection...
    strength = db.Column(db.String(80))  # 500mg, 250mg/5ml...
    manufacturer = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "name", "generic_name", "form", "strength", "manufacturer",
            name="uq_medication_identity",
        ),
    )


class TreatmentMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment.id"), nullable=False, index=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False, index=True)

    dose = db.Column(db.String(80))  # 1 tab, 5ml
    frequency = db.Column(db.String(80))  # OD/BID/TID/QID etc
    duration = db.Column(db.String(80))  # 5 days, 2 weeks
    instructions = db.Column(db.String(300))  # after food, bedtime...

    medication = db.relationship("Medication")


class Vital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), nullable=False, unique=True, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False, index=True)

    temperature = db.Column(db.Float)
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    pulse_rate = db.Column(db.Integer)
    spo2 = db.Column(db.Integer)
    respiratory_rate = db.Column(db.Integer)
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    appointment = db.relationship("Appointment")
    patient = db.relationship("Patient")
    doctor = db.relationship("Doctor")


class LabTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True, unique=True)
    description = db.Column(db.Text)
    normal_range = db.Column(db.String(200))
    unit = db.Column(db.String(50))
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LabOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False, index=True)
    lab_test_id = db.Column(db.Integer, db.ForeignKey("lab_test.id"), nullable=False, index=True)

    status = db.Column(db.String(20), default="ordered", index=True)  # ordered/collected/resulted/cancelled
    result_value = db.Column(db.String(200))
    result_notes = db.Column(db.Text)
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resulted_at = db.Column(db.DateTime)

    result_file_provider = db.Column(db.String(20), index=True)  # local|minio|s3
    result_file_key = db.Column(db.String(500))

    appointment = db.relationship("Appointment")
    patient = db.relationship("Patient")
    doctor = db.relationship("Doctor")
    lab_test = db.relationship("LabTest")

    __table_args__ = (
        db.UniqueConstraint("appointment_id", "lab_test_id", name="uq_apt_labtest"),
    )


class LabOrderStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey("lab_order.id"), nullable=False, index=True)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    lab_order = db.relationship("LabOrder")
    changed_by = db.relationship("User")


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), index=True)
    invoice_number = db.Column(db.String(50), unique=True, index=True)

    subtotal = db.Column(db.Float, default=0)
    tax_percent = db.Column(db.Float, default=0)
    tax_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="draft", index=True)  # draft/issued/paid/cancelled
    issued_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")
    appointment = db.relationship("Appointment")
    items = db.relationship("InvoiceItem", backref="invoice", lazy=True, cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False, index=True)
    description = db.Column(db.String(300), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # consultation/medication/lab_test/procedure
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0)
    total_price = db.Column(db.Float, default=0)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), index=True)
    resource_id = db.Column(db.Integer, index=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default="system", index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    link = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")


class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_avail"),
    )


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)  # admin/doctor/patient/...
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)  # ehr.read, ehr.write, ...
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey("permission.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    role = db.relationship("Role")
    permission = db.relationship("Permission")

    __table_args__ = (
        db.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")
    role = db.relationship("Role")

    __table_args__ = (
        db.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )


class UserMfa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)
    totp_secret = db.Column(db.String(64), nullable=False)  # base32 secret
    is_enabled = db.Column(db.Boolean, default=False, index=True)
    enabled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique=True, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    appointment = db.relationship("Appointment")
    patient = db.relationship("Patient")
    doctor = db.relationship("Doctor")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    conversation = db.relationship("Conversation")
    sender = db.relationship("User")


class MessageReadReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    read_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    message = db.relationship("Message")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("message_id", "user_id", name="uq_message_read"),
    )


class PatientVitalReading(db.Model):
    """
    Remote Patient Monitoring (RPM) patient-submitted vitals.
    Separate from clinic/appointment vitals (`Vital`) to preserve legacy workflows.
    """
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    source = db.Column(db.String(30), default="manual", index=True)  # manual|device
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Common vitals
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)
    glucose_mg_dl = db.Column(db.Float)
    spo2 = db.Column(db.Integer)
    temperature_c = db.Column(db.Float)
    weight_kg = db.Column(db.Float)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")


class Encounter(db.Model):
    """
    EHR encounter wrapper. Initially 1:1 with completed Appointment/Treatment.
    """
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), index=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointment.id"), unique=True, index=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment.id"), unique=True, index=True)

    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")
    doctor = db.relationship("Doctor")
    appointment = db.relationship("Appointment")
    treatment = db.relationship("Treatment")


class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    status = db.Column(db.String(30), default="active", index=True)  # active/resolved
    icd10 = db.Column(db.String(20), index=True)
    notes = db.Column(db.Text)
    onset_date = db.Column(db.Date)
    resolved_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")


class Allergy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    substance = db.Column(db.String(200), nullable=False, index=True)
    reaction = db.Column(db.String(200))
    severity = db.Column(db.String(20), index=True)  # mild/moderate/severe
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)

    category = db.Column(db.String(50), default="medical", index=True)  # lab_report, imaging, discharge, ...
    title = db.Column(db.String(200))
    original_filename = db.Column(db.String(300))
    mime_type = db.Column(db.String(100))
    size_bytes = db.Column(db.Integer)

    storage_provider = db.Column(db.String(20), default="local", index=True)  # local|minio|s3
    storage_key = db.Column(db.String(500), nullable=False, index=True)  # object key / local relative path

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")
    uploaded_by = db.relationship("User")


class EhrEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)

    event_type = db.Column(db.String(50), nullable=False, index=True)  # encounter, lab_order, vital, document, ...
    event_ref_id = db.Column(db.Integer, nullable=False, index=True)
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    title = db.Column(db.String(200))
    summary = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient")


class DrugItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False, index=True)
    sku = db.Column(db.String(50), unique=True, index=True)
    reorder_level = db.Column(db.Integer, default=10)
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    medication = db.relationship("Medication")


class StockLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drug_item_id = db.Column(db.Integer, db.ForeignKey("drug_item.id"), nullable=False, index=True)
    batch_number = db.Column(db.String(100), index=True)
    expiry_date = db.Column(db.Date, index=True)
    quantity_on_hand = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Float, default=0)
    received_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    drug_item = db.relationship("DrugItem")


class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_lot_id = db.Column(db.Integer, db.ForeignKey("stock_lot.id"), nullable=False, index=True)
    movement_type = db.Column(db.String(20), nullable=False, index=True)  # in/out/adjust
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200))
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    stock_lot = db.relationship("StockLot")
    actor = db.relationship("User")


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey("treatment.id"), index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor.id"), nullable=False, index=True)
    status = db.Column(db.String(30), default="pending", index=True)  # pending/sent/fulfilled/partial/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    treatment = db.relationship("Treatment")
    patient = db.relationship("Patient")
    doctor = db.relationship("Doctor")
    items = db.relationship("PrescriptionItem", backref="prescription", lazy=True, cascade="all, delete-orphan")


class PrescriptionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey("prescription.id"), nullable=False, index=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False, index=True)
    dose = db.Column(db.String(80))
    frequency = db.Column(db.String(80))
    duration = db.Column(db.String(80))
    instructions = db.Column(db.String(300))
    quantity = db.Column(db.Integer, default=1)

    medication = db.relationship("Medication")


class DispenseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey("prescription.id"), nullable=False, index=True)
    dispensed_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    status = db.Column(db.String(30), default="dispensed", index=True)  # dispensed/returned
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    prescription = db.relationship("Prescription")
    dispensed_by = db.relationship("User")
    items = db.relationship("DispenseItem", backref="dispense_order", lazy=True, cascade="all, delete-orphan")


class DispenseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dispense_order_id = db.Column(db.Integer, db.ForeignKey("dispense_order.id"), nullable=False, index=True)
    stock_lot_id = db.Column(db.Integer, db.ForeignKey("stock_lot.id"), nullable=False, index=True)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False)

    stock_lot = db.relationship("StockLot")
    medication = db.relationship("Medication")
