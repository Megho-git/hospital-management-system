from datetime import date, timedelta, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db
import os
from application.models import Doctor, Appointment, Treatment, Availability, User, Medication, TreatmentMedication, Vital, LabTest, LabOrder, Invoice, InvoiceItem
from utils.helpers import (
    role_required, serialize_appointment, serialize_treatment,
    serialize_availability, serialize_patient, serialize_doctor, serialize_vital, serialize_lab_order,
)
from utils.email import send_email
from utils.audit import log_action

doctor_bp = Blueprint("doctor", __name__)


def _get_doctor():
    user_id = int(get_jwt_identity())
    return Doctor.query.filter_by(user_id=user_id).first()


@doctor_bp.route("/dashboard", methods=["GET"])
@role_required("doctor")
def dashboard():
    doc = _get_doctor()
    if not doc:
        return jsonify(msg="Doctor profile not found"), 404
    upcoming = Appointment.query.filter(
        Appointment.doctor_id == doc.id,
        Appointment.date >= date.today(),
        Appointment.status.in_(["pending", "confirmed"]),
    ).order_by(Appointment.date, Appointment.time_slot).all()

    history = Appointment.query.filter(
        Appointment.doctor_id == doc.id,
        Appointment.status.in_(["completed", "no_show"]),
    ).order_by(Appointment.date.desc(), Appointment.time_slot.desc()).all()

    history_treatments = {}
    for apt in history:
        t = Treatment.query.filter_by(appointment_id=apt.id).first()
        if t:
            history_treatments[apt.id] = serialize_treatment(t)

    patients = {a.patient_id: a.patient for a in upcoming}
    return jsonify(
        appointments=[serialize_appointment(a) for a in upcoming],
        history=[serialize_appointment(a) for a in history],
        treatments=history_treatments,
        patients=[serialize_patient(p) for p in patients.values()],
    )


@doctor_bp.route("/appointments/<int:apt_id>/complete", methods=["PUT"])
@role_required("doctor")
def complete_appointment(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status not in ("pending", "confirmed"):
        return jsonify(msg="Appointment cannot be completed (wrong status)"), 400
    data = request.get_json()

    apt.status = "completed"
    treatment = Treatment(
        appointment_id=apt.id,
        doctor_id=doc.id,
        patient_id=apt.patient_id,
        diagnosis=data.get("diagnosis", ""),
        prescription=data.get("prescription", ""),
        medicines=data.get("medicines", ""),
        visit_type=data.get("visit_type", ""),
        notes=data.get("notes", ""),
        visit_date=apt.date,
    )
    db.session.add(treatment)
    db.session.flush()

    prescribed = data.get("prescribed_medicines") or []
    if isinstance(prescribed, list) and prescribed:
        names_for_legacy = []
        for item in prescribed:
            if not isinstance(item, dict):
                continue
            medication_id = item.get("medication_id")
            if not medication_id:
                continue
            med = Medication.query.get(medication_id)
            if not med:
                continue
            tm = TreatmentMedication(
                treatment_id=treatment.id,
                medication_id=medication_id,
                dose=(item.get("dose") or "").strip() or None,
                frequency=(item.get("frequency") or "").strip() or None,
                duration=(item.get("duration") or "").strip() or None,
                instructions=(item.get("instructions") or "").strip() or None,
            )
            db.session.add(tm)
            display = " ".join([p for p in [med.name, med.strength] if p])
            if display:
                names_for_legacy.append(display)
        if not treatment.medicines and names_for_legacy:
            treatment.medicines = ", ".join(names_for_legacy)[:500]

    # Auto-create draft invoice if not present
    existing_invoice = Invoice.query.filter_by(appointment_id=apt.id).first()
    if not existing_invoice:
        consultation_fee = float(os.getenv("CONSULTATION_FEE", "500"))
        inv = Invoice(
            patient_id=apt.patient_id,
            appointment_id=apt.id,
            status="draft",
            tax_percent=float(os.getenv("INVOICE_TAX_PERCENT", "0")),
            discount=float(os.getenv("INVOICE_DISCOUNT", "0")),
            notes="Auto-generated draft invoice on completion",
        )
        db.session.add(inv)
        db.session.flush()
        from utils.billing import generate_invoice_number, compute_totals
        inv.invoice_number = generate_invoice_number(inv.id)
        item_total = round(consultation_fee, 2)
        db.session.add(InvoiceItem(
            invoice_id=inv.id,
            description="Consultation Fee",
            item_type="consultation",
            quantity=1,
            unit_price=consultation_fee,
            total_price=item_total,
        ))
        totals = compute_totals(item_total, inv.tax_percent, inv.discount)
        inv.subtotal = totals["subtotal"]
        inv.tax_amount = totals["tax_amount"]
        inv.total = totals["total"]

    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.complete_appointment", "appointment", apt.id, {"patient_id": apt.patient_id}, request.remote_addr)
    result = serialize_appointment(apt)
    result["treatment"] = serialize_treatment(treatment)
    return jsonify(result)


@doctor_bp.route("/appointments/<int:apt_id>/cancel", methods=["PUT"])
@role_required("doctor")
def cancel_appointment(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status not in ("pending", "confirmed"):
        return jsonify(msg="Appointment cannot be cancelled (wrong status)"), 400
    original_slot = apt.time_slot
    apt.status = "cancelled"
    apt.time_slot = f"{original_slot}_cancelled_{apt.id}"
    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.cancel_appointment", "appointment", apt.id, None, request.remote_addr)
    return jsonify(serialize_appointment(apt))


@doctor_bp.route("/appointments/<int:apt_id>/confirm", methods=["PUT"])
@role_required("doctor")
def confirm_appointment(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status != "pending":
        return jsonify(msg="Only pending appointments can be confirmed"), 400
    apt.status = "confirmed"
    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.confirm_appointment", "appointment", apt.id, None, request.remote_addr)
    try:
        from utils.notifications import create_notification
        create_notification(
            user_id=apt.patient.user_id,
            title="Appointment confirmed",
            message=f"Your appointment with Dr. {doc.user.username} on {apt.date} at {apt.time_slot} has been confirmed.",
            type="appointment",
            link="/patient",
        )
    except Exception:
        pass

    send_email(
        to=apt.patient.user.email,
        subject="Appointment Confirmed - MedFlow HMS",
        body=(
            f"Dear {apt.patient.user.username},\n\n"
            f"Your appointment with Dr. {doc.user.username} has been confirmed.\n"
            f"Date: {apt.date}\nTime: {apt.time_slot}\n\n"
            f"Please arrive 10 minutes early.\n\n"
            f"-- MedFlow HMS"
        ),
    )
    return jsonify(serialize_appointment(apt))


@doctor_bp.route("/appointments/<int:apt_id>/no-show", methods=["PUT"])
@role_required("doctor")
def no_show_appointment(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    if apt.status not in ("pending", "confirmed"):
        return jsonify(msg="Cannot mark as no-show"), 400
    original_slot = apt.time_slot
    apt.status = "no_show"
    apt.time_slot = f"{original_slot}_noshow_{apt.id}"
    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.no_show_appointment", "appointment", apt.id, None, request.remote_addr)
    return jsonify(serialize_appointment(apt))


@doctor_bp.route("/appointments/<int:apt_id>/vitals", methods=["GET"])
@role_required("doctor")
def get_vitals(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    v = Vital.query.filter_by(appointment_id=apt.id).first()
    return jsonify(serialize_vital(v) if v else None)


@doctor_bp.route("/appointments/<int:apt_id>/vitals", methods=["POST"])
@role_required("doctor")
def set_vitals(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    data = request.get_json() or {}

    v = Vital.query.filter_by(appointment_id=apt.id).first()
    if not v:
        v = Vital(appointment_id=apt.id, patient_id=apt.patient_id, recorded_by=doc.id)
        db.session.add(v)

    v.temperature = data.get("temperature", v.temperature)
    v.blood_pressure_systolic = data.get("blood_pressure_systolic", v.blood_pressure_systolic)
    v.blood_pressure_diastolic = data.get("blood_pressure_diastolic", v.blood_pressure_diastolic)
    v.pulse_rate = data.get("pulse_rate", v.pulse_rate)
    v.spo2 = data.get("spo2", v.spo2)
    v.respiratory_rate = data.get("respiratory_rate", v.respiratory_rate)
    v.notes = data.get("notes", v.notes)

    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.record_vitals", "appointment", apt.id, None, request.remote_addr)
    return jsonify(serialize_vital(v)), 201


@doctor_bp.route("/availability", methods=["GET"])
@role_required("doctor")
def get_availability():
    doc = _get_doctor()
    avails = Availability.query.filter(
        Availability.doctor_id == doc.id,
        Availability.date >= date.today(),
    ).order_by(Availability.date, Availability.start_time).all()
    return jsonify([serialize_availability(a) for a in avails])


@doctor_bp.route("/availability", methods=["POST"])
@role_required("doctor")
def set_availability():
    doc = _get_doctor()
    data = request.get_json()
    slots = data.get("slots", [])

    today = date.today()
    max_date = today + timedelta(days=30)
    Availability.query.filter(
        Availability.doctor_id == doc.id,
        Availability.date >= today,
    ).delete()

    for slot in slots:
        slot_date = date.fromisoformat(slot["date"])
        if slot_date < today or slot_date > max_date:
            continue
        db.session.add(Availability(
            doctor_id=doc.id,
            date=slot_date,
            start_time=slot["start_time"],
            end_time=slot["end_time"],
        ))

    db.session.commit()
    return jsonify(msg="Availability updated")


@doctor_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
@role_required("doctor")
def patient_history(patient_id):
    doc = _get_doctor()
    treatments = Treatment.query.filter_by(
        doctor_id=doc.id, patient_id=patient_id
    ).order_by(Treatment.visit_date.desc()).all()
    return jsonify([serialize_treatment(t) for t in treatments])


@doctor_bp.route("/profile", methods=["GET"])
@role_required("doctor")
def get_profile():
    doc = _get_doctor()
    if not doc:
        return jsonify(msg="Doctor profile not found"), 404
    return jsonify(serialize_doctor(doc))


@doctor_bp.route("/profile", methods=["PUT"])
@role_required("doctor")
def update_profile():
    doc = _get_doctor()
    if not doc:
        return jsonify(msg="Doctor profile not found"), 404
    data = request.get_json()
    doc.specialization = data.get("specialization", doc.specialization)
    doc.phone = data.get("phone", doc.phone)
    doc.qualification = data.get("qualification", doc.qualification)
    exp = data.get("experience_years")
    if exp is not None:
        if exp < 0:
            return jsonify(msg="Experience years cannot be negative"), 400
        doc.experience_years = exp
    db.session.commit()
    return jsonify(serialize_doctor(doc))


@doctor_bp.route("/treatments/<int:treatment_id>", methods=["PUT"])
@role_required("doctor")
def edit_treatment(treatment_id):
    doc = _get_doctor()
    treatment = Treatment.query.get_or_404(treatment_id)
    if treatment.doctor_id != doc.id:
        return jsonify(msg="Not your treatment record"), 403
    data = request.get_json()
    treatment.diagnosis = data.get("diagnosis", treatment.diagnosis)
    treatment.prescription = data.get("prescription", treatment.prescription)
    treatment.medicines = data.get("medicines", treatment.medicines)
    treatment.visit_type = data.get("visit_type", treatment.visit_type)
    treatment.notes = data.get("notes", treatment.notes)

    prescribed = data.get("prescribed_medicines")
    if prescribed is not None:
        TreatmentMedication.query.filter_by(treatment_id=treatment.id).delete()
        names_for_legacy = []
        if isinstance(prescribed, list):
            for item in prescribed:
                if not isinstance(item, dict):
                    continue
                medication_id = item.get("medication_id")
                if not medication_id:
                    continue
                med = Medication.query.get(medication_id)
                if not med:
                    continue
                db.session.add(TreatmentMedication(
                    treatment_id=treatment.id,
                    medication_id=medication_id,
                    dose=(item.get("dose") or "").strip() or None,
                    frequency=(item.get("frequency") or "").strip() or None,
                    duration=(item.get("duration") or "").strip() or None,
                    instructions=(item.get("instructions") or "").strip() or None,
                ))
                display = " ".join([p for p in [med.name, med.strength] if p])
                if display:
                    names_for_legacy.append(display)
        if names_for_legacy:
            treatment.medicines = ", ".join(names_for_legacy)[:500]

    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.edit_treatment", "treatment", treatment.id, {"appointment_id": treatment.appointment_id}, request.remote_addr)
    return jsonify(serialize_treatment(treatment))


@doctor_bp.route("/medications", methods=["GET"])
@role_required("doctor")
def search_medications():
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


@doctor_bp.route("/appointments/<int:apt_id>/lab-orders", methods=["GET"])
@role_required("doctor")
def list_lab_orders(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    orders = LabOrder.query.filter_by(appointment_id=apt.id).order_by(LabOrder.ordered_at.desc()).all()
    return jsonify([serialize_lab_order(o) for o in orders])


@doctor_bp.route("/appointments/<int:apt_id>/lab-orders", methods=["POST"])
@role_required("doctor")
def create_lab_orders(apt_id):
    doc = _get_doctor()
    apt = Appointment.query.get_or_404(apt_id)
    if apt.doctor_id != doc.id:
        return jsonify(msg="Not your appointment"), 403
    data = request.get_json() or {}
    test_ids = data.get("lab_test_ids") or []
    if not isinstance(test_ids, list) or not test_ids:
        return jsonify(msg="lab_test_ids must be a non-empty list"), 400

    created = []
    for test_id in test_ids:
        t = LabTest.query.get(test_id)
        if not t or not t.is_active:
            continue
        o = LabOrder.query.filter_by(appointment_id=apt.id, lab_test_id=t.id).first()
        if o:
            continue
        o = LabOrder(
            appointment_id=apt.id,
            patient_id=apt.patient_id,
            doctor_id=doc.id,
            lab_test_id=t.id,
            status="ordered",
        )
        db.session.add(o)
        created.append(o)
    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.create_lab_orders", "appointment", apt.id, {"count": len(created)}, request.remote_addr)
    return jsonify([serialize_lab_order(o) for o in created]), 201


@doctor_bp.route("/lab-orders/<int:order_id>", methods=["PUT"])
@role_required("doctor")
def update_lab_order(order_id):
    doc = _get_doctor()
    o = LabOrder.query.get_or_404(order_id)
    if o.doctor_id != doc.id:
        return jsonify(msg="Not your lab order"), 403
    data = request.get_json() or {}
    uid = int(get_jwt_identity())
    if data.get("status") is not None:
        status = data.get("status")
        if status not in ("ordered", "collected", "resulted", "cancelled"):
            return jsonify(msg="Invalid status"), 400
        if o.status != status:
            from application.models import LabOrderStatusHistory
            db.session.add(LabOrderStatusHistory(
                lab_order_id=o.id, old_status=o.status,
                new_status=status, changed_by_user_id=uid,
            ))
        o.status = status
        if status == "resulted" and not o.resulted_at:
            o.resulted_at = datetime.utcnow()
    if data.get("result_value") is not None:
        o.result_value = (data.get("result_value") or "").strip() or None
    if data.get("result_notes") is not None:
        o.result_notes = (data.get("result_notes") or "").strip() or None
    db.session.commit()
    log_action(int(get_jwt_identity()), "doctor.update_lab_order", "lab_order", o.id, {"status": o.status}, request.remote_addr)
    if o.status == "resulted":
        try:
            from utils.notifications import create_notification
            create_notification(
                user_id=o.patient.user_id,
                title="Lab results available",
                message=f"Result for {o.lab_test.name} is available.",
                type="lab",
                link="/patient/lab-results",
            )
        except Exception:
            pass
    return jsonify(serialize_lab_order(o))


@doctor_bp.route("/lab-tests", methods=["GET"])
@role_required("doctor")
def search_lab_tests():
    q = (request.args.get("q") or "").strip()
    query = LabTest.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            (LabTest.name.ilike(f"%{q}%"))
            | (LabTest.category.ilike(f"%{q}%"))
            | (LabTest.unit.ilike(f"%{q}%"))
            | (LabTest.normal_range.ilike(f"%{q}%"))
        )
    tests = query.order_by(LabTest.category.asc(), LabTest.name.asc()).limit(50).all()
    return jsonify([
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "normal_range": t.normal_range,
            "unit": t.unit,
            "category": t.category,
        }
        for t in tests
    ])
