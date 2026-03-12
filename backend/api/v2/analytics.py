from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from application.models import Appointment, Doctor, Department, Patient, Invoice, User
from utils.helpers import role_required
from utils.audit import log_action


analytics_v2_bp = Blueprint("analytics_v2", __name__)


@analytics_v2_bp.route("/appointments/load", methods=["GET"])
@role_required("admin")
def appointment_load():
    """
    Returns counts per day over a window.
    """
    days = min(request.args.get("days", type=int) or 30, 365)
    start = date.today() - timedelta(days=days - 1)
    end = date.today()

    rows = (
        Appointment.query.filter(Appointment.date >= start, Appointment.date <= end)
        .all()
    )
    counts = {}
    for a in rows:
        k = a.date.isoformat() if a.date else None
        if not k:
            continue
        counts[k] = counts.get(k, 0) + 1

    series = [
        {"date": (start + timedelta(days=i)).isoformat(), "count": counts.get((start + timedelta(days=i)).isoformat(), 0)}
        for i in range(days)
    ]
    log_action(int(get_jwt_identity()), "analytics.v2.appointment_load", "analytics", None, {"days": days}, request.remote_addr)
    return jsonify(start=start.isoformat(), end=end.isoformat(), series=series)


@analytics_v2_bp.route("/departments/utilization", methods=["GET"])
@role_required("admin")
def department_utilization():
    """
    Utilization proxy: appointments per department in last N days.
    """
    days = min(request.args.get("days", type=int) or 30, 365)
    start = date.today() - timedelta(days=days)

    # join via doctor -> department
    from application.models import Doctor as D
    rows = (
        Appointment.query.join(D, Appointment.doctor_id == D.id)
        .filter(Appointment.date >= start)
        .all()
    )
    by_dept = {}
    for a in rows:
        dept = a.doctor.department.name if a.doctor and a.doctor.department else "Unassigned"
        by_dept[dept] = by_dept.get(dept, 0) + 1

    items = [{"department": k, "appointments": v} for k, v in sorted(by_dept.items(), key=lambda x: x[1], reverse=True)]
    log_action(int(get_jwt_identity()), "analytics.v2.department_utilization", "analytics", None, {"days": days}, request.remote_addr)
    return jsonify(days=days, items=items)


@analytics_v2_bp.route("/doctors/performance", methods=["GET"])
@role_required("admin")
def doctor_performance():
    """
    Simple performance metrics over last N days:
    - total appointments
    - completed
    - no_show
    - cancellation rate
    """
    days = min(request.args.get("days", type=int) or 30, 365)
    start = date.today() - timedelta(days=days)
    apts = Appointment.query.filter(Appointment.date >= start).all()

    metrics = {}
    for a in apts:
        did = a.doctor_id
        m = metrics.setdefault(did, {"total": 0, "completed": 0, "no_show": 0, "cancelled": 0})
        m["total"] += 1
        if a.status == "completed":
            m["completed"] += 1
        if a.status == "no_show":
            m["no_show"] += 1
        if a.status == "cancelled":
            m["cancelled"] += 1

    items = []
    for doc in Doctor.query.all():
        m = metrics.get(doc.id, {"total": 0, "completed": 0, "no_show": 0, "cancelled": 0})
        total = m["total"] or 0
        cancel_rate = round((m["cancelled"] / total) * 100, 2) if total else 0
        items.append({
            "doctor_id": doc.id,
            "doctor_name": doc.user.username if doc.user else None,
            "department": doc.department.name if doc.department else None,
            "total": total,
            "completed": m["completed"],
            "no_show": m["no_show"],
            "cancelled": m["cancelled"],
            "cancellation_rate": cancel_rate,
        })
    items.sort(key=lambda x: x["total"], reverse=True)
    log_action(int(get_jwt_identity()), "analytics.v2.doctor_performance", "analytics", None, {"days": days}, request.remote_addr)
    return jsonify(days=days, items=items)


@analytics_v2_bp.route("/patients/inflow", methods=["GET"])
@role_required("admin")
def patient_inflow():
    """
    Patient inflow proxy: new patient user registrations per day.
    """
    days = min(request.args.get("days", type=int) or 30, 365)
    start_dt = datetime.utcnow() - timedelta(days=days - 1)

    # Patient table links to user; use user.created_at
    patients = Patient.query.all()
    counts = {}
    for p in patients:
        if not p.user or not p.user.created_at:
            continue
        if p.user.created_at < start_dt:
            continue
        k = p.user.created_at.date().isoformat()
        counts[k] = counts.get(k, 0) + 1

    start = start_dt.date()
    series = [
        {"date": (start + timedelta(days=i)).isoformat(), "count": counts.get((start + timedelta(days=i)).isoformat(), 0)}
        for i in range(days)
    ]
    log_action(int(get_jwt_identity()), "analytics.v2.patient_inflow", "analytics", None, {"days": days}, request.remote_addr)
    return jsonify(series=series, days=days)

