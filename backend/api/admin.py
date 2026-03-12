from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import get_jwt_identity
from application.extensions import db, cache
from datetime import datetime
from application.models import User, Doctor, Patient, Department, Appointment, Treatment, Medication, LabTest, Invoice, InvoiceItem
from utils.helpers import (
    role_required, serialize_doctor, serialize_patient,
    serialize_appointment, serialize_user, serialize_invoice,
)
from utils.audit import log_action
from application.models import AuditLog

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/stats", methods=["GET"])
@role_required("admin")
def stats():
    recent = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20).all()
    recent_activity = [
        {
            "id": a.id,
            "user_id": a.user_id,
            "username": a.user.username if a.user else None,
            "action": a.action,
            "resource_type": a.resource_type,
            "resource_id": a.resource_id,
            "details": a.details,
            "ip_address": a.ip_address,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent
    ]
    total_apts = Appointment.query.count()
    completed = Appointment.query.filter_by(status="completed").count()
    completion_rate = round((completed / total_apts) * 100, 2) if total_apts else 0
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    revenue_mtd = sum(
        (inv.total or 0)
        for inv in Invoice.query.filter(Invoice.status == "paid", Invoice.paid_at >= month_start).all()
    )

    return jsonify(
        doctors=Doctor.query.count(),
        patients=Patient.query.count(),
        appointments=total_apts,
        departments=Department.query.count(),
        medications=Medication.query.count(),
        revenue_mtd=revenue_mtd,
        appointment_completion_rate=completion_rate,
        recent_activity=recent_activity,
    )


@admin_bp.route("/doctors", methods=["GET"])
@role_required("admin")
def list_doctors():
    q = request.args.get("q", "")
    query = Doctor.query.join(User)
    if q:
        query = query.filter(
            (User.username.ilike(f"%{q}%")) | (Doctor.specialization.ilike(f"%{q}%"))
        )
    return jsonify([serialize_doctor(d) for d in query.all()])


@admin_bp.route("/doctors", methods=["POST"])
@role_required("admin")
def add_doctor():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify(msg="Username, email, password required"), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(msg="Username or email already exists"), 409

    user = User(
        username=username, email=email,
        password_hash=generate_password_hash(password),
        role="doctor",
    )
    db.session.add(user)
    db.session.flush()

    exp = data.get("experience_years", 0)
    if exp is not None and exp < 0:
        return jsonify(msg="Experience years cannot be negative"), 400
    doctor = Doctor(
        user_id=user.id,
        department_id=data.get("department_id"),
        specialization=data.get("specialization", ""),
        phone=data.get("phone", ""),
        qualification=data.get("qualification", ""),
        experience_years=exp if exp is not None else 0,
    )
    db.session.add(doctor)
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.create_doctor", "doctor", doctor.id, {"username": username}, request.remote_addr)
    cache.delete("doctor_list")
    return jsonify(serialize_doctor(doctor)), 201


@admin_bp.route("/doctors/<int:doc_id>", methods=["PUT"])
@role_required("admin")
def update_doctor(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    data = request.get_json()
    doc.department_id = data.get("department_id", doc.department_id)
    doc.specialization = data.get("specialization", doc.specialization)
    doc.phone = data.get("phone", doc.phone)
    doc.qualification = data.get("qualification", doc.qualification)
    exp = data.get("experience_years")
    if exp is not None:
        if exp < 0:
            return jsonify(msg="Experience years cannot be negative"), 400
        doc.experience_years = exp
    db.session.commit()
    cache.delete("doctor_list")
    return jsonify(serialize_doctor(doc))


@admin_bp.route("/doctors/<int:doc_id>", methods=["DELETE"])
@role_required("admin")
def delete_doctor(doc_id):
    doc = Doctor.query.get_or_404(doc_id)
    if Appointment.query.filter_by(doctor_id=doc.id).first() or Treatment.query.filter_by(doctor_id=doc.id).first():
        return jsonify(msg="Cannot delete doctor with existing appointments or treatments"), 400
    user = doc.user
    db.session.delete(doc)
    db.session.delete(user)
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.delete_doctor", "doctor", doc_id, {"username": user.username}, request.remote_addr)
    cache.delete("doctor_list")
    return jsonify(msg="Doctor deleted")


@admin_bp.route("/patients", methods=["GET"])
@role_required("admin")
def list_patients():
    q = request.args.get("q", "")
    query = Patient.query.join(User)
    if q:
        filters = [
            User.username.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            Patient.phone.ilike(f"%{q}%"),
        ]
        if q.isdigit():
            filters.append(Patient.id == int(q))
        from sqlalchemy import or_
        query = query.filter(or_(*filters))
    return jsonify([serialize_patient(p) for p in query.all()])


@admin_bp.route("/appointments", methods=["GET"])
@role_required("admin")
def list_appointments():
    status = request.args.get("status")
    query = Appointment.query.order_by(Appointment.date.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify([serialize_appointment(a) for a in query.all()])


@admin_bp.route("/users/<int:user_id>/toggle", methods=["PUT"])
@role_required("admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        return jsonify(msg="Cannot deactivate admin"), 400
    user.is_active = not user.is_active
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.toggle_user", "user", user_id, {"is_active": user.is_active}, request.remote_addr)
    return jsonify(serialize_user(user))


@admin_bp.route("/departments", methods=["GET"])
@role_required("admin")
def list_departments():
    return jsonify([{"id": d.id, "name": d.name} for d in Department.query.all()])


@admin_bp.route("/departments", methods=["POST"])
@role_required("admin")
def create_department():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(msg="Department name is required"), 400
    dept = Department(name=name, description=(data.get("description") or "").strip() or None)
    db.session.add(dept)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(msg="Department already exists"), 409
    log_action(int(get_jwt_identity()), "admin.create_department", "department", dept.id, {"name": dept.name}, request.remote_addr)
    cache.delete("dept_list")
    return jsonify(id=dept.id, name=dept.name, description=dept.description or ""), 201


@admin_bp.route("/departments/<int:dept_id>", methods=["PUT"])
@role_required("admin")
def update_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json() or {}
    if data.get("name") is not None:
        dept.name = (data.get("name") or "").strip()
    if data.get("description") is not None:
        dept.description = (data.get("description") or "").strip() or None
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.update_department", "department", dept.id, None, request.remote_addr)
    cache.delete("dept_list")
    return jsonify(id=dept.id, name=dept.name, description=dept.description or "")


@admin_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
@role_required("admin")
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    if Doctor.query.filter_by(department_id=dept.id).first():
        return jsonify(msg="Cannot delete department with doctors"), 400
    db.session.delete(dept)
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.delete_department", "department", dept_id, {"name": dept.name}, request.remote_addr)
    cache.delete("dept_list")
    return jsonify(msg="Department deleted")


@admin_bp.route("/medications", methods=["GET"])
@role_required("admin")
def list_medications():
    q = (request.args.get("q") or "").strip()
    only_active = request.args.get("active", type=int)
    query = Medication.query
    if only_active in (0, 1):
        query = query.filter_by(is_active=bool(only_active))
    if q:
        query = query.filter(
            (Medication.name.ilike(f"%{q}%"))
            | (Medication.generic_name.ilike(f"%{q}%"))
            | (Medication.manufacturer.ilike(f"%{q}%"))
            | (Medication.strength.ilike(f"%{q}%"))
        )
    meds = query.order_by(Medication.is_active.desc(), Medication.name.asc()).all()
    return jsonify([
        {
            "id": m.id,
            "name": m.name,
            "generic_name": m.generic_name,
            "form": m.form,
            "strength": m.strength,
            "manufacturer": m.manufacturer,
            "is_active": m.is_active,
        }
        for m in meds
    ])


@admin_bp.route("/medications", methods=["POST"])
@role_required("admin")
def add_medication():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(msg="Medication name is required"), 400
    med = Medication(
        name=name,
        generic_name=(data.get("generic_name") or "").strip() or None,
        form=(data.get("form") or "").strip() or None,
        strength=(data.get("strength") or "").strip() or None,
        manufacturer=(data.get("manufacturer") or "").strip() or None,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(med)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(msg="Medication already exists (duplicate)"), 409
    log_action(int(get_jwt_identity()), "admin.create_medication", "medication", med.id, {"name": med.name}, request.remote_addr)
    return jsonify(
        id=med.id,
        name=med.name,
        generic_name=med.generic_name,
        form=med.form,
        strength=med.strength,
        manufacturer=med.manufacturer,
        is_active=med.is_active,
    ), 201


@admin_bp.route("/medications/<int:med_id>", methods=["PUT"])
@role_required("admin")
def update_medication(med_id):
    med = Medication.query.get_or_404(med_id)
    data = request.get_json() or {}
    if data.get("name") is not None:
        med.name = (data.get("name") or "").strip()
    if data.get("generic_name") is not None:
        med.generic_name = (data.get("generic_name") or "").strip() or None
    if data.get("form") is not None:
        med.form = (data.get("form") or "").strip() or None
    if data.get("strength") is not None:
        med.strength = (data.get("strength") or "").strip() or None
    if data.get("manufacturer") is not None:
        med.manufacturer = (data.get("manufacturer") or "").strip() or None
    if data.get("is_active") is not None:
        med.is_active = bool(data.get("is_active"))
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.update_medication", "medication", med.id, None, request.remote_addr)
    return jsonify(
        id=med.id,
        name=med.name,
        generic_name=med.generic_name,
        form=med.form,
        strength=med.strength,
        manufacturer=med.manufacturer,
        is_active=med.is_active,
    )


@admin_bp.route("/medications/<int:med_id>", methods=["DELETE"])
@role_required("admin")
def delete_medication(med_id):
    med = Medication.query.get_or_404(med_id)
    db.session.delete(med)
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.delete_medication", "medication", med_id, {"name": med.name}, request.remote_addr)
    return jsonify(msg="Medication deleted")


@admin_bp.route("/lab-tests", methods=["GET"])
@role_required("admin")
def list_lab_tests():
    q = (request.args.get("q") or "").strip()
    only_active = request.args.get("active", type=int)
    query = LabTest.query
    if only_active in (0, 1):
        query = query.filter_by(is_active=bool(only_active))
    if q:
        query = query.filter(
            (LabTest.name.ilike(f"%{q}%"))
            | (LabTest.category.ilike(f"%{q}%"))
            | (LabTest.unit.ilike(f"%{q}%"))
            | (LabTest.normal_range.ilike(f"%{q}%"))
        )
    tests = query.order_by(LabTest.is_active.desc(), LabTest.category.asc(), LabTest.name.asc()).all()
    return jsonify([
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "normal_range": t.normal_range,
            "unit": t.unit,
            "category": t.category,
            "is_active": t.is_active,
        }
        for t in tests
    ])


@admin_bp.route("/lab-tests", methods=["POST"])
@role_required("admin")
def add_lab_test():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify(msg="Lab test name is required"), 400
    t = LabTest(
        name=name,
        description=(data.get("description") or "").strip() or None,
        normal_range=(data.get("normal_range") or "").strip() or None,
        unit=(data.get("unit") or "").strip() or None,
        category=(data.get("category") or "").strip() or None,
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(t)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify(msg="Lab test already exists (duplicate)"), 409
    log_action(int(get_jwt_identity()), "admin.create_lab_test", "lab_test", t.id, {"name": t.name}, request.remote_addr)
    return jsonify(
        id=t.id,
        name=t.name,
        description=t.description,
        normal_range=t.normal_range,
        unit=t.unit,
        category=t.category,
        is_active=t.is_active,
    ), 201


@admin_bp.route("/lab-tests/<int:test_id>", methods=["PUT"])
@role_required("admin")
def update_lab_test(test_id):
    t = LabTest.query.get_or_404(test_id)
    data = request.get_json() or {}
    if data.get("name") is not None:
        t.name = (data.get("name") or "").strip()
    if data.get("description") is not None:
        t.description = (data.get("description") or "").strip() or None
    if data.get("normal_range") is not None:
        t.normal_range = (data.get("normal_range") or "").strip() or None
    if data.get("unit") is not None:
        t.unit = (data.get("unit") or "").strip() or None
    if data.get("category") is not None:
        t.category = (data.get("category") or "").strip() or None
    if data.get("is_active") is not None:
        t.is_active = bool(data.get("is_active"))
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.update_lab_test", "lab_test", t.id, None, request.remote_addr)
    return jsonify(
        id=t.id,
        name=t.name,
        description=t.description,
        normal_range=t.normal_range,
        unit=t.unit,
        category=t.category,
        is_active=t.is_active,
    )


@admin_bp.route("/lab-tests/<int:test_id>", methods=["DELETE"])
@role_required("admin")
def delete_lab_test(test_id):
    t = LabTest.query.get_or_404(test_id)
    db.session.delete(t)
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.delete_lab_test", "lab_test", test_id, {"name": t.name}, request.remote_addr)
    return jsonify(msg="Lab test deleted")


@admin_bp.route("/invoices", methods=["GET"])
@role_required("admin")
def list_invoices():
    status = request.args.get("status")
    q = (request.args.get("q") or "").strip().lower()
    query = Invoice.query.order_by(Invoice.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    invoices = query.all()
    if q:
        invoices = [
            inv for inv in invoices
            if q in (inv.invoice_number or "").lower()
            or q in (inv.patient.user.username if inv.patient and inv.patient.user else "").lower()
        ]
    return jsonify([serialize_invoice(inv) for inv in invoices])


@admin_bp.route("/invoices/<int:invoice_id>", methods=["GET"])
@role_required("admin")
def get_invoice(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    return jsonify(serialize_invoice(inv))


@admin_bp.route("/appointments/<int:apt_id>/invoice", methods=["POST"])
@role_required("admin")
def generate_invoice_for_appointment(apt_id):
    apt = Appointment.query.get_or_404(apt_id)
    inv = Invoice.query.filter_by(appointment_id=apt.id).first()
    if inv:
        return jsonify(serialize_invoice(inv))

    from utils.billing import compute_totals, generate_invoice_number
    consultation_fee = float(request.args.get("consultation_fee") or 500)
    inv = Invoice(
        patient_id=apt.patient_id,
        appointment_id=apt.id,
        status="issued",
        issued_at=datetime.utcnow(),
        tax_percent=float(request.args.get("tax_percent") or 0),
        discount=float(request.args.get("discount") or 0),
    )
    db.session.add(inv)
    db.session.flush()
    inv.invoice_number = generate_invoice_number(inv.id)
    db.session.add(InvoiceItem(
        invoice_id=inv.id,
        description="Consultation Fee",
        item_type="consultation",
        quantity=1,
        unit_price=consultation_fee,
        total_price=round(consultation_fee, 2),
    ))
    totals = compute_totals(consultation_fee, inv.tax_percent, inv.discount)
    inv.subtotal = totals["subtotal"]
    inv.tax_amount = totals["tax_amount"]
    inv.total = totals["total"]
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.generate_invoice", "invoice", inv.id, {"appointment_id": apt_id}, request.remote_addr)
    try:
        from utils.notifications import create_notification
        create_notification(
            user_id=apt.patient.user_id,
            title="Invoice issued",
            message=f"Invoice {inv.invoice_number} has been issued.",
            type="billing",
            link="/patient/billing",
        )
    except Exception:
        pass
    return jsonify(serialize_invoice(inv)), 201


@admin_bp.route("/invoices/<int:invoice_id>/pay", methods=["PUT"])
@role_required("admin")
def mark_invoice_paid(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    if inv.status == "paid":
        return jsonify(serialize_invoice(inv))
    inv.status = "paid"
    inv.paid_at = datetime.utcnow()
    if not inv.issued_at:
        inv.issued_at = datetime.utcnow()
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.mark_invoice_paid", "invoice", invoice_id, None, request.remote_addr)
    return jsonify(serialize_invoice(inv))


@admin_bp.route("/audit-log", methods=["GET"])
@role_required("admin")
def audit_log():
    page = request.args.get("page", type=int) or 1
    per_page = min(request.args.get("per_page", type=int) or 25, 100)
    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter_by(resource_type=resource_type)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify(
        total=total,
        page=page,
        per_page=per_page,
        items=[
            {
                "id": a.id,
                "user_id": a.user_id,
                "username": a.user.username if a.user else None,
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "details": a.details,
                "ip_address": a.ip_address,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
    )


@admin_bp.route("/profile", methods=["GET"])
@role_required("admin")
def get_profile():
    user = User.query.get(int(get_jwt_identity()))
    return jsonify(serialize_user(user))


@admin_bp.route("/profile", methods=["PUT"])
@role_required("admin")
def update_profile():
    user = User.query.get(int(get_jwt_identity()))
    data = request.get_json()
    if data.get("email"):
        user.email = data["email"].strip()
    if data.get("new_password"):
        current = data.get("current_password", "")
        if not current:
            return jsonify(msg="Current password is required"), 400
        if not check_password_hash(user.password_hash, current):
            return jsonify(msg="Current password is incorrect"), 400
        user.password_hash = generate_password_hash(data["new_password"])
    db.session.commit()
    return jsonify(serialize_user(user))


@admin_bp.route("/export/<data_type>", methods=["POST"])
@role_required("admin")
def trigger_export(data_type):
    if data_type not in ("appointments", "doctors", "patients"):
        return jsonify(msg="Invalid export type"), 400
    from tasks.jobs import export_csv
    task = export_csv.delay(data_type)
    return jsonify(task_id=task.id, msg="Export started")


@admin_bp.route("/export/status/<task_id>", methods=["GET"])
@role_required("admin")
def export_status(task_id):
    from tasks.jobs import export_csv
    result = export_csv.AsyncResult(task_id)
    if result.ready():
        return jsonify(status="done", filepath=result.result)
    return jsonify(status="pending")
