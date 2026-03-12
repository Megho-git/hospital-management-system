from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity

from application.extensions import db
from application.models import Patient, User, Allergy, Problem, Document
from utils.helpers import role_required
from utils.ehr import build_patient_timeline
from utils.audit import log_action
from utils.object_store import put_bytes, get_local_path, presign_get_url


ehr_v2_bp = Blueprint("ehr_v2", __name__)


@ehr_v2_bp.route("/patients/<int:patient_id>/timeline", methods=["GET"])
@role_required("admin", "doctor", "patient")
def patient_timeline(patient_id):
    """
    Unified patient timeline (computed from existing tables first).

    Access rules:
    - admin: any patient
    - doctor: any patient (current HMS doesn't track doctor-patient assignment beyond appointments)
    - patient: only their own patient_id
    """
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)

    # patient self-access enforcement
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient":
        if not pat.user_id or pat.user_id != viewer.id:
            return jsonify(msg="Access denied"), 403

    limit = min(request.args.get("limit", type=int) or 50, 200)
    offset = max(request.args.get("offset", type=int) or 0, 0)
    items = build_patient_timeline(pat.id, limit=limit, offset=offset)
    log_action(viewer_user_id, "ehr.v2.timeline_read", "patient", pat.id, {"limit": limit, "offset": offset}, request.remote_addr)
    return jsonify(patient_id=pat.id, items=items, limit=limit, offset=offset)


@ehr_v2_bp.route("/patients/<int:patient_id>/allergies", methods=["GET"])
@role_required("admin", "doctor", "patient")
def list_allergies(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403
    items = Allergy.query.filter_by(patient_id=pat.id).order_by(Allergy.created_at.desc()).all()
    log_action(viewer_user_id, "ehr.v2.allergies_read", "patient", pat.id, None, request.remote_addr)
    return jsonify(items=[
        {
            "id": a.id,
            "substance": a.substance,
            "reaction": a.reaction,
            "severity": a.severity,
            "notes": a.notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ])


@ehr_v2_bp.route("/patients/<int:patient_id>/allergies", methods=["POST"])
@role_required("admin", "doctor", "patient")
def create_allergy(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403
    data = request.get_json() or {}
    substance = (data.get("substance") or "").strip()
    if not substance:
        return jsonify(msg="substance required"), 400
    a = Allergy(
        patient_id=pat.id,
        substance=substance,
        reaction=(data.get("reaction") or "").strip() or None,
        severity=(data.get("severity") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(a)
    db.session.commit()
    log_action(viewer_user_id, "ehr.v2.allergy_create", "allergy", a.id, {"patient_id": pat.id}, request.remote_addr)
    return jsonify(id=a.id), 201


@ehr_v2_bp.route("/patients/<int:patient_id>/problems", methods=["GET"])
@role_required("admin", "doctor", "patient")
def list_problems(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403
    items = Problem.query.filter_by(patient_id=pat.id).order_by(Problem.created_at.desc()).all()
    log_action(viewer_user_id, "ehr.v2.problems_read", "patient", pat.id, None, request.remote_addr)
    return jsonify(items=[
        {
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "icd10": p.icd10,
            "notes": p.notes,
            "onset_date": p.onset_date.isoformat() if p.onset_date else None,
            "resolved_date": p.resolved_date.isoformat() if p.resolved_date else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in items
    ])


@ehr_v2_bp.route("/patients/<int:patient_id>/problems", methods=["POST"])
@role_required("admin", "doctor", "patient")
def create_problem(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(msg="title required"), 400
    p = Problem(
        patient_id=pat.id,
        title=title,
        status=(data.get("status") or "active").strip() or "active",
        icd10=(data.get("icd10") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(p)
    db.session.commit()
    log_action(viewer_user_id, "ehr.v2.problem_create", "problem", p.id, {"patient_id": pat.id}, request.remote_addr)
    return jsonify(id=p.id), 201


@ehr_v2_bp.route("/patients/<int:patient_id>/documents", methods=["POST"])
@role_required("admin", "doctor", "patient")
def upload_document(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403

    if "file" not in request.files:
        return jsonify(msg="file required"), 400
    f = request.files["file"]
    raw = f.read()
    if not raw:
        return jsonify(msg="Empty file"), 400

    from flask import current_app
    stored = put_bytes(app_instance_path=current_app.instance_path, content=raw, filename=f.filename)
    doc = Document(
        patient_id=pat.id,
        uploaded_by_user_id=viewer_user_id,
        category=(request.form.get("category") or "medical").strip() or "medical",
        title=(request.form.get("title") or "").strip() or (f.filename or "").strip() or None,
        original_filename=f.filename,
        mime_type=f.mimetype,
        size_bytes=len(raw),
        storage_provider=stored.provider,
        storage_key=stored.key,
    )
    db.session.add(doc)
    db.session.commit()
    log_action(viewer_user_id, "ehr.v2.document_upload", "document", doc.id, {"patient_id": pat.id}, request.remote_addr)
    return jsonify(id=doc.id), 201


@ehr_v2_bp.route("/patients/<int:patient_id>/documents", methods=["GET"])
@role_required("admin", "doctor", "patient")
def list_documents(patient_id):
    viewer_user_id = int(get_jwt_identity())
    pat = Patient.query.get_or_404(patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403

    category = (request.args.get("category") or "").strip().lower()
    query = Document.query.filter_by(patient_id=pat.id)
    if category:
        query = query.filter_by(category=category)
    docs = query.order_by(Document.created_at.desc()).limit(200).all()
    log_action(viewer_user_id, "ehr.v2.documents_list", "patient", pat.id, {"category": category or None}, request.remote_addr)
    return jsonify(items=[
        {
            "id": d.id,
            "category": d.category,
            "title": d.title,
            "original_filename": d.original_filename,
            "mime_type": d.mime_type,
            "size_bytes": d.size_bytes,
            "storage_provider": d.storage_provider,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ])


@ehr_v2_bp.route("/documents/<int:document_id>/download", methods=["GET"])
@role_required("admin", "doctor", "patient")
def download_document(document_id):
    viewer_user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(document_id)
    pat = Patient.query.get(doc.patient_id)
    viewer = User.query.get(viewer_user_id)
    if viewer and viewer.role == "patient" and pat and pat.user_id != viewer.id:
        return jsonify(msg="Access denied"), 403

    from flask import current_app
    log_action(viewer_user_id, "ehr.v2.document_download", "document", doc.id, None, request.remote_addr)

    if doc.storage_provider == "local":
        path = get_local_path(app_instance_path=current_app.instance_path, key=doc.storage_key)
        return send_file(path, as_attachment=True, download_name=doc.original_filename or f"document_{doc.id}")

    # S3/MinIO: return presigned URL for client to download
    url = presign_get_url(key=doc.storage_key, expires_seconds=300)
    if not url:
        return jsonify(msg="Download not available"), 501
    return jsonify(url=url, expires_in=300)

