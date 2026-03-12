"""
AI-assisted tools — gated behind AI_FEATURES_ENABLED env var.

External service: Azure OpenAI (or compatible OpenAI endpoint)
Purpose: prescription suggestions, patient history summarisation, clinical note generation
Environment variables: AI_FEATURES_ENABLED, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_CHAT
Manual setup: Create an Azure OpenAI resource, deploy a chat model, set env vars.
Backend: This file + utils/integrations.py + utils/ai_client.py
Frontend: AI action buttons on doctor dashboard / patient timeline (gracefully hidden when disabled)
"""
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from application.extensions import db
from application.models import (
    User, Patient, Doctor, Treatment, TreatmentMedication,
    Medication, Allergy, Problem, LabOrder,
)
from utils.helpers import role_required
from utils.integrations import is_azure_openai_configured

ai_v2_bp = Blueprint("ai_v2", __name__)


def _ai_disabled_response():
    return jsonify(msg="AI features are not enabled. Set AI_FEATURES_ENABLED=true and configure Azure OpenAI credentials."), 503


def _get_chat_completion(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """Call Azure OpenAI chat completion. Falls back to OpenAI-compatible API."""
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-06-01",
    )
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT")
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _build_patient_context(patient_id: int, max_treatments: int = 10) -> str:
    pat = Patient.query.get(patient_id)
    if not pat:
        return "Patient not found."

    parts = [f"Patient: {pat.user.username if pat.user else 'Unknown'}"]

    allergies = Allergy.query.filter_by(patient_id=patient_id).all()
    if allergies:
        parts.append("Allergies: " + ", ".join(f"{a.substance} ({a.severity or 'unknown severity'})" for a in allergies))

    problems = Problem.query.filter_by(patient_id=patient_id, status="active").all()
    if problems:
        parts.append("Active problems: " + ", ".join(p.title for p in problems))

    treatments = (
        Treatment.query
        .filter_by(patient_id=patient_id)
        .order_by(Treatment.visit_date.desc())
        .limit(max_treatments)
        .all()
    )
    if treatments:
        t_lines = []
        for t in treatments:
            meds = TreatmentMedication.query.filter_by(treatment_id=t.id).all()
            med_str = ", ".join(
                f"{m.medication.name} {m.medication.strength or ''}" for m in meds if m.medication
            ) if meds else (t.medicines or "none")
            t_lines.append(
                f"  - {t.visit_date}: dx={t.diagnosis or 'N/A'}, rx={med_str}, notes={t.notes or 'N/A'}"
            )
        parts.append("Recent treatments:\n" + "\n".join(t_lines))

    recent_labs = (
        LabOrder.query
        .filter_by(patient_id=patient_id)
        .order_by(LabOrder.ordered_at.desc())
        .limit(5)
        .all()
    )
    if recent_labs:
        lab_lines = []
        for lo in recent_labs:
            test_name = lo.lab_test.name if lo.lab_test else "Unknown"
            lab_lines.append(
                f"  - {test_name}: status={lo.status}, result={lo.result_value or 'pending'}"
            )
        parts.append("Recent labs:\n" + "\n".join(lab_lines))

    return "\n".join(parts)


# ---- AI Status ----

@ai_v2_bp.route("/status", methods=["GET"])
@jwt_required()
def ai_status():
    return jsonify(enabled=is_azure_openai_configured())


# ---- Prescription Suggestion ----

@ai_v2_bp.route("/suggest-prescription", methods=["POST"])
@jwt_required()
@role_required("doctor")
def suggest_prescription():
    if not is_azure_openai_configured():
        return _ai_disabled_response()

    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    diagnosis = data.get("diagnosis", "")

    if not patient_id:
        return jsonify(msg="patient_id required"), 400

    context = _build_patient_context(patient_id)

    meds = Medication.query.filter_by(is_active=True).limit(200).all()
    catalog_snippet = "\n".join(
        f"  - id={m.id} {m.name} {m.strength or ''} ({m.form or ''})"
        for m in meds
    )

    system = (
        "You are a clinical decision-support assistant in a hospital management system. "
        "Suggest appropriate medications based on the diagnosis and patient context. "
        "ALWAYS include dose, frequency, duration, and any precautions. "
        "Return ONLY a JSON array of objects: [{\"medication_id\": int, \"name\": str, \"dose\": str, \"frequency\": str, \"duration\": str, \"reason\": str}]. "
        "If you cannot suggest, return an empty array []."
    )
    user_msg = (
        f"Diagnosis: {diagnosis}\n\n"
        f"Patient context:\n{context}\n\n"
        f"Available medications (partial catalog):\n{catalog_snippet}"
    )

    try:
        result = _get_chat_completion(system, user_msg, max_tokens=1024)
        import json
        try:
            suggestions = json.loads(result)
        except json.JSONDecodeError:
            suggestions = result
        return jsonify(suggestions=suggestions)
    except Exception as e:
        return jsonify(msg=f"AI error: {str(e)}"), 502


# ---- Patient History Summary ----

@ai_v2_bp.route("/summarize-history", methods=["POST"])
@jwt_required()
@role_required("doctor")
def summarize_history():
    if not is_azure_openai_configured():
        return _ai_disabled_response()

    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    if not patient_id:
        return jsonify(msg="patient_id required"), 400

    context = _build_patient_context(patient_id, max_treatments=20)

    system = (
        "You are a clinical assistant. Summarise the patient's medical history concisely "
        "for a doctor about to see this patient. Highlight key diagnoses, current medications, "
        "allergies, active problems, and any trends. Be factual and brief (max 300 words)."
    )

    try:
        summary = _get_chat_completion(system, context, max_tokens=600)
        return jsonify(summary=summary)
    except Exception as e:
        return jsonify(msg=f"AI error: {str(e)}"), 502


# ---- Clinical Note Generation ----

@ai_v2_bp.route("/generate-note", methods=["POST"])
@jwt_required()
@role_required("doctor")
def generate_note():
    if not is_azure_openai_configured():
        return _ai_disabled_response()

    data = request.get_json() or {}
    patient_id = data.get("patient_id")
    diagnosis = data.get("diagnosis", "")
    prescription = data.get("prescription", "")
    visit_type = data.get("visit_type", "")
    notes_draft = data.get("notes_draft", "")

    if not patient_id:
        return jsonify(msg="patient_id required"), 400

    context = _build_patient_context(patient_id)

    system = (
        "You are a clinical documentation assistant. Generate a professional SOAP note "
        "(Subjective, Objective, Assessment, Plan) based on the provided encounter details "
        "and patient context. Be thorough but concise."
    )
    user_msg = (
        f"Visit type: {visit_type}\n"
        f"Diagnosis: {diagnosis}\n"
        f"Prescription: {prescription}\n"
        f"Doctor's draft notes: {notes_draft}\n\n"
        f"Patient context:\n{context}"
    )

    try:
        note = _get_chat_completion(system, user_msg, max_tokens=800)
        return jsonify(note=note)
    except Exception as e:
        return jsonify(msg=f"AI error: {str(e)}"), 502
