from datetime import datetime

from application.extensions import db
from application.models import (
    Encounter,
    Treatment,
    Appointment,
    Vital,
    LabOrder,
)


def ensure_encounter_for_treatment(treatment: Treatment):
    """
    Create an Encounter wrapper for an existing Treatment (additive + safe).
    """
    if not treatment:
        return None

    existing = Encounter.query.filter_by(treatment_id=treatment.id).first()
    if existing:
        return existing

    apt = Appointment.query.get(treatment.appointment_id) if treatment.appointment_id else None
    occurred_at = None
    if apt and apt.date and apt.time_slot:
        # best-effort timestamp: date + time_slot
        try:
            occurred_at = datetime.fromisoformat(f"{apt.date.isoformat()}T{apt.time_slot}:00")
        except Exception:
            occurred_at = None

    enc = Encounter(
        patient_id=treatment.patient_id,
        doctor_id=treatment.doctor_id,
        appointment_id=treatment.appointment_id,
        treatment_id=treatment.id,
        occurred_at=occurred_at or datetime.utcnow(),
        summary=(treatment.diagnosis or "")[:200] or None,
    )
    db.session.add(enc)
    db.session.commit()
    return enc


def build_patient_timeline(patient_id: int, limit: int = 50, offset: int = 0):
    """
    Build a unified timeline from existing core tables (back-compat first).

    This does not require pre-populating EhrEvent; it is computed live.
    """
    items = []

    treatments = (
        Treatment.query.filter_by(patient_id=patient_id)
        .order_by(Treatment.visit_date.desc(), Treatment.created_at.desc())
        .limit(200)
        .all()
    )
    for t in treatments:
        ensure_encounter_for_treatment(t)
        items.append({
            "type": "encounter",
            "ref_id": t.id,
            "occurred_at": (t.visit_date.isoformat() if t.visit_date else None),
            "title": "Consultation",
            "summary": (t.diagnosis or "")[:200] or (t.notes or "")[:200] or None,
        })

    vitals = (
        Vital.query.filter_by(patient_id=patient_id)
        .order_by(Vital.recorded_at.desc())
        .limit(200)
        .all()
    )
    for v in vitals:
        items.append({
            "type": "vital",
            "ref_id": v.id,
            "occurred_at": v.recorded_at.isoformat() if v.recorded_at else None,
            "title": "Vitals recorded",
            "summary": None,
        })

    labs = (
        LabOrder.query.filter_by(patient_id=patient_id)
        .order_by(LabOrder.ordered_at.desc())
        .limit(200)
        .all()
    )
    for o in labs:
        items.append({
            "type": "lab_order",
            "ref_id": o.id,
            "occurred_at": o.ordered_at.isoformat() if o.ordered_at else None,
            "title": f"Lab: {o.lab_test.name if o.lab_test else 'Test'}",
            "summary": f"Status: {o.status}",
        })

    # Sort by occurred_at where possible
    def sort_key(it):
        try:
            return it["occurred_at"] or ""
        except Exception:
            return ""

    items.sort(key=sort_key, reverse=True)
    return items[offset: offset + limit]

