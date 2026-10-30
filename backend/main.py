"""
Krishok-Bondhu: FastAPI Server & Master REST API Engine
Coordinates Vision Pipeline, Multi-Constraint Agent, Bengali TTS, Telegram Bot,
and Field/National Ecosystem Services for the Krishok-Bondhu Single-Page Dashboard.
"""

import os
import sqlite3
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.vision_pipeline import pipeline_instance
from backend.agent_worker import agent_instance
from backend.bangla_tts import voice_engine, telegram_notifier, voice_assistant
from backend.ecosystem_modules import (
    get_lifecycle_status,
    get_agronomist_queue,
    resolve_agronomist_ticket,
    get_spatial_arbitrage_and_lots,
    generate_qr_passport
)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "farm_state.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(
    title="Krishok-Bondhu API",
    description="Autonomous Spatial Crop-Pathology & Multi-Constraint Field Agent Powered by Meta AI",
    version="2.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Assets & Static Files
os.makedirs(os.path.join(ASSETS_DIR, "audio_out"), exist_ok=True)
os.makedirs(os.path.join(ASSETS_DIR, "sample_leaves"), exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


# Pydantic Schemas
class AgentRunRequest(BaseModel):
    plot_id: int = 1
    weather_override: Optional[Dict[str, Any]] = None


class VoiceAskRequest(BaseModel):
    question_text: str = ""
    plot_id: int = 1


class AgronomistReviewRequest(BaseModel):
    ticket_id: int
    action: str = "approve"  # approve or reject
    officer_notes: str = "Verified by Upazila Agriculture Officer (UAO), Atrai, Naogaon"


# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/")
def serve_dashboard():
    """Serves the Single-Page Modern Interactive Dashboard."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Krishok-Bondhu backend online. Frontend index.html loading..."}


@app.get("/api/state")
def get_farm_state(plot_id: int = 1):
    """Loads all farm plot info, inventory levels, latest scan, decision history, and queue."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Plot
    cur.execute("SELECT * FROM plots WHERE plot_id = ?", (plot_id,))
    plot_row = cur.fetchone()
    plot = dict(plot_row) if plot_row else {}

    # Inventory
    cur.execute("SELECT * FROM inventory WHERE plot_id = ?", (plot_id,))
    inventory = [dict(r) for r in cur.fetchall()]

    # Latest Scan
    cur.execute("SELECT * FROM disease_scans WHERE plot_id = ? ORDER BY scan_id DESC LIMIT 1", (plot_id,))
    latest_scan_row = cur.fetchone()
    latest_scan = dict(latest_scan_row) if latest_scan_row else None

    # Decisions
    cur.execute("SELECT * FROM agent_decisions WHERE plot_id = ? ORDER BY decision_id DESC LIMIT 5", (plot_id,))
    decisions = [dict(r) for r in cur.fetchall()]

    # Pending Tickets Count
    cur.execute("SELECT COUNT(*) AS pending_count FROM agronomist_queue WHERE status = 'PENDING_HUMAN_REVIEW'")
    pending_tickets = cur.fetchone()["pending_count"]

    conn.close()

    return {
        "plot": plot,
        "inventory": inventory,
        "latest_scan": latest_scan,
        "recent_decisions": decisions,
        "pending_tickets_count": pending_tickets,
        "system_status": "OPERATIONAL_AUTONOMOUS"
    }


@app.post("/api/scan-leaf")
async def scan_leaf(
    plot_id: int = Form(1),
    sample_filename: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    3-Stage Spatial Pathology Vision API:
    1. Leaf Isolation via SAM 3.1
    2. Lesion Masking & Spatial Hotspot via SAM 3.1 + CIE-LAB
    3. 4-Class Classifier + <85% Safety Lock & Micro-Dosage
    """
    image_bytes = None
    target_path = None

    if file and file.filename:
        image_bytes = await file.read()
        target_path = f"upload_{file.filename}"
    elif sample_filename:
        target_path = os.path.join(ASSETS_DIR, "sample_leaves", sample_filename)
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail=f"Sample {sample_filename} not found.")
    else:
        # Default to blast sample
        target_path = os.path.join(ASSETS_DIR, "sample_leaves", "rice_blast_leaf.jpg")

    result = pipeline_instance.process_image(
        image_path=target_path,
        image_bytes=image_bytes,
        plot_id=plot_id,
        save_to_db=True
    )
    return result


@app.post("/api/run-agent")
def run_agent(req: AgentRunRequest):
    """
    Multi-Constraint Agronomic Agent API:
    Executes Muse Spark 1.3 / Glimmer 30B agent loop, compares Naive Rule vs AI,
    generates Bengali voice audio (.wav), and delivers alert to Telegram.
    """
    decision = agent_instance.run_agentic_loop(
        plot_id=req.plot_id,
        weather_override=req.weather_override
    )

    # Generate Dynamic Bengali Speech Audio (.wav) via facebook/mms-tts-ben
    bangla_text = decision["bangla_voice_text"]
    audio_path = voice_engine.synthesize_wav(bangla_text)
    audio_filename = os.path.basename(audio_path)
    audio_url = f"/assets/audio_out/{audio_filename}"

    # Autonomous Telegram Delivery
    sample_image = os.path.join(ASSETS_DIR, "sample_leaves", "rice_blast_leaf.jpg")
    telegram_receipt = telegram_notifier.deliver_alert(
        farmer_name="Md. Rahim Uddin",
        bangla_text=bangla_text,
        audio_filepath=audio_path,
        image_filepath=sample_image
    )

    return {
        "decision": decision,
        "audio_file_url": audio_url,
        "telegram_delivery": telegram_receipt
    }


@app.post("/api/voice-ask")
def voice_ask(req: VoiceAskRequest):
    """
    Bengali Voice Assistant API:
    Transcribes question using muse-voice-transcribe-1.0 and generates voice audio.
    """
    result = voice_assistant.process_voice_or_text_question(question_text=req.question_text)
    return result


@app.get("/api/ecosystem")
def get_ecosystem_data(plot_id: int = 1):
    """
    Field & National Ecosystem Services API:
    Returns 90-day lifecycle tracker, agronomist queue, 64-district spatial arbitrage,
    and digital export traceability QR passport.
    """
    lifecycle = get_lifecycle_status(plot_id=plot_id)
    queue = get_agronomist_queue()
    arbitrage = get_spatial_arbitrage_and_lots()
    qr_passport = generate_qr_passport(plot_id=plot_id)

    return {
        "lifecycle": lifecycle,
        "agronomist_queue": queue,
        "spatial_arbitrage": arbitrage,
        "export_qr_passport": qr_passport
    }


@app.post("/api/agronomist/review")
def review_ticket(req: AgronomistReviewRequest):
    """Human-in-the-Loop Agronomist 1-click review/approval."""
    res = resolve_agronomist_ticket(
        ticket_id=req.ticket_id,
        action=req.action,
        officer_notes=req.officer_notes
    )
    return res


@app.get("/api/samples")
def list_samples():
    """Lists available test leaf samples."""
    samples_dir = os.path.join(ASSETS_DIR, "sample_leaves")
    files = []
    if os.path.exists(samples_dir):
        files = os.listdir(samples_dir)
    return {"samples": files}
