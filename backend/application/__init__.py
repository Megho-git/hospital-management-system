import os
import logging
from flask import Flask, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException
from .config import Config
from .extensions import db, jwt, cors, cache, limiter
from .models import User, Department

DEPARTMENT_DATA = {
    "Cardiology": (
        "Specializes in diagnosing and treating diseases of the heart and "
        "cardiovascular system, including heart failure, arrhythmias, and "
        "coronary artery disease."
    ),
    "Neurology": (
        "Focuses on disorders of the nervous system, including the brain, "
        "spinal cord, and nerves. Treats conditions like epilepsy, stroke, "
        "and multiple sclerosis."
    ),
    "Orthopedics": (
        "Deals with conditions involving the musculoskeletal system \u2014 bones, "
        "joints, ligaments, tendons, and muscles. Covers fractures, arthritis, "
        "and sports injuries."
    ),
    "Pediatrics": (
        "Dedicated to the health and medical care of infants, children, and "
        "adolescents. Covers growth monitoring, vaccinations, and childhood "
        "illnesses."
    ),
    "Dermatology": (
        "Concerned with the diagnosis and treatment of skin, hair, and nail "
        "disorders. Addresses conditions like acne, eczema, psoriasis, and "
        "skin cancer."
    ),
    "General Medicine": (
        "Provides comprehensive primary care for adults, handling a wide range "
        "of acute and chronic conditions, preventive care, and health screenings."
    ),
}


def _setup_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    _setup_logging(app)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True)
    cache.init_app(app)
    limiter.init_app(app)

    from api.auth import auth_bp
    from api.admin import admin_bp
    from api.doctor import doctor_bp
    from api.patient import patient_bp
    from api.notifications import notifications_bp
    from api.v2.auth import auth_v2_bp
    from api.v2.admin import admin_v2_bp
    from api.v2.ehr import ehr_v2_bp
    from api.v2.telemedicine import telemedicine_v2_bp
    from api.v2.messaging import messaging_v2_bp
    from api.v2.rpm import rpm_v2_bp
    from api.v2.analytics import analytics_v2_bp
    from api.v2.pharmacy import pharmacy_v2_bp
    from api.v2.labs import labs_v2_bp
    from api.v2.ai import ai_v2_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(doctor_bp, url_prefix="/api/doctor")
    app.register_blueprint(patient_bp, url_prefix="/api/patient")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(auth_v2_bp, url_prefix="/api/v2/auth")
    app.register_blueprint(admin_v2_bp, url_prefix="/api/v2/admin")
    app.register_blueprint(ehr_v2_bp, url_prefix="/api/v2/ehr")
    app.register_blueprint(telemedicine_v2_bp, url_prefix="/api/v2/telemedicine")
    app.register_blueprint(messaging_v2_bp, url_prefix="/api/v2/messaging")
    app.register_blueprint(rpm_v2_bp, url_prefix="/api/v2/rpm")
    app.register_blueprint(analytics_v2_bp, url_prefix="/api/v2/analytics")
    app.register_blueprint(pharmacy_v2_bp, url_prefix="/api/v2/pharmacy")
    app.register_blueprint(labs_v2_bp, url_prefix="/api/v2/labs")
    app.register_blueprint(ai_v2_bp, url_prefix="/api/v2/ai")

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return jsonify(msg=e.description), e.code

    @app.errorhandler(429)
    def handle_rate_limit(e):
        return jsonify(msg="Too many requests. Please slow down."), 429

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        app.logger.exception("Unhandled exception: %s", e)
        return jsonify(msg="Internal server error"), 500

    with app.app_context():
        db.create_all()
        _migrate_db()
        _seed_admin()
        _seed_departments()

    return app


def _migrate_db():
    """Add new columns to existing tables so existing DBs don't break."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "treatment" in tables:
        cols = [c["name"] for c in inspector.get_columns("treatment")]
        with db.engine.connect() as conn:
            if "medicines" not in cols:
                conn.execute(text("ALTER TABLE treatment ADD COLUMN medicines VARCHAR(500)"))
            if "visit_type" not in cols:
                conn.execute(text("ALTER TABLE treatment ADD COLUMN visit_type VARCHAR(100)"))
            conn.commit()

    if "department" in tables:
        cols = [c["name"] for c in inspector.get_columns("department")]
        with db.engine.connect() as conn:
            if "description" not in cols:
                conn.execute(text("ALTER TABLE department ADD COLUMN description TEXT"))
            conn.commit()

    if "patient" in tables:
        cols = [c["name"] for c in inspector.get_columns("patient")]
        with db.engine.connect() as conn:
            if "allergies" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN allergies TEXT"))
            if "chronic_conditions" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN chronic_conditions TEXT"))
            if "emergency_contact_name" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN emergency_contact_name VARCHAR(100)"))
            if "emergency_contact_phone" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN emergency_contact_phone VARCHAR(20)"))
            if "insurance_id" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN insurance_id VARCHAR(100)"))
            if "insurance_provider" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN insurance_provider VARCHAR(200)"))
            if "height_cm" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN height_cm FLOAT"))
            if "weight_kg" not in cols:
                conn.execute(text("ALTER TABLE patient ADD COLUMN weight_kg FLOAT"))
            conn.commit()

    if "lab_order" in tables:
        cols = [c["name"] for c in inspector.get_columns("lab_order")]
        with db.engine.connect() as conn:
            if "result_file_provider" not in cols:
                conn.execute(text("ALTER TABLE lab_order ADD COLUMN result_file_provider VARCHAR(20)"))
            if "result_file_key" not in cols:
                conn.execute(text("ALTER TABLE lab_order ADD COLUMN result_file_key VARCHAR(500)"))
            conn.commit()

    if "user" in tables:
        cols = [c["name"] for c in inspector.get_columns("user")]
        with db.engine.connect() as conn:
            if "last_login_at" not in cols:
                conn.execute(text("ALTER TABLE user ADD COLUMN last_login_at DATETIME"))
            conn.commit()


def _seed_admin():
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username=os.getenv("ADMIN_USERNAME", "admin"),
            email=os.getenv("ADMIN_EMAIL", "admin@hms.com"),
            password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123")),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


def _seed_departments():
    for name, desc in DEPARTMENT_DATA.items():
        dept = Department.query.filter_by(name=name).first()
        if dept:
            if not dept.description:
                dept.description = desc
        else:
            db.session.add(Department(name=name, description=desc))
    db.session.commit()
