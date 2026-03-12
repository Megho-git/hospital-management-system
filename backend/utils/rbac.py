from __future__ import annotations

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

from application.models import User, UserRole, RolePermission, Permission


def user_has_permission(user_id: int, permission_key: str) -> bool:
    if not user_id:
        return False
    if not permission_key:
        return False

    # Superuser fallback: keep backward compatibility with existing role claim.
    user = User.query.get(int(user_id))
    if not user or not user.is_active:
        return False
    if user.role == "admin":
        return True

    perm = Permission.query.filter_by(key=permission_key).first()
    if not perm:
        return False

    role_ids = [
        ur.role_id
        for ur in UserRole.query.filter_by(user_id=user.id).all()
    ]
    if not role_ids:
        return False

    return (
        RolePermission.query.filter(
            RolePermission.role_id.in_(role_ids),
            RolePermission.permission_id == perm.id,
        ).first()
        is not None
    )


def permission_required(*permission_keys: str):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            # If permission model not rolled out yet, preserve existing role gating.
            if claims.get("role") == "admin":
                return fn(*args, **kwargs)

            uid = int(get_jwt_identity())
            for key in permission_keys:
                if user_has_permission(uid, key):
                    return fn(*args, **kwargs)
            return jsonify(msg="Access denied"), 403

        return decorated

    return wrapper

