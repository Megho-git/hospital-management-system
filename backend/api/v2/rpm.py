from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from application.extensions import db
from application.models import Patient, User, PatientVitalReading
from utils.helpers import role_required
from utils.audit import log_action


rpm_v2_bp = Blueprint("rpm_v2", __name__)


def _assert_patient_access(patient: Patient, viewer: User) -> bool:
    if not patient or not viewer:
        return False
    if viewer.role == "admin":
        return True
    if viewer.role == "doctor":
        return True  # current system doesn't constrain panels to a doctor-patient panel
    if viewer.role == "patient":
        return patient.user_id == viewer.id
    return False


def _check_abnormal(r: PatientVitalReading):
    """
    Very simple default thresholds. In a real system this becomes per-patient rules.
    """
    alerts = []
    if r.blood_pressure_systolic and r.blood_pressure_systolic >= 180:
        alerts.append("High systolic blood pressure")
    if r.blood_pressure_diastolic and r.blood_pressure_diastolic >= 120:
        alerts.append("High diastolic blood pressure")
    if r.heart_rate and (r.heart_rate < 40 or r.heart_rate > 130):
        alerts.append("Abnormal heart rate")
    if r.glucose_mg_dl and (r.glucose_mg_dl < 60 or r.glucose_mg_dl > 300):
        alerts.append("Abnormal glucose")
    if r.spo2 and r.spo2 < 90:
        alerts.append("Low SpO2")
    return alerts


@rpm_v2_bp.route("/patients/<int:patient_id>/readings", methods=["GET"])
@role_required("admin", "doctor", "patient")
def list_readings(patient_id):
    viewer_user_id = int(get_jwt_identity())
    viewer = User.query.get(viewer_user_id)
    pat = Patient.query.get_or_404(patient_id)
    if not _assert_patient_access(pat, viewer):
        return jsonify(msg="Access denied"), 403

    limit = min(request.args.get("limit", type=int) or 200, 500)
    items = (
        PatientVitalReading.query.filter_by(patient_id=pat.id)
        .order_by(PatientVitalReading.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify(items=[
        {
            "id": r.id,
            "source": r.source,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            "blood_pressure_systolic": r.blood_pressure_systolic,
            "blood_pressure_diastolic": r.blood_pressure_diastolic,
            "heart_rate": r.heart_rate,
            "glucose_mg_dl": r.glucose_mg_dl,
            "spo2": r.spo2,
            "temperature_c": r.temperature_c,
            "weight_kg": r.weight_kg,
            "notes": r.notes,
        }
        for r in items
    ])


@rpm_v2_bp.route("/patients/<int:patient_id>/readings", methods=["POST"])
@role_required("patient")
def create_reading(patient_id):
    viewer_user_id = int(get_jwt_identity())
    viewer = User.query.get(viewer_user_id)
    pat = Patient.query.get_or_404(patient_id)
    if not _assert_patient_access(pat, viewer):
        return jsonify(msg="Access denied"), 403

    data = request.get_json() or {}
    r = PatientVitalReading(
        patient_id=pat.id,
        source="manual",
        recorded_at=datetime.utcnow(),
        blood_pressure_systolic=data.get("blood_pressure_systolic"),
        blood_pressure_diastolic=data.get("blood_pressure_diastolic"),
        heart_rate=data.get("heart_rate"),
        glucose_mg_dl=data.get("glucose_mg_dl"),
        spo2=data.get("spo2"),
        temperature_c=data.get("temperature_c"),
        weight_kg=data.get("weight_kg"),
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(r)
    db.session.commit()
    log_action(viewer_user_id, "rpm.v2.reading_create", "patient", pat.id, {"reading_id": r.id}, request.remote_addr)

    alerts = _check_abnormal(r)
    if alerts:
        try:
            from utils.notifications import create_notification
            # Minimal: notify admin(s). In the next iteration, notify assigned doctor/care-team.
            from application.models import User as U
            admins = U.query.filter_by(role="admin").all()
            for a in admins:
                create_notification(
                    user_id=a.id,
                    title="RPM alert",
                    message=f"Patient #{pat.id}: {', '.join(alerts)}",
                    type="rpm",
                    link=f"/admin",
                )
        except Exception:
            pass

    return jsonify(id=r.id, alerts=alerts), 201

