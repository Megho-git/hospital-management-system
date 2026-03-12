from datetime import date, datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from application.extensions import db, limiter
from application.models import User, Patient
from utils.helpers import serialize_user
from utils.audit import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "patient")

    if not username or not email or not password:
        return jsonify(msg="All fields required"), 400
    if role not in ("doctor", "patient"):
        return jsonify(msg="Invalid role"), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(msg="Username or email already exists"), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.flush()

    if role == "patient":
        dob = data.get("date_of_birth")
        db.session.add(Patient(
            user_id=user.id,
            phone=data.get("phone", ""),
            gender=data.get("gender", ""),
            date_of_birth=date.fromisoformat(dob) if dob else None,
            blood_group=data.get("blood_group", ""),
        ))

    db.session.commit()
    log_action(user.id, "auth.register", "user", user.id, {"role": user.role}, request.remote_addr)
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh = create_refresh_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, refresh_token=refresh, user=serialize_user(user)), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("15 per minute")
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(msg="Invalid credentials"), 401
    if not user.is_active:
        return jsonify(msg="Account is deactivated"), 403

    user.last_login_at = datetime.utcnow()
    db.session.commit()
    log_action(user.id, "auth.login", "user", user.id, {"role": user.role}, request.remote_addr)

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh = create_refresh_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, refresh_token=refresh, user=serialize_user(user))


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify(msg="User not found"), 404
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=serialize_user(user))


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify(msg="User not found"), 404
    return jsonify(user=serialize_user(user))
