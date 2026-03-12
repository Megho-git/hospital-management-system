"""
Labs v2 API
 - Result file uploads (object store or local)
 - Status history tracking
 - Optional LIS webhook stub
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db
from application.models import (
    User, LabOrder, LabTest, LabOrderStatusHistory, Notification,
    Patient, Doctor,
)
from utils.helpers import role_required, serialize_lab_order
from utils.audit import log_action

labs_v2_bp = Blueprint("labs_v2", __name__)


def _serialize_status_history(h):
    return {
        "id": h.id,
        "old_status": h.old_status,
        "new_status": h.new_status,
        "changed_by_user_id": h.changed_by_user_id,
        "notes": h.notes,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


def _record_status_change(order, new_status, user_id, notes=None):
    old = order.status
    if old == new_status:
        return
    order.status = new_status
    if new_status == "resulted" and not order.resulted_at:
        order.resulted_at = datetime.utcnow()
    db.session.add(LabOrderStatusHistory(
        lab_order_id=order.id,
        old_status=old,
        new_status=new_status,
        changed_by_user_id=user_id,
        notes=notes,
    ))


# ---------- status history ----------

@labs_v2_bp.route("/orders/<int:order_id>/history", methods=["GET"])
@jwt_required()
def order_status_history(order_id):
    order = LabOrder.query.get_or_404(order_id)
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user.role == "patient":
        pat = Patient.query.filter_by(user_id=uid).first()
        if not pat or order.patient_id != pat.id:
            return jsonify(msg="Access denied"), 403
    elif user.role == "doctor":
        doc = Doctor.query.filter_by(user_id=uid).first()
        if not doc or order.doctor_id != doc.id:
            return jsonify(msg="Access denied"), 403

    entries = (
        LabOrderStatusHistory.query
        .filter_by(lab_order_id=order.id)
        .order_by(LabOrderStatusHistory.created_at)
        .all()
    )
    return jsonify([_serialize_status_history(e) for e in entries])


# ---------- result file upload ----------

@labs_v2_bp.route("/orders/<int:order_id>/result-file", methods=["POST"])
@jwt_required()
@role_required("admin", "doctor")
def upload_result_file(order_id):
    order = LabOrder.query.get_or_404(order_id)
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(msg="No file provided"), 400

    uid = int(get_jwt_identity())
    from utils.object_store import put_bytes, StoredObject
    key = f"lab-results/{order.patient_id}/{order.id}/{f.filename}"
    obj: StoredObject = put_bytes(key, f.read(), content_type=f.content_type)
    order.result_file_provider = obj.provider
    order.result_file_key = obj.key

    _record_status_change(order, "resulted", uid, notes="Result file uploaded")

    pat = Patient.query.get(order.patient_id)
    if pat:
        test_name = order.lab_test.name if order.lab_test else "Lab Test"
        db.session.add(Notification(
            user_id=pat.user_id,
            title="Lab Result Available",
            message=f"Result file uploaded for {test_name}.",
        ))

    db.session.commit()
    log_action(uid, "labs.upload_result_file", "lab_order", order.id, {"file": f.filename}, request.remote_addr)
    return jsonify(msg="ok", order=serialize_lab_order(order))


@labs_v2_bp.route("/orders/<int:order_id>/result-file", methods=["GET"])
@jwt_required()
def download_result_file(order_id):
    order = LabOrder.query.get_or_404(order_id)
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user.role == "patient":
        pat = Patient.query.filter_by(user_id=uid).first()
        if not pat or order.patient_id != pat.id:
            return jsonify(msg="Access denied"), 403

    if not order.result_file_key:
        return jsonify(msg="No result file"), 404

    provider = order.result_file_provider or "local"
    if provider == "local":
        from utils.object_store import get_local_path
        path = get_local_path(order.result_file_key)
        if not path:
            return jsonify(msg="File not found on disk"), 404
        return send_file(path, as_attachment=True, download_name=order.result_file_key.split("/")[-1])
    else:
        from utils.object_store import presign_get_url
        url = presign_get_url(order.result_file_key)
        return redirect(url)


# ---------- bulk list with optional filters ----------

@labs_v2_bp.route("/orders", methods=["GET"])
@jwt_required()
def list_orders():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    q = LabOrder.query

    if user.role == "patient":
        pat = Patient.query.filter_by(user_id=uid).first()
        q = q.filter_by(patient_id=pat.id) if pat else q.filter_by(id=-1)
    elif user.role == "doctor":
        doc = Doctor.query.filter_by(user_id=uid).first()
        q = q.filter_by(doctor_id=doc.id) if doc else q.filter_by(id=-1)

    status = request.args.get("status")
    if status:
        q = q.filter_by(status=status)

    orders = q.order_by(LabOrder.ordered_at.desc()).limit(200).all()
    results = []
    for o in orders:
        d = serialize_lab_order(o)
        d["has_result_file"] = bool(o.result_file_key)
        results.append(d)
    return jsonify(results)


# ---------- LIS Webhook Stub ----------

@labs_v2_bp.route("/lis/webhook", methods=["POST"])
def lis_webhook():
    """
    Stub endpoint for external Laboratory Information System integration.
    Accepts a JSON payload with lab_order_id, status, result_value, result_notes.
    NO EXTERNAL SERVICE REQUIRED — this is a passive receiver.
    """
    data = request.get_json(silent=True) or {}
    order_id = data.get("lab_order_id")
    if not order_id:
        return jsonify(msg="lab_order_id required"), 400

    order = LabOrder.query.get(order_id)
    if not order:
        return jsonify(msg="Order not found"), 404

    new_status = data.get("status")
    if new_status and new_status in ("ordered", "collected", "resulted", "cancelled"):
        _record_status_change(order, new_status, user_id=None, notes="LIS webhook update")

    if data.get("result_value") is not None:
        order.result_value = str(data["result_value"])
    if data.get("result_notes") is not None:
        order.result_notes = str(data["result_notes"])

    db.session.commit()

    if new_status == "resulted":
        pat = Patient.query.get(order.patient_id)
        if pat:
            test_name = order.lab_test.name if order.lab_test else "Lab Test"
            db.session.add(Notification(
                user_id=pat.user_id,
                title="Lab Result Available",
                message=f"Result for {test_name} received from lab system.",
            ))
            db.session.commit()

    return jsonify(msg="ok")
