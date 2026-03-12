from datetime import date, datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db, cache
from application.models import (
    Patient, Doctor, Department, Appointment,
    Treatment, Availability, User,
)
from utils.helpers import (
    role_required, serialize_doctor, serialize_appointment,
    serialize_treatment, serialize_availability, serialize_patient, serialize_vital,
)
from utils.email import send_email
from application.models import Medication, Vital, LabOrder, Invoice
from utils.audit import log_action

patient_bp = Blueprint("patient", __name__)


def _get_patient():
    user_id = int(get_jwt_identity())
    return Patient.query.filter_by(user_id=user_id).first()


@patient_bp.route("/departments", methods=["GET"])
@role_required("patient")
def departments():
    cached = cache.get("dept_list")
    if cached:
        return jsonify(cached)
    depts = [{"id": d.id, "name": d.name, "description": d.description or ""} for d in Department.query.all()]
    cache.set("dept_list", depts, timeout=600)
    return jsonify(depts)


@patient_bp.route("/doctors", methods=["GET"])
@role_required("patient")
def list_doctors():
    dept_id = request.args.get("department_id", type=int)
    spec = request.args.get("specialization", "")
    q = request.args.get("q", "")

    cache_key = f"doctor_list:{dept_id}:{spec}:{q}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached)

    query = Doctor.query.join(User).filter(User.is_active == True)
    if dept_id:
        query = query.filter(Doctor.department_id == dept_id)
    if spec:
        query = query.filter(Doctor.specialization.ilike(f"%{spec}%"))
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) | (Doctor.specialization.ilike(f"%{q}%"))
        )
    result = [serialize_doctor(d) for d in query.all()]
    cache.set(cache_key, result, timeout=300)
    return jsonify(result)


@patient_bp.route("/doctors/<int:doc_id>", methods=["GET"])
@role_required("patient")
def doctor_profile(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    avails = Availability.query.filter(
        Availability.doctor_id == doc_id,
        Availability.date >= date.today(),
    ).order_by(Availability.date, Availability.start_time).all()
    return jsonify(
        doctor=serialize_doctor(doc),
        availability=[serialize_availability(a) for a in avails],
    )


@patient_bp.route("/doctors/<int:doc_id>/slots", methods=["GET"])
@role_required("patient")
def doctor_slots(doc_id):
    """Return 30-min slots for a doctor on a given date, marking booked ones."""
    slot_date_str = request.args.get("date")
    if not slot_date_str:
        return jsonify(msg="date parameter required"), 400
    slot_date = date.fromisoformat(slot_date_str)
    if slot_date < date.today():
        return jsonify([])

    avails = Availability.query.filter(
        Availability.doctor_id == doc_id,
        Availability.date == slot_date,
    ).order_by(Availability.start_time).all()

    booked = {
        a.time_slot
        for a in Appointment.query.filter(
            Appointment.doctor_id == doc_id,
            Appointment.date == slot_date,
            Appointment.status.in_(["pending", "confirmed"]),
        ).all()
    }

    slots = []
    for av in avails:
        try:
            start = datetime.strptime(av.start_time, "%H:%M")
            end = datetime.strptime(av.end_time, "%H:%M")
        except ValueError:
            continue
        current = start
        while current + timedelta(minutes=30) <= end:
            t = current.strftime("%H:%M")
            slots.append({"time": t, "available": t not in booked})
            current += timedelta(minutes=30)

    return jsonify(slots)


@patient_bp.route("/appointments", methods=["GET"])
@role_required("patient")
def list_appointments():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    apts = Appointment.query.filter_by(patient_id=pat.id).order_by(
        Appointment.date.desc()
    ).all()
    return jsonify([serialize_appointment(a) for a in apts])


@patient_bp.route("/appointments", methods=["POST"])
@role_required("patient")
def book_appointment():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    apt_date = date.fromisoformat(data.get("date"))
    time_slot = data.get("time_slot")
    reason = data.get("reason", "")

    if apt_date < date.today():
        return jsonify(msg="Cannot book in the past"), 400

    existing = Appointment.query.filter_by(
        doctor_id=doctor_id, date=apt_date, time_slot=time_slot
    ).filter(Appointment.status.in_(["pending", "confirmed"])).first()
    if existing:
        return jsonify(msg="This slot is already booked"), 409

    avail = Availability.query.filter(
        Availability.doctor_id == doctor_id,
        Availability.date == apt_date,
        Availability.start_time <= time_slot,
        Availability.end_time > time_slot,
    ).first()
    if not avail:
        return jsonify(msg="Doctor not available at this time"), 400

    apt = Appointment(
        patient_id=pat.id, doctor_id=doctor_id,
        date=apt_date, time_slot=time_slot, reason=reason,
    )
    db.session.add(apt)
    db.session.commit()
    log_action(int(get_jwt_identity()), "patient.book_appointment", "appointment", apt.id, {"doctor_id": doctor_id}, request.remote_addr)
    try:
        from utils.notifications import create_notification
        create_notification(
            user_id=apt.doctor.user_id,
            title="New appointment booked",
            message=f"{apt.patient.user.username} booked an appointment on {apt.date} at {apt.time_slot}.",
            type="appointment",
            link=f"/doctor",
        )
    except Exception:
        pass

    doc = Doctor.query.get(doctor_id)
    send_email(
        to=pat.user.email,
        subject="Appointment Booked - MedFlow HMS",
        body=(
            f"Dear {pat.user.username},\n\n"
            f"Your appointment with Dr. {doc.user.username} has been booked.\n"
            f"Date: {apt_date}\nTime: {time_slot}\n"
            f"Status: Pending confirmation\n\n"
            f"You will receive a notification once the doctor confirms.\n\n"
            f"-- MedFlow HMS"
        ),
    )
    return jsonify(serialize_appointment(apt)), 201


@patient_bp.route("/appointments/<int:apt_id>/cancel", methods=["PUT"])
@role_required("patient")
def cancel_appointment(apt_id):
    pat = _get_patient()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.patient_id != pat.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status not in ("pending", "confirmed"):
        return jsonify(msg="Cannot cancel this appointment"), 400
    original_slot = apt.time_slot
    apt.status = "cancelled"
    apt.time_slot = f"{original_slot}_cancelled_{apt.id}"
    db.session.commit()
    log_action(int(get_jwt_identity()), "patient.cancel_appointment", "appointment", apt.id, None, request.remote_addr)
    try:
        from utils.notifications import create_notification
        create_notification(
            user_id=apt.doctor.user_id,
            title="Appointment cancelled",
            message=f"{apt.patient.user.username} cancelled an appointment on {apt.date} at {apt.time_slot}.",
            type="appointment",
            link="/doctor",
        )
    except Exception:
        pass
    return jsonify(serialize_appointment(apt))


@patient_bp.route("/appointments/<int:apt_id>/reschedule", methods=["PUT"])
@role_required("patient")
def reschedule_appointment(apt_id):
    pat = _get_patient()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.patient_id != pat.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status not in ("pending", "confirmed"):
        return jsonify(msg="Cannot reschedule this appointment"), 400

    data = request.get_json()
    new_date = date.fromisoformat(data.get("date"))
    new_slot = data.get("time_slot")

    if new_date < date.today():
        return jsonify(msg="Cannot book in the past"), 400

    avail = Availability.query.filter(
        Availability.doctor_id == apt.doctor_id,
        Availability.date == new_date,
        Availability.start_time <= new_slot,
        Availability.end_time > new_slot,
    ).first()
    if not avail:
        return jsonify(msg="Doctor not available at this time"), 400

    existing = Appointment.query.filter_by(
        doctor_id=apt.doctor_id, date=new_date, time_slot=new_slot,
    ).filter(Appointment.status.in_(["pending", "confirmed"])).first()
    if existing:
        return jsonify(msg="This slot is already booked"), 409

    apt.date = new_date
    apt.time_slot = new_slot
    db.session.commit()
    log_action(int(get_jwt_identity()), "patient.reschedule_appointment", "appointment", apt.id, {"date": new_date.isoformat(), "time_slot": new_slot}, request.remote_addr)
    return jsonify(serialize_appointment(apt))


@patient_bp.route("/history", methods=["GET"])
@role_required("patient")
def treatment_history():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    treatments = Treatment.query.filter_by(patient_id=pat.id).order_by(
        Treatment.visit_date.desc()
    ).all()
    return jsonify([serialize_treatment(t) for t in treatments])


@patient_bp.route("/medications", methods=["GET"])
@role_required("patient")
def list_medications():
    q = (request.args.get("q") or "").strip()
    query = Medication.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            (Medication.name.ilike(f"%{q}%"))
            | (Medication.generic_name.ilike(f"%{q}%"))
            | (Medication.manufacturer.ilike(f"%{q}%"))
            | (Medication.strength.ilike(f"%{q}%"))
        )
    meds = query.order_by(Medication.name.asc()).limit(50).all()
    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "generic_name": m.generic_name,
            "form": m.form,
            "strength": m.strength,
            "manufacturer": m.manufacturer,
        }
        for m in meds
    ])


@patient_bp.route("/profile", methods=["GET"])
@role_required("patient")
def get_profile():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    return jsonify(serialize_patient(pat))


@patient_bp.route("/profile", methods=["PUT"])
@role_required("patient")
def update_profile():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    data = request.get_json()
    pat.phone = data.get("phone", pat.phone)
    pat.address = data.get("address", pat.address)
    pat.gender = data.get("gender", pat.gender)
    pat.blood_group = data.get("blood_group", pat.blood_group)
    pat.allergies = data.get("allergies", pat.allergies)
    pat.chronic_conditions = data.get("chronic_conditions", pat.chronic_conditions)
    pat.emergency_contact_name = data.get("emergency_contact_name", pat.emergency_contact_name)
    pat.emergency_contact_phone = data.get("emergency_contact_phone", pat.emergency_contact_phone)
    pat.insurance_id = data.get("insurance_id", pat.insurance_id)
    pat.insurance_provider = data.get("insurance_provider", pat.insurance_provider)
    if data.get("height_cm") is not None:
        pat.height_cm = data.get("height_cm")
    if data.get("weight_kg") is not None:
        pat.weight_kg = data.get("weight_kg")
    if data.get("date_of_birth"):
        pat.date_of_birth = date.fromisoformat(data["date_of_birth"])
    db.session.commit()
    log_action(int(get_jwt_identity()), "patient.update_profile", "patient", pat.id, None, request.remote_addr)
    return jsonify(serialize_patient(pat))


@patient_bp.route("/appointments/<int:apt_id>/summary", methods=["GET"])
@role_required("patient")
def appointment_summary(apt_id):
    """Full appointment + treatment data for print view."""
    pat = _get_patient()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.patient_id != pat.id:
        return jsonify(msg="Not your appointment"), 403
    result = serialize_appointment(apt)
    result["patient_email"] = pat.user.email
    result["patient_phone"] = pat.phone
    result["patient_gender"] = pat.gender
    result["patient_blood_group"] = pat.blood_group
    result["patient_dob"] = pat.date_of_birth.isoformat() if pat.date_of_birth else None
    result["patient_allergies"] = pat.allergies
    result["patient_chronic_conditions"] = pat.chronic_conditions
    result["doctor_qualification"] = apt.doctor.qualification if apt.doctor else None
    result["doctor_department"] = apt.doctor.department.name if apt.doctor and apt.doctor.department else None
    result["doctor_phone"] = apt.doctor.phone if apt.doctor else None
    if apt.treatment:
        result["treatment"] = serialize_treatment(apt.treatment)
    else:
        result["treatment"] = None
    vital = Vital.query.filter_by(appointment_id=apt.id).first()
    result["vitals"] = serialize_vital(vital) if vital else None
    orders = LabOrder.query.filter_by(appointment_id=apt.id).order_by(LabOrder.ordered_at.desc()).all()
    from utils.helpers import serialize_lab_order
    result["lab_orders"] = [serialize_lab_order(o) for o in orders]
    return jsonify(result)


@patient_bp.route("/vitals", methods=["GET"])
@role_required("patient")
def vitals_history():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    vitals = Vital.query.filter_by(patient_id=pat.id).order_by(Vital.recorded_at.desc()).all()
    return jsonify([serialize_vital(v) for v in vitals])


@patient_bp.route("/lab-results", methods=["GET"])
@role_required("patient")
def lab_results():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    orders = LabOrder.query.filter_by(patient_id=pat.id).order_by(LabOrder.ordered_at.desc()).all()
    from utils.helpers import serialize_lab_order
    return jsonify([serialize_lab_order(o) for o in orders])


@patient_bp.route("/invoices", methods=["GET"])
@role_required("patient")
def list_invoices():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    from utils.helpers import serialize_invoice
    invoices = Invoice.query.filter_by(patient_id=pat.id).order_by(Invoice.created_at.desc()).all()
    return jsonify([serialize_invoice(inv) for inv in invoices])


@patient_bp.route("/invoices/<int:invoice_id>", methods=["GET"])
@role_required("patient")
def get_invoice(invoice_id):
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    inv = Invoice.query.get_or_404(invoice_id)
    if inv.patient_id != pat.id:
        return jsonify(msg="Not your invoice"), 403
    from utils.helpers import serialize_invoice
    return jsonify(serialize_invoice(inv))


@patient_bp.route("/export", methods=["POST"])
@role_required("patient")
def trigger_export():
    pat = _get_patient()
    if not pat:
        return jsonify(msg="Patient profile not found"), 404
    from tasks.jobs import export_patient_treatments
    task = export_patient_treatments.delay(pat.id)
    return jsonify(task_id=task.id, msg="Export started")


@patient_bp.route("/export/status/<task_id>", methods=["GET"])
@role_required("patient")
def export_status(task_id):
    from tasks.jobs import export_patient_treatments
    result = export_patient_treatments.AsyncResult(task_id)
    if result.ready():
        return jsonify(status="done", filepath=result.result)
    return jsonify(status="pending")
