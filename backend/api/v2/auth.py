from datetime import datetime

import pyotp
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import check_password_hash

from application.extensions import db, limiter
from application.models import User, UserMfa
from utils.helpers import serialize_user
from utils.audit import log_action


auth_v2_bp = Blueprint("auth_v2", __name__)


@auth_v2_bp.route("/login", methods=["POST"])
@limiter.limit("15 per minute")
def login_v2():
    """
    v2 login adds optional MFA challenge.

    Backward compatibility:
    - v1 /api/auth/login remains unchanged.
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    mfa_code = (data.get("mfa_code") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(msg="Invalid credentials"), 401
    if not user.is_active:
        return jsonify(msg="Account is deactivated"), 403

    mfa = UserMfa.query.filter_by(user_id=user.id).first()
    if mfa and mfa.is_enabled:
        if not mfa_code:
            return jsonify(mfa_required=True, msg="MFA code required"), 200
        totp = pyotp.TOTP(mfa.totp_secret)
        if not totp.verify(mfa_code, valid_window=1):
            return jsonify(msg="Invalid MFA code"), 401

    user.last_login_at = datetime.utcnow()
    db.session.commit()
    log_action(user.id, "auth.v2.login", "user", user.id, {"role": user.role}, request.remote_addr)

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    refresh = create_refresh_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, refresh_token=refresh, user=serialize_user(user))


@auth_v2_bp.route("/mfa/setup", methods=["POST"])
@jwt_required()
def mfa_setup():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify(msg="User not found"), 404

    existing = UserMfa.query.filter_by(user_id=user.id).first()
    if existing and existing.is_enabled:
        return jsonify(msg="MFA already enabled"), 409

    secret = pyotp.random_base32()
    if not existing:
        existing = UserMfa(user_id=user.id, totp_secret=secret, is_enabled=False)
        db.session.add(existing)
    else:
        existing.totp_secret = secret
        existing.is_enabled = False
        existing.enabled_at = None

    db.session.commit()
    issuer = current_app.config.get("MFA_ISSUER", "MedFlow HMS")
    otp_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email or user.username, issuer_name=issuer)
    log_action(user.id, "auth.v2.mfa_setup", "user", user.id, None, request.remote_addr)
    return jsonify(
        msg="Scan QR in authenticator app",
        otpauth_uri=otp_uri,
    )


@auth_v2_bp.route("/mfa/verify", methods=["POST"])
@jwt_required()
def mfa_verify():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify(msg="User not found"), 404

    mfa = UserMfa.query.filter_by(user_id=user.id).first()
    if not mfa:
        return jsonify(msg="MFA not set up"), 400

    data = request.get_json() or {}
    code = (data.get("code") or "").strip()
    if not code:
        return jsonify(msg="code required"), 400

    totp = pyotp.TOTP(mfa.totp_secret)
    if not totp.verify(code, valid_window=1):
        return jsonify(msg="Invalid code"), 400

    mfa.is_enabled = True
    mfa.enabled_at = datetime.utcnow()
    db.session.commit()
    log_action(user.id, "auth.v2.mfa_enabled", "user", user.id, None, request.remote_addr)
    return jsonify(msg="MFA enabled")

