"""
Krishok-Bondhu: Database Initialization & Schema Engine
Initializes SQLite database 'farm_state.db' with 5 tables and realistic baseline seed data.
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "farm_state.db")


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH, force=False):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    if force and os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Plots Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plots (
        plot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_name TEXT NOT NULL,
        location_name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        crop_variety TEXT NOT NULL,
        planting_date TEXT NOT NULL,
        area_bigha REAL NOT NULL
    );
    """)

    # 2. Inventory Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plot_id INTEGER NOT NULL,
        chemical_name TEXT NOT NULL,
        stock_grams REAL NOT NULL,
        rainfastness_hours REAL NOT NULL,
        FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
    );
    """)

    # 3. Disease Scans Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disease_scans (
        scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plot_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        image_path TEXT NOT NULL,
        total_leaf_pixels INTEGER NOT NULL,
        lesion_pixels INTEGER NOT NULL,
        dla_percent REAL NOT NULL,
        irri_grade INTEGER NOT NULL,
        disease_class TEXT NOT NULL,
        confidence REAL NOT NULL,
        iou_score REAL NOT NULL,
        hotspot_quadrant TEXT NOT NULL,
        safety_locked INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
    );
    """)

    # 4. Agent Decisions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_decisions (
        decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plot_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        weather_summary TEXT NOT NULL,
        naive_rule_output TEXT NOT NULL,
        muse_agent_output TEXT NOT NULL,
        reasoning_trace_json TEXT NOT NULL,
        bangla_voice_text TEXT NOT NULL,
        telegram_sent_status TEXT NOT NULL,
        FOREIGN KEY(plot_id) REFERENCES plots(plot_id)
    );
    """)

    # 5. Agronomist Verification Queue
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agronomist_queue (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',
        officer_notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(scan_id) REFERENCES disease_scans(scan_id)
    );
    """)

    conn.commit()

    # Seed Baseline Data if plots is empty
    cursor.execute("SELECT COUNT(*) AS cnt FROM plots")
    if cursor.fetchone()["cnt"] == 0:
        seed_data(cursor)
        conn.commit()
        print("Database initialized and seeded with baseline farm data.")
    else:
        print("Database schema verified (tables already populated).")

    conn.close()


def seed_data(cursor):
    # Planted 28 days ago (Active Tillering Stage)
    planting_date = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Insert Rahim Uddin's Plot in Atrai, Naogaon
    cursor.execute("""
    INSERT INTO plots (plot_id, farmer_name, location_name, lat, lon, crop_variety, planting_date, area_bigha)
    VALUES (1, 'Md. Rahim Uddin', 'Atrai, Naogaon', 24.6133, 88.9515, 'BRRI dhan29', ?, 3.0)
    """, (planting_date,))

    # 2. Insert Farmer's Current Chemical Inventory
    inventory_items = [
        (1, 'Tricyclazole 75 WP', 100.0, 2.5),
        (1, 'Urea Fertilizer', 5000.0, 48.0),
        (1, 'MOP Potash', 2500.0, 12.0)
    ]
    cursor.executemany("""
    INSERT INTO inventory (plot_id, chemical_name, stock_grams, rainfastness_hours)
    VALUES (?, ?, ?, ?)
    """, inventory_items)

    # 3. Seed Realistic Baseline Scan (Grade 5 Blast in NE Quadrant)
    cursor.execute("""
    INSERT INTO disease_scans (
        scan_id, plot_id, timestamp, image_path, total_leaf_pixels, lesion_pixels,
        dla_percent, irri_grade, disease_class, confidence, iou_score, hotspot_quadrant, safety_locked
    ) VALUES (
        1, 1, ?, 'assets/sample_leaves/rice_blast_leaf.jpg',
        425000, 78200, 18.4, 5, 'Rice Blast', 0.924, 0.88, 'North-East', 0
    )
    """, (now_iso,))

    # 4. Seed Baseline Agent Decision
    naive_out = "CANCEL ALL CHEMICAL APPLICATIONS DUE TO 7:00 PM HEAVY RAIN (22mm)."
    muse_out = "CANCEL UREA (leach risk: 48h > 4h dry window); ADVANCE TRICYCLAZOLE 75 WP (28g) SPOT-SPRAY TO 1:00 PM IN NORTH-EAST QUADRANT (2.5h rainfastness < 4h window)."
    bangla_speech = "রহিম ভাই, আজ সন্ধ্যা ৭টায় বৃষ্টি হবে। ইউরিয়া সার দেওয়া বন্ধ রাখুন, কিন্তু ঘরে থাকা ট্রাইসাইক্লাজোল দিয়ে দুপুর ১টায় ধানের পাতার উত্তর-পূর্ব কোণায় মাত্র ২৮ গ্রাম স্পট-স্প্রে করুন।"
    trace_json = '{"dry_window_hours": 4.0, "rain_onset": "19:00", "rainfall_mm": 22.0, "chosen_action": "ADVANCE_SPOT_SPRAY", "chemical_saved_percent": 79.5}'

    cursor.execute("""
    INSERT INTO agent_decisions (
        plot_id, timestamp, weather_summary, naive_rule_output, muse_agent_output,
        reasoning_trace_json, bangla_voice_text, telegram_sent_status
    ) VALUES (
        1, ?, 'Atrai 13:00 dry, 19:00 Heavy Rain 22mm (RH 89%)',
        ?, ?, ?, ?, 'DELIVERED_AUDIO_AND_IMAGE'
    )
    """, (now_iso, naive_out, muse_out, trace_json, bangla_speech))

    # 5. Seed a Sample Agronomist Ticket (from a low-confidence or blurry scan)
    cursor.execute("""
    INSERT INTO agronomist_queue (
        scan_id, reason, status, officer_notes, created_at
    ) VALUES (
        1, 'Demonstration Ticket: Motion-blurred test sample with confidence < 85% safety trigger',
        'PENDING_HUMAN_REVIEW', 'Awaiting Upazila Agriculture Officer confirmation', ?
    )
    """, (now_iso,))


if __name__ == "__main__":
    init_db()
