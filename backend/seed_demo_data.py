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
)


def main():
    app = create_app()
    with app.app_context():
        # Avoid duplicating demo data
        if User.query.filter_by(username="demo_doctor").first() and User.query.filter_by(username="demo_patient").first():
            print("Demo data appears to already exist; skipping.")
            return

        # Departments (reuse existing if already seeded by app)
        cardio = Department.query.filter_by(name="Cardiology").first()
        neuro = Department.query.filter_by(name="Neurology").first()
        if not cardio:
            cardio = Department(name="Cardiology")
            db.session.add(cardio)
        if not neuro:
            neuro = Department(name="Neurology")
            db.session.add(neuro)

        # Users
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("admin123"),
                role="admin",
            )
            db.session.add(admin)
        doc_user = User(
            username="demo_doctor",
            email="doctor@example.com",
            password_hash=generate_password_hash("doctor123"),
            role="doctor",
        )
        pat_user = User(
            username="demo_patient",
            email="patient@example.com",
            password_hash=generate_password_hash("patient123"),
            role="patient",
        )
        db.session.add_all([doc_user, pat_user])
        db.session.flush()

        # Doctor & Patient
        doctor = Doctor(
            user_id=doc_user.id,
            department=cardio,
            specialization="Cardiologist",
            phone="+1-555-0101",
            qualification="MD Cardiology",
            experience_years=10,
        )
        patient = Patient(
            user_id=pat_user.id,
            phone="+1-555-0202",
            address="123 Demo Street",
            date_of_birth=date(1985, 5, 15),
            blood_group="O+",
            gender="Male",
            allergies="Penicillin",
            chronic_conditions="Hypertension",
        )
        db.session.add_all([doctor, patient])
        db.session.flush()

        # Medications
        meds = [
            Medication(name="Atorvastatin", generic_name="Atorvastatin", form="tablet", strength="20mg", manufacturer="Demo Pharma"),
            Medication(name="Aspirin", generic_name="Acetylsalicylic Acid", form="tablet", strength="75mg", manufacturer="Demo Pharma"),
            Medication(name="Metformin", generic_name="Metformin", form="tablet", strength="500mg", manufacturer="Demo Pharma"),
        ]
        db.session.add_all(meds)
        db.session.flush()

        # Drug inventory (pharmacy)
        drug_items = []
        for m in meds:
            di = DrugItem(medication_id=m.id, sku=f"SKU-{m.id}", reorder_level=10)
            drug_items.append(di)
        db.session.add_all(drug_items)
        db.session.flush()

        for di in drug_items:
            lot = StockLot(
                drug_item_id=di.id,
                batch_number=f"BATCH-{di.id}",
                expiry_date=date.today() + timedelta(days=365),
                quantity_on_hand=100,
                unit_cost=5.0,
            )
            db.session.add(lot)

        # Lab tests
        labs = [
            LabTest(name="CBC", category="Hematology", unit="", normal_range="", description="Complete blood count"),
            LabTest(name="Fasting Blood Sugar", category="Biochemistry", unit="mg/dL", normal_range="70-100"),
            LabTest(name="Lipid Profile", category="Biochemistry", unit="mg/dL", normal_range=""),
        ]
        db.session.add_all(labs)

        db.session.flush()

        # Appointments, treatments, vitals, labs, invoices, prescriptions
        for i in range(5):
            apt_date = date.today() - timedelta(days=5 - i)
            apt = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                date=apt_date,
                time_slot=f"{10 + i}:00",
                status="completed",
                reason="Follow-up",
            )
            db.session.add(apt)
            db.session.flush()

            treatment = Treatment(
                appointment_id=apt.id,
                doctor_id=doctor.id,
                patient_id=patient.id,
                diagnosis="Stable hypertension",
                prescription="Continue current meds",
                medicines="Atorvastatin 20mg, Aspirin 75mg",
                visit_type="Follow-up",
                notes="Patient doing well, continue therapy.",
                visit_date=apt_date,
            )
            db.session.add(treatment)
            db.session.flush()

            # Structured meds
            for med in meds[:2]:
                tm = TreatmentMedication(
                    treatment_id=treatment.id,
                    medication_id=med.id,
                    dose="1 tab",
                    frequency="OD",
                    duration="30 days",
                    instructions="After dinner",
                )
                db.session.add(tm)

            # Vitals
            v = Vital(
                appointment_id=apt.id,
                patient_id=patient.id,
                recorded_by=doctor.id,
                temperature=36.8,
                blood_pressure_systolic=120 + random.randint(-10, 10),
                blood_pressure_diastolic=80 + random.randint(-5, 5),
                pulse_rate=72 + random.randint(-5, 5),
                spo2=98,
                respiratory_rate=16,
                notes="Routine check",
            )
            db.session.add(v)

            # Lab order
            lab_test = random.choice(labs)
            lo = LabOrder(
                appointment_id=apt.id,
                patient_id=patient.id,
                doctor_id=doctor.id,
                lab_test_id=lab_test.id,
                status="resulted",
                result_value="90" if lab_test.name == "Fasting Blood Sugar" else "",
                result_notes="Within normal range",
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
                status="fulfilled",
            )
            db.session.add(rx)
            db.session.flush()
            for med in meds[:2]:
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

        db.session.commit()
        print("Demo data inserted:")
        print(f"  Admin: admin / admin123")
        print(f"  Doctor: demo_doctor / doctor123")
        print(f"  Patient: demo_patient / patient123")


if __name__ == "__main__":
    main()

