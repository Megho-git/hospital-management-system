import csv
import io
import os
from datetime import date, timedelta
from . import celery_app


@celery_app.task(name="daily_reminder")
def daily_reminder():
    """Check tomorrow's appointments and log reminders."""
    from app import app
    with app.app_context():
        from application.models import Appointment
        tomorrow = date.today() + timedelta(days=1)
        apts = Appointment.query.filter_by(date=tomorrow, status="pending").all()
        for apt in apts:
            patient_email = apt.patient.user.email
            body = (f"Dear {apt.patient.user.username}, you have an appointment "
                    f"with Dr. {apt.doctor.user.username} on {apt.date} at {apt.time_slot}. "
                    f"Please visit the hospital at the scheduled time.")
            print(
                f"[REMINDER] Patient {apt.patient.user.username} has appointment "
                f"with Dr. {apt.doctor.user.username} on {apt.date} at {apt.time_slot}"
            )
            print(f"[EMAIL] To: {patient_email} | Subject: Appointment Reminder | Body: {body}")
        return f"Sent {len(apts)} reminders"


@celery_app.task(name="monthly_doctor_report")
def monthly_doctor_report():
    """Generate HTML report for each doctor's monthly activity."""
    from app import app
    with app.app_context():
        from application.models import Doctor, Appointment, Treatment
        today = date.today()
        month_start = today.replace(day=1)

        reports_dir = os.path.join(app.instance_path, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        for doc in Doctor.query.all():
            apts = Appointment.query.filter(
                Appointment.doctor_id == doc.id,
                Appointment.date >= month_start,
                Appointment.date <= today,
            ).all()
            completed = [a for a in apts if a.status == "completed"]
            html = f"""<html><body>
            <h1>Monthly Report - Dr. {doc.user.username}</h1>
            <p>Period: {month_start} to {today}</p>
            <p>Total Appointments: {len(apts)}</p>
            <p>Completed: {len(completed)}</p>
            <p>Cancelled: {len([a for a in apts if a.status == 'cancelled'])}</p>
            <h2>Completed Appointments</h2><ul>"""
            for a in completed:
                html += f"<li>{a.date} {a.time_slot} - {a.patient.user.username}</li>"
            html += "</ul></body></html>"

            path = os.path.join(reports_dir, f"doctor_{doc.id}_{today.isoformat()}.html")
            with open(path, "w") as f:
                f.write(html)
            print(f"[REPORT] Generated report for Dr. {doc.user.username} at {path}")
            print(f"[EMAIL] To: {doc.user.email} | Subject: Monthly Activity Report | Attachment: {path}")

        return "Reports generated"


@celery_app.task(name="export_csv")
def export_csv(data_type="appointments"):
    """Export data as CSV. Returns the file path."""
    from app import app
    with app.app_context():
        from application.models import Appointment, Doctor, Patient

        exports_dir = os.path.join(app.instance_path, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, f"{data_type}_{date.today().isoformat()}.csv")

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            if data_type == "appointments":
                writer.writerow(["ID", "Patient", "Doctor", "Date", "Time", "Status", "Reason"])
                for a in Appointment.query.all():
                    writer.writerow([
                        a.id, a.patient.user.username, a.doctor.user.username,
                        a.date.isoformat(), a.time_slot, a.status, a.reason,
                    ])
            elif data_type == "doctors":
                writer.writerow(["ID", "Name", "Specialization", "Department", "Phone"])
                for d in Doctor.query.all():
                    writer.writerow([
                        d.id, d.user.username, d.specialization,
                        d.department.name if d.department else "", d.phone,
                    ])
            elif data_type == "patients":
                writer.writerow(["ID", "Name", "Email", "Phone", "Gender", "Blood Group"])
                for p in Patient.query.all():
                    writer.writerow([
                        p.id, p.user.username, p.user.email,
                        p.phone, p.gender, p.blood_group,
                    ])

        return filepath


@celery_app.task(name="export_patient_treatments")
def export_patient_treatments(patient_id):
    """Export a single patient's treatment history as CSV."""
    from app import app
    with app.app_context():
        from application.models import Treatment, Patient, TreatmentMedication

        pat = Patient.query.get(patient_id)
        if not pat:
            return "Patient not found"

        exports_dir = os.path.join(app.instance_path, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        filepath = os.path.join(exports_dir, f"treatments_patient_{patient_id}_{date.today().isoformat()}.csv")

        treatments = Treatment.query.filter_by(patient_id=patient_id).order_by(Treatment.visit_date.desc()).all()
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Patient ID", "Patient Name", "Consulting Doctor", "Appointment Date",
                             "Time Slot", "Diagnosis", "Prescription", "Medicines (Legacy)", "Prescribed Medicines (Structured)", "Visit Type", "Notes"])
            for t in treatments:
                apt = t.appointment
                structured = []
                try:
                    for tm in TreatmentMedication.query.filter_by(treatment_id=t.id).all():
                        m = tm.medication
                        display = " ".join([p for p in [m.name if m else "", m.strength if m else ""] if p]).strip()
                        details = " • ".join([p for p in [tm.dose, tm.frequency, tm.duration] if p]).strip()
                        instr = (tm.instructions or "").strip()
                        structured.append(" | ".join([x for x in [display, details, instr] if x]))
                except Exception:
                    structured = []
                writer.writerow([
                    pat.id, pat.user.username,
                    t.doctor.user.username if t.doctor else "",
                    t.visit_date.isoformat() if t.visit_date else "",
                    apt.time_slot if apt else "",
                    t.diagnosis, t.prescription, t.medicines, "; ".join(structured), t.visit_type, t.notes,
                ])

        print(f"[EXPORT] Patient treatment CSV generated at {filepath}")
        print(f"[EMAIL] To: {pat.user.email} | Subject: Your Treatment History Export is Ready | File: {filepath}")
        return filepath


celery_app.conf.beat_schedule = {
    "daily-reminder": {
        "task": "daily_reminder",
        "schedule": 86400.0,  # once per day
    },
    "monthly-report": {
        "task": "monthly_doctor_report",
        "schedule": 2592000.0,  # ~30 days
    },
}
