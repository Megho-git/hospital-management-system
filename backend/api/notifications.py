from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db
from application.models import Notification
from utils.helpers import role_required


notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    items = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
    unread = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify(
        unread_count=unread,
        items=[
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "link": n.link,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    )


@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notification_id):
    user_id = int(get_jwt_identity())
    n = Notification.query.get_or_404(notification_id)
    if n.user_id != user_id:
        return jsonify(msg="Not your notification"), 403
    n.is_read = True
    db.session.commit()
    return jsonify(msg="ok")


@notifications_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify(msg="ok")

