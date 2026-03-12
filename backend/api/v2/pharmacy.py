from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db
from application.models import (
    User, DrugItem, StockLot, StockMovement,
    Prescription, PrescriptionItem, DispenseOrder, DispenseItem,
    Treatment, TreatmentMedication, Medication, Notification,
)
from utils.helpers import role_required
from utils.audit import log_action

pharmacy_v2_bp = Blueprint("pharmacy_v2", __name__)


def _serialize_drug_item(di):
    med = di.medication
    total_qty = sum(sl.quantity_on_hand for sl in StockLot.query.filter_by(drug_item_id=di.id).all())
    return {
        "id": di.id,
        "medication_id": di.medication_id,
        "medication_name": med.name if med else None,
        "generic_name": med.generic_name if med else None,
        "form": med.form if med else None,
        "strength": med.strength if med else None,
        "sku": di.sku,
        "reorder_level": di.reorder_level,
        "total_on_hand": total_qty,
        "is_active": di.is_active,
    }


def _serialize_stock_lot(sl):
    return {
        "id": sl.id,
        "drug_item_id": sl.drug_item_id,
        "batch_number": sl.batch_number,
        "expiry_date": sl.expiry_date.isoformat() if sl.expiry_date else None,
        "quantity_on_hand": sl.quantity_on_hand,
        "unit_cost": sl.unit_cost,
        "received_at": sl.received_at.isoformat() if sl.received_at else None,
    }


def _serialize_prescription(rx):
    return {
        "id": rx.id,
        "treatment_id": rx.treatment_id,
        "patient_id": rx.patient_id,
        "doctor_id": rx.doctor_id,
        "status": rx.status,
        "created_at": rx.created_at.isoformat() if rx.created_at else None,
        "items": [
            {
                "id": pi.id,
                "medication_id": pi.medication_id,
                "medication_name": pi.medication.name if pi.medication else None,
                "dose": pi.dose,
                "frequency": pi.frequency,
                "duration": pi.duration,
                "instructions": pi.instructions,
                "quantity": pi.quantity,
            }
            for pi in rx.items
        ],
    }


# --------------- Drug-Item CRUD (admin) ---------------

@pharmacy_v2_bp.route("/drugs", methods=["GET"])
@jwt_required()
@role_required("admin")
def list_drugs():
    q = DrugItem.query.filter_by(is_active=True).order_by(DrugItem.id)
    search = request.args.get("q", "").strip()
    if search:
        q = q.join(Medication).filter(
            Medication.name.ilike(f"%{search}%")
            | Medication.generic_name.ilike(f"%{search}%")
        )
    items = q.all()
    return jsonify([_serialize_drug_item(di) for di in items])


@pharmacy_v2_bp.route("/drugs", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_drug():
    data = request.get_json()
    med = Medication.query.get(data.get("medication_id"))
    if not med:
        return jsonify(msg="Medication not found"), 404
    di = DrugItem(
        medication_id=med.id,
        sku=data.get("sku") or f"SKU-{med.id}",
        reorder_level=data.get("reorder_level", 10),
    )
    db.session.add(di)
    db.session.commit()
    log_action(int(get_jwt_identity()), "pharmacy.drug_created", "drug_item", di.id, {}, request.remote_addr)
    return jsonify(_serialize_drug_item(di)), 201


@pharmacy_v2_bp.route("/drugs/<int:drug_id>", methods=["PATCH"])
@jwt_required()
@role_required("admin")
def update_drug(drug_id):
    di = DrugItem.query.get_or_404(drug_id)
    data = request.get_json()
    if "sku" in data:
        di.sku = data["sku"]
    if "reorder_level" in data:
        di.reorder_level = int(data["reorder_level"])
    if "is_active" in data:
        di.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify(_serialize_drug_item(di))


# --------------- Stock-lot CRUD (admin) ---------------

@pharmacy_v2_bp.route("/drugs/<int:drug_id>/lots", methods=["GET"])
@jwt_required()
@role_required("admin")
def list_lots(drug_id):
    DrugItem.query.get_or_404(drug_id)
    lots = StockLot.query.filter_by(drug_item_id=drug_id).order_by(StockLot.expiry_date).all()
    return jsonify([_serialize_stock_lot(sl) for sl in lots])


@pharmacy_v2_bp.route("/drugs/<int:drug_id>/lots", methods=["POST"])
@jwt_required()
@role_required("admin")
def receive_lot(drug_id):
    DrugItem.query.get_or_404(drug_id)
    data = request.get_json()
    sl = StockLot(
        drug_item_id=drug_id,
        batch_number=data.get("batch_number"),
        expiry_date=date.fromisoformat(data["expiry_date"]) if data.get("expiry_date") else None,
        quantity_on_hand=int(data.get("quantity", 0)),
        unit_cost=float(data.get("unit_cost", 0)),
    )
    db.session.add(sl)
    db.session.flush()
    mv = StockMovement(
        stock_lot_id=sl.id,
        movement_type="in",
        quantity=sl.quantity_on_hand,
        reason="initial receipt",
        actor_user_id=int(get_jwt_identity()),
    )
    db.session.add(mv)
    db.session.commit()
    log_action(int(get_jwt_identity()), "pharmacy.lot_received", "stock_lot", sl.id, {"qty": sl.quantity_on_hand}, request.remote_addr)
    return jsonify(_serialize_stock_lot(sl)), 201


@pharmacy_v2_bp.route("/lots/<int:lot_id>/adjust", methods=["POST"])
@jwt_required()
@role_required("admin")
def adjust_lot(lot_id):
    sl = StockLot.query.get_or_404(lot_id)
    data = request.get_json()
    delta = int(data.get("quantity", 0))
    if sl.quantity_on_hand + delta < 0:
        return jsonify(msg="Resulting quantity would be negative"), 400
    sl.quantity_on_hand += delta
    mv = StockMovement(
        stock_lot_id=sl.id,
        movement_type="adjust",
        quantity=delta,
        reason=data.get("reason", ""),
        actor_user_id=int(get_jwt_identity()),
    )
    db.session.add(mv)
    db.session.commit()
    return jsonify(_serialize_stock_lot(sl))


# --------------- Alerts ---------------

@pharmacy_v2_bp.route("/alerts/low-stock", methods=["GET"])
@jwt_required()
@role_required("admin")
def low_stock_alerts():
    items = DrugItem.query.filter_by(is_active=True).all()
    alerts = []
    for di in items:
        total = sum(sl.quantity_on_hand for sl in StockLot.query.filter_by(drug_item_id=di.id).all())
        if total <= di.reorder_level:
            alerts.append({**_serialize_drug_item(di), "alert": "low_stock"})
    return jsonify(alerts)


@pharmacy_v2_bp.route("/alerts/expiry", methods=["GET"])
@jwt_required()
@role_required("admin")
def expiry_alerts():
    horizon = int(request.args.get("days", 90))
    cutoff = date.today() + timedelta(days=horizon)
    lots = (
        StockLot.query
        .filter(StockLot.quantity_on_hand > 0, StockLot.expiry_date != None, StockLot.expiry_date <= cutoff)
        .order_by(StockLot.expiry_date)
        .all()
    )
    return jsonify([
        {
            **_serialize_stock_lot(sl),
            "drug_item": _serialize_drug_item(DrugItem.query.get(sl.drug_item_id)),
            "alert": "expired" if sl.expiry_date <= date.today() else "expiring_soon",
        }
        for sl in lots
    ])


# --------------- Prescriptions (doctor → pharmacy) ---------------

@pharmacy_v2_bp.route("/prescriptions", methods=["POST"])
@jwt_required()
@role_required("doctor")
def create_prescription():
    """Doctor sends treatment meds to pharmacy as a formal prescription."""
    data = request.get_json()
    treatment_id = data.get("treatment_id")
    treatment = Treatment.query.get_or_404(treatment_id)
    from application.models import Doctor
    doc = Doctor.query.filter_by(user_id=int(get_jwt_identity())).first()
    if not doc or treatment.doctor_id != doc.id:
        return jsonify(msg="Not your treatment"), 403

    existing = Prescription.query.filter_by(treatment_id=treatment_id).first()
    if existing:
        return jsonify(msg="Prescription already exists for this treatment", prescription=_serialize_prescription(existing)), 409

    rx = Prescription(
        treatment_id=treatment.id,
        patient_id=treatment.patient_id,
        doctor_id=doc.id,
        status="sent",
    )
    db.session.add(rx)
    db.session.flush()

    items_data = data.get("items") or []
    if not items_data:
        tms = TreatmentMedication.query.filter_by(treatment_id=treatment.id).all()
        items_data = [
            {"medication_id": tm.medication_id, "dose": tm.dose, "frequency": tm.frequency, "duration": tm.duration, "quantity": 1}
            for tm in tms
        ]

    for it in items_data:
        med = Medication.query.get(it.get("medication_id"))
        if not med:
            continue
        pi = PrescriptionItem(
            prescription_id=rx.id,
            medication_id=med.id,
            dose=it.get("dose"),
            frequency=it.get("frequency"),
            duration=it.get("duration"),
            instructions=it.get("instructions"),
            quantity=int(it.get("quantity", 1)),
        )
        db.session.add(pi)

    admins = User.query.filter_by(role="admin").all()
    for a in admins:
        db.session.add(Notification(user_id=a.id, title="New Prescription",
                                    message=f"Rx #{rx.id} sent to pharmacy by Dr {doc.user.username}"))

    db.session.commit()
    log_action(int(get_jwt_identity()), "pharmacy.rx_created", "prescription", rx.id, {}, request.remote_addr)
    return jsonify(_serialize_prescription(rx)), 201


@pharmacy_v2_bp.route("/prescriptions", methods=["GET"])
@jwt_required()
def list_prescriptions():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    q = Prescription.query
    if user.role == "doctor":
        from application.models import Doctor
        doc = Doctor.query.filter_by(user_id=uid).first()
        q = q.filter_by(doctor_id=doc.id) if doc else q.filter_by(id=-1)
    elif user.role == "patient":
        from application.models import Patient
        pat = Patient.query.filter_by(user_id=uid).first()
        q = q.filter_by(patient_id=pat.id) if pat else q.filter_by(id=-1)

    status_filter = request.args.get("status")
    if status_filter:
        q = q.filter_by(status=status_filter)

    rxs = q.order_by(Prescription.created_at.desc()).all()
    return jsonify([_serialize_prescription(rx) for rx in rxs])


@pharmacy_v2_bp.route("/prescriptions/<int:rx_id>", methods=["GET"])
@jwt_required()
def get_prescription(rx_id):
    rx = Prescription.query.get_or_404(rx_id)
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if user.role == "patient":
        from application.models import Patient
        pat = Patient.query.filter_by(user_id=uid).first()
        if not pat or rx.patient_id != pat.id:
            return jsonify(msg="Access denied"), 403
    elif user.role == "doctor":
        from application.models import Doctor
        doc = Doctor.query.filter_by(user_id=uid).first()
        if not doc or rx.doctor_id != doc.id:
            return jsonify(msg="Access denied"), 403
    return jsonify(_serialize_prescription(rx))


# --------------- Dispensing (admin/pharmacist) ---------------

@pharmacy_v2_bp.route("/prescriptions/<int:rx_id>/dispense", methods=["POST"])
@jwt_required()
@role_required("admin")
def dispense_prescription(rx_id):
    """Fulfil a prescription by deducting stock (FEFO) and creating a dispense order."""
    rx = Prescription.query.get_or_404(rx_id)
    if rx.status in ("fulfilled", "cancelled"):
        return jsonify(msg=f"Prescription already {rx.status}"), 400

    uid = int(get_jwt_identity())
    data = request.get_json() or {}

    dord = DispenseOrder(
        prescription_id=rx.id,
        dispensed_by_user_id=uid,
        notes=data.get("notes"),
    )
    db.session.add(dord)
    db.session.flush()

    all_fulfilled = True
    for pi in rx.items:
        remaining = pi.quantity
        lots = (
            StockLot.query
            .join(DrugItem)
            .filter(DrugItem.medication_id == pi.medication_id, StockLot.quantity_on_hand > 0)
            .order_by(StockLot.expiry_date.asc())
            .all()
        )
        for sl in lots:
            if remaining <= 0:
                break
            take = min(remaining, sl.quantity_on_hand)
            sl.quantity_on_hand -= take
            remaining -= take
            db.session.add(DispenseItem(
                dispense_order_id=dord.id,
                stock_lot_id=sl.id,
                medication_id=pi.medication_id,
                quantity=take,
            ))
            db.session.add(StockMovement(
                stock_lot_id=sl.id,
                movement_type="out",
                quantity=-take,
                reason=f"dispense rx#{rx.id}",
                actor_user_id=uid,
            ))
        if remaining > 0:
            all_fulfilled = False

    rx.status = "fulfilled" if all_fulfilled else "partial"

    from application.models import Patient
    pat = Patient.query.get(rx.patient_id)
    if pat:
        db.session.add(Notification(
            user_id=pat.user_id,
            title="Prescription Dispensed",
            message=f"Rx #{rx.id} has been {'fully' if all_fulfilled else 'partially'} dispensed.",
        ))

    db.session.commit()
    log_action(uid, "pharmacy.dispensed", "dispense_order", dord.id, {"rx_id": rx.id}, request.remote_addr)
    return jsonify(msg="ok", prescription=_serialize_prescription(rx), all_fulfilled=all_fulfilled)
