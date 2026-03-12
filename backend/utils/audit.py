import json
from application.extensions import db
from application.models import AuditLog


def log_action(user_id, action, resource_type=None, resource_id=None, details=None, ip_address=None):
    try:
        payload = None
        if details is not None:
            payload = details if isinstance(details, str) else json.dumps(details, default=str)
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=payload,
            ip_address=ip_address,
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception:
        db.session.rollback()
        return None

