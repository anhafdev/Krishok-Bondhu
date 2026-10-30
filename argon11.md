# Argon 11: "Krishok-Bondhu" — A-to-Z Project Specification, Features & Complete Backend Architecture

## ১. প্রজেক্টের নাম ও পরিচয় (Project Identity)
- **প্রজেক্টের নাম:** Krishok-Bondhu (কৃষক-বন্ধু)
- **অফিশিয়াল টাইটেল:** Krishok-Bondhu: Autonomous Spatial Crop-Pathology & Multi-Constraint Field Agent Powered by Meta SAM 3.1, Muse Spark 1.3 & Muse Glimmer 30B
- **হ্যাকাথন ট্র্যাক ও থিম:** Indie Developer Track | Theme: Build for Your World + Push the Frontier
- **ডিফল্ট ফিল্ড লোকেশন (জিপিএস):** আত্রাই, নওগাঁ / রাজশাহী বিভাগ (Latitude: 24.6133° N, Longitude: 88.9515° E)

### ব্যবহৃত কোর Meta AI মডেলসমূহ:
1. `sam-3.1` (Meta Segment Anything Model 3.1): পাতা এবং পাতার ক্ষত/দাগ (Lesion) পিক্সেল ধরে সেগমেন্ট করার জন্য।
2. `muse-spark-1.3` (Meta Model API) / `muse-glimmer-30b` (Open-Weights): ৪-মুখী কৃষি ও আবহাওয়া সংকটের লজিক্যাল সিদ্ধান্ত নেওয়ার (Agentic Tool-Calling) জন্য।
3. `facebook/mms-tts-ben` (Meta Massively Multilingual Speech - Bengali): ডায়নামিক বাংলা টেক্সট থেকে অফলাইনে .wav ভয়েস অডিও তৈরি করার জন্য।
4. `muse-voice-transcribe-1.0`: কৃষকের বাংলা ভয়েস প্রশ্নকে টেক্সটে রূপান্তর (ASR) করার জন্য।

---

## ২. প্রজেক্টের ৮টি কোর ও ইকোসিস্টেম ফিচার
- **ফিচার ১:** 3-Stage Spatial Crop-Pathology Vision & Safety Lock (`vision_pipeline.py`)
- **ফিচার ২:** IRRI SES (0–9 Scale) & BRRI-Validated Micro-Dosage Calculator (`irri_dosage.py`)
- **ফিচার ৩:** Multi-Constraint Agronomic Trade-Off Agent (`agent_worker.py`)
- **ফিচার ৪:** 100% Meta Bengali Voice & Autonomous Telegram Delivery (`bangla_tts.py`)
- **ফিচার ৫:** 90-Day Dynamic Lifecycle Tracker (`ecosystem_modules.py`)
- **ফিচার ৬:** Human-in-the-Loop Agronomist Queue (`ecosystem_modules.py`)
- **ফিচার ৭:** 64-District Spatial Arbitrage & Virtual Lot Calculator (`ecosystem_modules.py`)
- **ফিচার ৮:** Digital Export & Traceability QR Passport (`ecosystem_modules.py`)

---

## ৩. ব্যাকএন্ড আর্কিটেকচার ও ডিরেক্টরি স্ট্রাকচার
```
krishok-bondhu/
├── .env                        # Meta API Key, Telegram Bot Token & Chat ID
├── requirements.txt            # Python libraries
├── argon11.md                  # এই মাস্টার স্পেসিফিকেশন ফাইল
├── database/
│   ├── db_init.py              # SQLite ডাটাবেস ও ডেমো ডেটা তৈরির স্ক্রিপ্ট
│   └── farm_state.db           # আসল SQLite Database ফাইল
├── backend/
│   ├── main.py                 # FastAPI সার্ভার ও REST API Endpoints
│   ├── vision_pipeline.py      # SAM 3.1 + CIE-LAB + Classifier + Safety Lock
│   ├── irri_dosage.py          # IRRI SES (0-9 Scale) ও BRRI ডোজ ক্যালকুলেটর
│   ├── agent_worker.py         # Muse Spark 1.3 / Glimmer 30B Agent
│   ├── tools.py                # এজেন্টের ৪টি টুল (Weather, Rainfastness, Inventory, Scan)
│   ├── bangla_tts.py           # Meta Bengali Voice & Telegram Delivery
│   └── ecosystem_modules.py    # Lifecycle, Queue, Arbitrage, QR Passport
├── assets/
│   ├── sample_leaves/          # টেস্ট করার জন্য ৫টি ধানের পাতার ছবি
│   └── audio_out/              # জেনারেট হওয়া বাংলা .wav ফাইল
└── frontend/
    └── index.html              # সিঙ্গেল-পেজ ইন্টারঅ্যাক্টিভ ড্যাশবোর্ড
```
