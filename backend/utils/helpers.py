from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*roles):
    """Decorator that checks JWT role claim against allowed roles."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify(msg="Access denied"), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if getattr(user, "last_login_at", None) else None,
    }


def serialize_doctor(doc):
    return {
        "id": doc.id,
        "user_id": doc.user_id,
        "username": doc.user.username,
        "email": doc.user.email,
        "is_active": doc.user.is_active,
        "department": doc.department.name if doc.department else None,
        "department_id": doc.department_id,
        "specialization": doc.specialization,
        "phone": doc.phone,
        "qualification": doc.qualification,
        "experience_years": doc.experience_years,
    }


def serialize_patient(pat):
    return {
        "id": pat.id,
        "user_id": pat.user_id,
        "username": pat.user.username,
        "email": pat.user.email,
        "is_active": pat.user.is_active,
        "phone": pat.phone,
        "address": pat.address,
        "date_of_birth": pat.date_of_birth.isoformat() if pat.date_of_birth else None,
        "blood_group": pat.blood_group,
        "gender": pat.gender,
        "allergies": pat.allergies,
        "chronic_conditions": pat.chronic_conditions,
        "emergency_contact_name": pat.emergency_contact_name,
        "emergency_contact_phone": pat.emergency_contact_phone,
        "insurance_id": pat.insurance_id,
        "insurance_provider": pat.insurance_provider,
        "height_cm": pat.height_cm,
        "weight_kg": pat.weight_kg,
    }


def serialize_appointment(apt):
    ts = apt.time_slot or ""
    if "_cancelled_" in ts:
        ts = ts.split("_cancelled_")[0]
    elif "_noshow_" in ts:
        ts = ts.split("_noshow_")[0]
    return {
        "id": apt.id,
        "patient_id": apt.patient_id,
        "doctor_id": apt.doctor_id,
        "patient_name": apt.patient.user.username if apt.patient else None,
        "doctor_name": apt.doctor.user.username if apt.doctor else None,
        "specialization": apt.doctor.specialization if apt.doctor else None,
        "date": apt.date.isoformat() if apt.date else None,
        "time_slot": ts,
        "status": apt.status,
        "reason": apt.reason,
        "created_at": apt.created_at.isoformat() if apt.created_at else None,
    }


def serialize_treatment(t):
    meds = []
    try:
        for tm in (t.prescribed_medicines or []):
            m = tm.medication
            meds.append({
                "id": tm.id,
                "medication_id": tm.medication_id,
                "name": m.name if m else None,
                "generic_name": m.generic_name if m else None,
                "form": m.form if m else None,
                "strength": m.strength if m else None,
                "manufacturer": m.manufacturer if m else None,
                "dose": tm.dose,
                "frequency": tm.frequency,
                "duration": tm.duration,
                "instructions": tm.instructions,
            })
    except Exception:
        meds = []
    return {
        "id": t.id,
        "appointment_id": t.appointment_id,
        "doctor_id": t.doctor_id,
        "patient_id": t.patient_id,
        "doctor_name": t.doctor.user.username if t.doctor else None,
        "diagnosis": t.diagnosis,
        "prescription": t.prescription,
        "medicines": t.medicines,
        "prescribed_medicines": meds,
        "visit_type": t.visit_type,
        "notes": t.notes,
        "visit_date": t.visit_date.isoformat() if t.visit_date else None,
    }


def serialize_availability(a):
    return {
        "id": a.id,
        "doctor_id": a.doctor_id,
        "date": a.date.isoformat() if a.date else None,
        "start_time": a.start_time,
        "end_time": a.end_time,
    }


def serialize_vital(v):
    return {
        "id": v.id,
        "appointment_id": v.appointment_id,
        "patient_id": v.patient_id,
        "recorded_by": v.recorded_by,
        "doctor_name": v.doctor.user.username if v.doctor and v.doctor.user else None,
        "temperature": v.temperature,
        "blood_pressure_systolic": v.blood_pressure_systolic,
        "blood_pressure_diastolic": v.blood_pressure_diastolic,
        "pulse_rate": v.pulse_rate,
        "spo2": v.spo2,
        "respiratory_rate": v.respiratory_rate,
        "notes": v.notes,
        "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None,
    }


def serialize_lab_test(t):
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "normal_range": t.normal_range,
        "unit": t.unit,
        "category": t.category,
        "is_active": t.is_active,
    }


def serialize_lab_order(o):
    lt = o.lab_test
    return {
        "id": o.id,
        "appointment_id": o.appointment_id,
        "patient_id": o.patient_id,
        "doctor_id": o.doctor_id,
        "doctor_name": o.doctor.user.username if o.doctor and o.doctor.user else None,
        "status": o.status,
        "result_value": o.result_value,
        "result_notes": o.result_notes,
        "ordered_at": o.ordered_at.isoformat() if o.ordered_at else None,
        "resulted_at": o.resulted_at.isoformat() if o.resulted_at else None,
        "lab_test": serialize_lab_test(lt) if lt else None,
    }


def serialize_invoice(inv):
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "patient_id": inv.patient_id,
        "appointment_id": inv.appointment_id,
        "status": inv.status,
        "subtotal": inv.subtotal,
        "tax_percent": inv.tax_percent,
        "tax_amount": inv.tax_amount,
        "discount": inv.discount,
        "total": inv.total,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "notes": inv.notes,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "patient_name": inv.patient.user.username if inv.patient and inv.patient.user else None,
        "items": [
            {
                "id": it.id,
                "description": it.description,
                "item_type": it.item_type,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "total_price": it.total_price,
            }
            for it in (inv.items or [])
        ],
    }
