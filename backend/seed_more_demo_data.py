import random
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from application import create_app
from application.extensions import db
from application.models import (
    User,
    Department,
    Doctor,
    Patient,
    Appointment,
    Treatment,
    Medication,
    TreatmentMedication,
    Vital,
    LabTest,
    LabOrder,
    Invoice,
    InvoiceItem,
    DrugItem,
    StockLot,
    Prescription,
    PrescriptionItem,
    PatientVitalReading,
)


DIAGNOSES = [
    "Stable hypertension",
    "Type 2 diabetes mellitus",
    "Migraine without aura",
    "Dyslipidemia",
    "Acute low back pain",
]


def ensure_departments():
    names = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics"]
    result = {}
    for name in names:
        dept = Department.query.filter_by(name=name).first()
        if not dept:
            dept = Department(name=name)
            db.session.add(dept)
        result[name] = dept
    db.session.flush()
    return result


def ensure_medications():
    """Re-use existing meds; add a few more if missing."""
    catalog = [
        ("Atorvastatin", "Atorvastatin", "tablet", "20mg", "Demo Pharma"),
        ("Aspirin", "Acetylsalicylic Acid", "tablet", "75mg", "Demo Pharma"),
        ("Metformin", "Metformin", "tablet", "500mg", "Demo Pharma"),
        ("Losartan", "Losartan", "tablet", "50mg", "Demo Pharma"),
        ("Sumatriptan", "Sumatriptan", "tablet", "50mg", "Demo Pharma"),
        ("Ibuprofen", "Ibuprofen", "tablet", "400mg", "Demo Pharma"),
    ]
    meds = []
    for name, gen, form, strength, mfg in catalog:
        m = (
            Medication.query.filter_by(
                name=name, generic_name=gen, form=form, strength=strength, manufacturer=mfg
            ).first()
        )
        if not m:
            m = Medication(
                name=name,
                generic_name=gen,
                form=form,
                strength=strength,
                manufacturer=mfg,
            )
            db.session.add(m)
        meds.append(m)
    db.session.flush()

    # Ensure basic inventory exists for each medication
    for m in meds:
        di = DrugItem.query.filter_by(medication_id=m.id).first()
        if not di:
            di = DrugItem(medication_id=m.id, sku=f"SKU-{m.id}", reorder_level=10)
            db.session.add(di)
            db.session.flush()
            lot = StockLot(
                drug_item_id=di.id,
                batch_number=f"BATCH-{di.id}",
                expiry_date=date.today() + timedelta(days=365),
                quantity_on_hand=100,
                unit_cost=5.0,
            )
            db.session.add(lot)
    db.session.flush()
    return meds


def ensure_lab_tests():
    tests = [
        ("CBC", "Hematology", "", "", "Complete blood count"),
        ("Fasting Blood Sugar", "Biochemistry", "mg/dL", "70-100", "Glucose level"),
        ("Lipid Profile", "Biochemistry", "mg/dL", "", "Cholesterol panel"),
        ("CRP", "Inflammation", "mg/L", "0-5", "C-reactive protein"),
        ("Serum Creatinine", "Renal", "mg/dL", "0.6-1.3", "Kidney function"),
    ]
    lab_objs = []
    for name, cat, unit, rng, desc in tests:
        t = LabTest.query.filter_by(name=name).first()
        if not t:
            t = LabTest(name=name, category=cat, unit=unit, normal_range=rng, description=desc)
            db.session.add(t)
        lab_objs.append(t)
    db.session.flush()
    return lab_objs


def create_doctor(username, email, dept, specialization):
    user = User.query.filter_by(username=username).first()
    if user:
        return Doctor.query.filter_by(user_id=user.id).first()
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash("doctor123"),
        role="doctor",
    )
    db.session.add(user)
    db.session.flush()
    doc = Doctor(
        user_id=user.id,
        department=dept,
        specialization=specialization,
        phone=f"+1-555-{random.randint(3000,3999)}",
        qualification=f"MD {specialization}",
        experience_years=random.randint(3, 20),
    )
    db.session.add(doc)
    db.session.flush()
    return doc


def create_patient(username, email):
    user = User.query.filter_by(username=username).first()
    if user:
        return Patient.query.filter_by(user_id=user.id).first()
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash("patient123"),
        role="patient",
    )
    db.session.add(user)
    db.session.flush()
    pat = Patient(
        user_id=user.id,
        phone=f"+1-555-{random.randint(4000,4999)}",
        address=f"{random.randint(10,999)} Demo Avenue",
        date_of_birth=date(1970 + random.randint(0, 30), random.randint(1, 12), random.randint(1, 28)),
        blood_group=random.choice(["O+", "A+", "B+", "AB+", "O-"]),
        gender=random.choice(["Male", "Female"]),
        allergies=random.choice(["None", "Penicillin", "NSAIDs"]),
        chronic_conditions=random.choice(["None", "Hypertension", "Diabetes", "Asthma"]),
    )
    db.session.add(pat)
    db.session.flush()
    return pat


def create_encounters_for_pair(doctor, patient, meds, lab_tests):
    """Create several appointments + treatments + vitals + labs + billing + prescriptions + RPM readings."""
    today = date.today()
    num_appointments = random.randint(2, 4)
    for i in range(num_appointments):
        apt_date = today - timedelta(days=random.randint(5, 40))
        apt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=apt_date,
            time_slot=f"{9 + i}:00",
            status="completed",
            reason="Follow-up" if i else "Initial consult",
        )
        db.session.add(apt)
        db.session.flush()

        diagnosis = random.choice(DIAGNOSES)
        treatment = Treatment(
            appointment_id=apt.id,
            doctor_id=doctor.id,
            patient_id=patient.id,
            diagnosis=diagnosis,
            prescription="See structured meds below",
            medicines=", ".join({m.name for m in meds[:3]}),
            visit_type="Follow-up" if i else "Initial Consultation",
            notes="Demo generated encounter.",
            visit_date=apt_date,
        )
        db.session.add(treatment)
        db.session.flush()

        # Structured meds (pick 2–3 random)
        for med in random.sample(meds, k=min(3, len(meds))):
            tm = TreatmentMedication(
                treatment_id=treatment.id,
                medication_id=med.id,
                dose="1 tab",
                frequency=random.choice(["OD", "BID", "TID"]),
                duration=random.choice(["5 days", "10 days", "30 days"]),
                instructions=random.choice(["After food", "Before breakfast", "At bedtime"]),
            )
            db.session.add(tm)

        # Vitals
        v = Vital(
            appointment_id=apt.id,
            patient_id=patient.id,
            recorded_by=doctor.id,
            temperature=36.5 + random.random() * 1.0,
            blood_pressure_systolic=120 + random.randint(-15, 20),
            blood_pressure_diastolic=80 + random.randint(-10, 10),
            pulse_rate=72 + random.randint(-8, 10),
            spo2=96 + random.randint(-3, 1),
            respiratory_rate=16 + random.randint(-3, 3),
            notes="Auto-generated vitals",
        )
        db.session.add(v)

        # Lab order
        lab_test = random.choice(lab_tests)
        lo = LabOrder(
            appointment_id=apt.id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            lab_test_id=lab_test.id,
            status="resulted",
            result_value=str(random.randint(70, 180)),
            result_notes="Demo result",
        )
        db.session.add(lo)

        # Invoice
        inv = Invoice(
            patient_id=patient.id,
            appointment_id=apt.id,
            status="paid",
            subtotal=500.0,
            tax_percent=0,
            tax_amount=0,
            discount=0,
            total=500.0,
        )
        db.session.add(inv)
        db.session.flush()
        item = InvoiceItem(
            invoice_id=inv.id,
            description="Consultation Fee",
            item_type="consultation",
            quantity=1,
            unit_price=500.0,
            total_price=500.0,
        )
        db.session.add(item)

        # Pharmacy prescription
        rx = Prescription(
            treatment_id=treatment.id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            status=random.choice(["sent", "fulfilled", "partial"]),
        )
        db.session.add(rx)
        db.session.flush()
        for med in random.sample(meds, k=min(3, len(meds))):
            pi = PrescriptionItem(
                prescription_id=rx.id,
                medication_id=med.id,
                dose="1 tab",
                frequency="OD",
                duration="30 days",
                instructions="After dinner",
                quantity=30,
            )
            db.session.add(pi)

    # RPM readings for trend graphs (last ~30 days)
    for offset in range(30):
        r_date = today - timedelta(days=offset)
        r = PatientVitalReading(
            patient_id=patient.id,
            source="manual",
            recorded_at=r_date,
            blood_pressure_systolic=118 + random.randint(-12, 18),
            blood_pressure_diastolic=78 + random.randint(-8, 8),
            heart_rate=72 + random.randint(-10, 10),
            glucose_mg_dl=100 + random.randint(-20, 40),
            spo2=97 + random.randint(-4, 1),
            temperature_c=36.7 + random.random() * 0.8,
            weight_kg=75 + random.randint(-3, 3),
            notes="Demo RPM reading",
        )
        db.session.add(r)


def main():
    app = create_app()
    with app.app_context():
        depts = ensure_departments()
        meds = ensure_medications()
        lab_tests = ensure_lab_tests()

        # Create a few doctors across departments
        doctors = [
            create_doctor("cardio_doc2", "cardio2@example.com", depts["Cardiology"], "Cardiologist"),
            create_doctor("neuro_doc1", "neuro1@example.com", depts["Neurology"], "Neurologist"),
            create_doctor("ortho_doc1", "ortho1@example.com", depts["Orthopedics"], "Orthopedic Surgeon"),
        ]

        # Create patients and assign encounters with each doctor
        patients = [
            create_patient("patient_alpha", "alpha@example.com"),
            create_patient("patient_bravo", "bravo@example.com"),
            create_patient("patient_charlie", "charlie@example.com"),
            create_patient("patient_delta", "delta@example.com"),
            create_patient("patient_echo", "echo@example.com"),
            create_patient("patient_foxtrot", "foxtrot@example.com"),
        ]

        for i, pat in enumerate(patients):
            doc = doctors[i % len(doctors)]
            create_encounters_for_pair(doc, pat, meds, lab_tests)

        db.session.commit()
        print("Additional demo data inserted:")
        print("  Doctors:", ", ".join(d.user.username for d in doctors))
        print("  Patients:", ", ".join(p.user.username for p in patients))


if __name__ == "__main__":
    main()

