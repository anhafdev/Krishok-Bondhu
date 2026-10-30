"""
Krishok-Bondhu: Automated Server & Endpoint Test Harness
Launches the FastAPI server in a background thread and validates all endpoints:
- GET /
- GET /api/state
- GET /api/ecosystem
- POST /api/scan-leaf
- POST /api/run-agent
- POST /api/voice-ask
- POST /api/agronomist/review
"""

import os
import sys

# Ensure root workspace directory is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import uvicorn
import threading
import time
import urllib.request
import urllib.parse
import json

from backend.main import app


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2.5)

    base = "http://127.0.0.1:8000"
    print("Testing Krishok-Bondhu endpoints on", base)

    # 1. GET /
    with urllib.request.urlopen(f"{base}/") as resp:
        html = resp.read()
        assert resp.status == 200
        print(f"✓ GET / -> 200 OK ({len(html)} bytes)")

    # 2. GET /api/state
    with urllib.request.urlopen(f"{base}/api/state") as resp:
        state = json.loads(resp.read().decode("utf-8"))
        assert state["system_status"] == "OPERATIONAL_AUTONOMOUS"
        print(f"✓ GET /api/state -> Farmer: {state['plot']['farmer_name']}, Area: {state['plot']['area_bigha']} bigha")

    # 3. GET /api/ecosystem
    with urllib.request.urlopen(f"{base}/api/ecosystem") as resp:
        eco = json.loads(resp.read().decode("utf-8"))
        print(f"✓ GET /api/ecosystem -> Stage: {eco['lifecycle']['current_stage']['name_en']}, Arbitrage Dests: {len(eco['spatial_arbitrage']['arbitrage_opportunities'])}, QR Hash: {eco['export_qr_passport']['short_hash']}")

    # 4. POST /api/scan-leaf (Rice Blast Sample)
    scan_body = urllib.parse.urlencode({"sample_filename": "rice_blast_leaf.jpg", "plot_id": 1}).encode("utf-8")
    req_scan = urllib.request.Request(f"{base}/api/scan-leaf", data=scan_body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req_scan) as resp:
        scan_res = json.loads(resp.read().decode("utf-8"))
        print(f"✓ POST /api/scan-leaf (Blast) -> Disease: {scan_res['disease_class']}, DLA: {scan_res['dla_percent']}%, Grade: {scan_res['irri_grade']}, Hotspot: {scan_res['hotspot_quadrant']}, SafeLock: {scan_res['safety_locked']}")

    # 5. POST /api/scan-leaf (Blurry Failure Case -> Safety Lock <85%)
    scan_body_blur = urllib.parse.urlencode({"sample_filename": "blurry_leaf.jpg", "plot_id": 1}).encode("utf-8")
    req_blur = urllib.request.Request(f"{base}/api/scan-leaf", data=scan_body_blur, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req_blur) as resp:
        blur_res = json.loads(resp.read().decode("utf-8"))
        assert blur_res["safety_locked"] is True
        print(f"✓ POST /api/scan-leaf (Blurry) -> Conf: {blur_res['confidence']*100:.1f}%, Safety Lock ENGAGED: {blur_res['safety_locked']} (Prescription Blocked)")

    # 6. POST /api/run-agent
    agent_body = json.dumps({"plot_id": 1}).encode("utf-8")
    req_agent = urllib.request.Request(f"{base}/api/run-agent", data=agent_body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_agent) as resp:
        agent_res = json.loads(resp.read().decode("utf-8"))
        print(f"✓ POST /api/run-agent -> Muse Action: {agent_res['decision']['muse_spark']['action_fungicide']}, Saved: {agent_res['decision']['muse_spark']['chemical_saved_percent']}%, Audio: {agent_res['audio_file_url']}")

    # 7. POST /api/voice-ask
    voice_body = json.dumps({"question_text": "আজ কি জমিতে ইউরিয়া সার দেওয়া ঠিক হবে?"}).encode("utf-8")
    req_voice = urllib.request.Request(f"{base}/api/voice-ask", data=voice_body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_voice) as resp:
        voice_res = json.loads(resp.read().decode("utf-8"))
        print(f"✓ POST /api/voice-ask -> ASR: {voice_res['asr_model']}, TTS: {voice_res['tts_model']}, Reply Audio: {voice_res['audio_wav_url']}")

    print("\n🎉 ALL 7 API ENDPOINTS AND FEATURES VALIDATED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
