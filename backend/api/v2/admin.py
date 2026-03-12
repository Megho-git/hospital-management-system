from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from application.extensions import db
from application.models import User, Role, Permission, UserRole, RolePermission
from utils.helpers import role_required
from utils.audit import log_action


admin_v2_bp = Blueprint("admin_v2", __name__)


@admin_v2_bp.route("/users/<int:user_id>/roles", methods=["GET"])
@role_required("admin")
def get_user_roles(user_id):
    user = User.query.get_or_404(user_id)
    roles = UserRole.query.filter_by(user_id=user.id).all()
    return jsonify(
        user_id=user.id,
        roles=[
            {"id": ur.role.id, "name": ur.role.name, "description": ur.role.description}
            for ur in roles
            if ur.role
        ],
    )


@admin_v2_bp.route("/users/<int:user_id>/roles", methods=["PUT"])
@role_required("admin")
def set_user_roles(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    role_names = data.get("roles") or []
    if not isinstance(role_names, list):
        return jsonify(msg="roles must be a list"), 400

    roles = Role.query.filter(Role.name.in_([str(r).strip() for r in role_names if str(r).strip()])).all()
    UserRole.query.filter_by(user_id=user.id).delete()
    for r in roles:
        db.session.add(UserRole(user_id=user.id, role_id=r.id))
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.v2.set_user_roles", "user", user.id, {"roles": [r.name for r in roles]}, request.remote_addr)
    return jsonify(msg="ok", roles=[r.name for r in roles])


@admin_v2_bp.route("/roles", methods=["GET"])
@role_required("admin")
def list_roles():
    roles = Role.query.order_by(Role.name.asc()).all()
    return jsonify(
        roles=[
            {"id": r.id, "name": r.name, "description": r.description}
            for r in roles
        ]
    )


@admin_v2_bp.route("/permissions", methods=["GET"])
@role_required("admin")
def list_permissions():
    perms = Permission.query.order_by(Permission.key.asc()).all()
    return jsonify(
        permissions=[
            {"id": p.id, "key": p.key, "description": p.description}
            for p in perms
        ]
    )


@admin_v2_bp.route("/roles/<int:role_id>/permissions", methods=["PUT"])
@role_required("admin")
def set_role_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    data = request.get_json() or {}
    perm_keys = data.get("permissions") or []
    if not isinstance(perm_keys, list):
        return jsonify(msg="permissions must be a list"), 400

    perms = Permission.query.filter(Permission.key.in_([str(k).strip() for k in perm_keys if str(k).strip()])).all()
    RolePermission.query.filter_by(role_id=role.id).delete()
    for p in perms:
        db.session.add(RolePermission(role_id=role.id, permission_id=p.id))
    db.session.commit()
    log_action(int(get_jwt_identity()), "admin.v2.set_role_permissions", "role", role.id, {"permissions": [p.key for p in perms]}, request.remote_addr)
    return jsonify(msg="ok", role=role.name, permissions=[p.key for p in perms])

