from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from application.extensions import db
from application.models import (
    Appointment,
    Conversation,
    Message,
    MessageReadReceipt,
    User,
)
from utils.helpers import role_required
from utils.audit import log_action


messaging_v2_bp = Blueprint("messaging_v2", __name__)


def _assert_appointment_member(apt: Appointment, user: User) -> bool:
    if not apt or not user:
        return False
    if user.role == "admin":
        return True
    if user.role == "patient":
        return bool(apt.patient and apt.patient.user_id == user.id)
    if user.role == "doctor":
        return bool(apt.doctor and apt.doctor.user_id == user.id)
    return False


@messaging_v2_bp.route("/appointments/<int:appointment_id>/conversation", methods=["GET"])
@role_required("admin", "doctor", "patient")
def get_or_create_conversation(appointment_id):
    viewer_user_id = int(get_jwt_identity())
    user = User.query.get(viewer_user_id)
    apt = Appointment.query.get_or_404(appointment_id)
    if not _assert_appointment_member(apt, user):
        return jsonify(msg="Access denied"), 403

    conv = Conversation.query.filter_by(appointment_id=apt.id).first()
    if not conv:
        conv = Conversation(
            appointment_id=apt.id,
            patient_id=apt.patient_id,
            doctor_id=apt.doctor_id,
        )
        db.session.add(conv)
        db.session.commit()
        log_action(viewer_user_id, "messaging.v2.conversation_create", "appointment", apt.id, None, request.remote_addr)

    return jsonify(id=conv.id, appointment_id=conv.appointment_id)


@messaging_v2_bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@role_required("admin", "doctor", "patient")
def list_messages(conversation_id):
    viewer_user_id = int(get_jwt_identity())
    user = User.query.get(viewer_user_id)
    conv = Conversation.query.get_or_404(conversation_id)
    apt = Appointment.query.get(conv.appointment_id) if conv.appointment_id else None
    if not apt or not _assert_appointment_member(apt, user):
        return jsonify(msg="Access denied"), 403

    limit = min(request.args.get("limit", type=int) or 50, 200)
    after_id = request.args.get("after_id", type=int)

    query = Message.query.filter_by(conversation_id=conv.id).order_by(Message.id.asc())
    if after_id:
        query = query.filter(Message.id > after_id)
    msgs = query.limit(limit).all()
    return jsonify(items=[
        {
            "id": m.id,
            "sender_user_id": m.sender_user_id,
            "sender_name": m.sender.username if m.sender else None,
            "body": m.body,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ])


@messaging_v2_bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
@role_required("admin", "doctor", "patient")
def send_message(conversation_id):
    viewer_user_id = int(get_jwt_identity())
    user = User.query.get(viewer_user_id)
    conv = Conversation.query.get_or_404(conversation_id)
    apt = Appointment.query.get(conv.appointment_id) if conv.appointment_id else None
    if not apt or not _assert_appointment_member(apt, user):
        return jsonify(msg="Access denied"), 403

    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify(msg="body required"), 400

    msg = Message(conversation_id=conv.id, sender_user_id=user.id, body=body)
    db.session.add(msg)
    db.session.commit()

    # Notify the other participant (in-app notification)
    try:
        from utils.notifications import create_notification
        other_user_id = None
        if user.role == "doctor" and apt.patient:
            other_user_id = apt.patient.user_id
        if user.role == "patient" and apt.doctor:
            other_user_id = apt.doctor.user_id
        if other_user_id:
            create_notification(
                user_id=other_user_id,
                title="New message",
                message=f"New message for appointment #{apt.id}.",
                type="message",
                link=f"/telemedicine/appointments/{apt.id}",
            )
    except Exception:
        pass

    log_action(viewer_user_id, "messaging.v2.message_send", "conversation", conv.id, {"message_id": msg.id}, request.remote_addr)
    return jsonify(id=msg.id), 201


@messaging_v2_bp.route("/messages/<int:message_id>/read", methods=["PUT"])
@role_required("admin", "doctor", "patient")
def mark_message_read(message_id):
    viewer_user_id = int(get_jwt_identity())
    user = User.query.get(viewer_user_id)
    msg = Message.query.get_or_404(message_id)
    conv = Conversation.query.get_or_404(msg.conversation_id)
    apt = Appointment.query.get(conv.appointment_id) if conv.appointment_id else None
    if not apt or not _assert_appointment_member(apt, user):
        return jsonify(msg="Access denied"), 403

    existing = MessageReadReceipt.query.filter_by(message_id=msg.id, user_id=user.id).first()
    if not existing:
        db.session.add(MessageReadReceipt(message_id=msg.id, user_id=user.id))
        db.session.commit()
    return jsonify(msg="ok")

