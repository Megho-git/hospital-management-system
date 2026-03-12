import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from application.models import Appointment, User
from utils.helpers import role_required
from utils.audit import log_action
from utils.integrations import is_twilio_configured


telemedicine_v2_bp = Blueprint("telemedicine_v2", __name__)


@telemedicine_v2_bp.route("/appointments/<int:appointment_id>/token", methods=["POST"])
@role_required("doctor", "patient", "admin")
def create_video_token(appointment_id):
    """
    Create an appointment-scoped Twilio Video access token.

    If Twilio is not configured, returns 501 with setup hint.
    """
    if not is_twilio_configured():
        return jsonify(msg="Telemedicine not configured", code="TELEMED_NOT_CONFIGURED"), 501

    apt = Appointment.query.get_or_404(appointment_id)
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify(msg="User not found"), 404

    # Patient can only join their own appointment.
    if user.role == "patient":
        if not apt.patient or apt.patient.user_id != user.id:
            return jsonify(msg="Access denied"), 403

    # Doctor can only join their own appointment.
    if user.role == "doctor":
        if not apt.doctor or apt.doctor.user_id != user.id:
            return jsonify(msg="Access denied"), 403

    ttl = int(os.getenv("TELEMED_ROOM_TTL_MINUTES", "60") or "60")
    room_name = f"appointment_{apt.id}"

    from twilio.jwt.access_token import AccessToken
    from twilio.jwt.access_token.grants import VideoGrant

    token = AccessToken(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_API_KEY"),
        os.getenv("TWILIO_API_SECRET"),
        identity=str(user.id),
        ttl=ttl * 60,
    )
    token.add_grant(VideoGrant(room=room_name))

    log_action(int(get_jwt_identity()), "telemedicine.v2.token_issued", "appointment", apt.id, {"room": room_name}, request.remote_addr)
    return jsonify(
        room=room_name,
        expires_at=(datetime.utcnow() + timedelta(minutes=ttl)).isoformat() + "Z",
        token=token.to_jwt().decode("utf-8") if hasattr(token.to_jwt(), "decode") else token.to_jwt(),
    )

