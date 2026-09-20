# GhostWatch 🛡️
### Detecting Silent Failures in Public Sustainability Infrastructure

**1M1B AI for Sustainability Virtual Internship — IBM SkillsBuild & AICTE**

---

## 🌍 Executive Summary & SDG Alignment

Public investments in green infrastructure—solar streetlights, water ATMs, EV charging stations, and rainwater harvesting units—are central to municipal climate resilience. However, many of these assets **silently fail**: they stop operating without triggering an electrical telemetry alert or formal citizen complaint, remaining broken for months or years while public funds and citizen trust decay.

**GhostWatch** is an Agentic AI system that continuously audits municipal asset registries, maintenance logs, and unstructured citizen grievance streams. By treating the **absence of scheduled maintenance activity** as a primary risk signal and cross-referencing free-text grievances via semantic RAG, GhostWatch flags failing sustainability assets **before** citizens are forced to notice or complain.

### United Nations Sustainable Development Goals (SDGs)
- **Primary: SDG 11 — Sustainable Cities and Communities** (Target 11.2, 11.6, 11.a)
- **Secondary: SDG 9 — Industry, Innovation, and Infrastructure** (Target 9.1, 9.4)
- **Secondary: SDG 12 — Responsible Consumption and Production** (Target 12.7)

---

## 🏛️ System Architecture

GhostWatch is structured as a full-stack platform comprising a modern **React SPA frontend**, a **FastAPI backend API**, and a multi-step agentic pipeline orchestrated with tool abstractions compatible with **IBM watsonx.ai Agent Lab** and **LangGraph**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        React SPA Frontend                       │
│         (Geospatial Map · Audit Table · Evidence Drill-down)    │
└───────────────────────────┬───────────────────────────────────┘
                             │ REST JSON API
┌───────────────────────────▼───────────────────────────────────┐
│                    FastAPI Server (api.py)                      │
│                 (In-Memory Pipeline Cache)                      │
└───────────────────────────┬───────────────────────────────────┘
                             │
┌───────────────────────────▼───────────────────────────────────┐
│                     Agent Orchestrator                          │
│                 (LangGraph / Agent Chain)                       │
│                                                                 │
│  load_asset_registry → retrieve_signals → silence_scorer →      │
│  cross_reference_classifier → generate_flag_report →            │
│  guardrails (hedge/PII) → escalate                              │
└───────┬───────────────┬──────────────┬───────────────┬──────────┘
        │               │              │               │
┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼────────┐
│ Asset        │ │ RAG /       │ │ IBM Granite│ │ IBM Granite   │
│ Registry     │ │ Vector      │ │ Instruct   │ │ Guardian      │
│ (CSV/JSON)   │ │ Store       │ │ (watsonx)  │ │ (Safety/Hedge)│
└──────────────┘ └─────────────┘ └────────────┘ └───────────────┘
```

---

## 🤖 Agent Tool Chain & Workflow

1. `load_asset_registry`: Ingests and validates municipal asset records (install date, service intervals, contractor, warranty dates, location).
2. `retrieve_signals` (RAG): Queries the grievance vector store (ChromaDB / Cosine Vector Store) for semantic complaint signals matching asset type and location.
3. `silence_scorer`: Calculates months since last logged maintenance against expected service intervals. Computes a normalized silence score (0.0 to 1.0) purely on maintenance time gaps.
4. `cross_reference_classifier`: Evaluates retrieved grievances using composite similarity: semantic cosine similarity + ward/street location match + domain keyword alignment.
5. `generate_flag_report`: Synthesizes an evidence-backed audit report with unified confidence score and recommended action (`monitor`, `inspect`, or `escalate`). Supports IBM Granite Instruct models via watsonx.ai with automatic template fallback.
6. `guardrails`: Enforces Responsible AI standards by verifying hedged language, stripping citizen PII, and ensuring cited complaint IDs exist in the retrieved corpus.
7. `escalate`: Generates official municipal inspection recommendation notices for high-confidence flags ($\ge 0.75$), cross-referencing active warranty periods to establish contractor AMC liability vs. municipal public works liability.

---

## ⚖️ Responsible AI Principles (PRD §9)

| Principle | GhostWatch Implementation |
|---|---|
| **Fairness & Equity** | **Independent Silence Scoring**: The `silence_scorer` calculates risk purely from maintenance elapsed time, **never** penalizing low-complaint wards. Underserved neighborhoods with low digital reporting literacy are surfaced for inspection on equal terms. |
| **Strict Hedging** | **Anti-Defamation Guardrails**: The system never asserts failure as an absolute fact (e.g. "Asset is broken"), using strictly hedged terminology (e.g., *"exhibits indications of probable operational failure"*) to prevent erroneous vendor penalties. |
| **Privacy by Design** | **Automated PII Stripping**: Citizen phone numbers, email addresses, Aadhaar numbers, and personal names are sanitized via regex filters at the ingestion layer prior to vector embedding or model inference. |
| **Transparency & Auditability** | **Complete Reasoning Traces**: Every tool invocation, candidate score, duration, and decision threshold is serialized into reproducible JSON traces stored in `logs/trace_<asset_id>_<timestamp>.json`. |

---

## 📁 Repository Structure

```
ghostwatch/
├── api.py                      # FastAPI server (bridges pipeline to React)
├── app.py                      # Streamlit dashboard (alternative frontend)
├── requirements.txt            # Python dependencies
├── .env.example                # IBM watsonx environment template
├── README.md                   # Full documentation & project overview
├── ghostwatch-prd.md           # Product Requirements Document
├── ghostwatch-technical-requirements.md # Technical Specifications
├── frontend/                   # Modern React SPA (Vite + Leaflet)
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── index.css           # Modern dark design system
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── Sidebar.jsx
│   │       ├── KPICards.jsx
│   │       ├── MapView.jsx
│   │       ├── AssetTable.jsx
│   │       ├── EvidenceDrilldown.jsx
│   │       ├── EscalationCenter.jsx
│   │       └── ResponsibleAI.jsx
│   └── dist/                   # Production build
├── data/
│   ├── asset_registry.csv      # 50 municipal sustainability assets
│   └── grievances.csv          # 52 citizen grievance records with PII
├── src/
│   ├── __init__.py
│   ├── config.py               # Settings, paths, thresholds, IBM creds
│   ├── models.py               # Typed dataclasses (Asset, Grievance, etc.)
│   ├── utils.py                # PII stripping, date math, logging, traces
│   ├── data_loader.py          # CSV ingestion with schema validation
│   ├── silence_scorer.py       # Fairness-aware maintenance gap scorer
│   ├── rag.py                  # ChromaDB + In-Memory vector store
│   ├── cross_reference.py      # Semantic & metadata complaint matcher
│   ├── report_generator.py     # Hedged evidence report generator (Granite)
│   ├── guardrails.py           # Safety screening & hallucination defense
│   ├── escalation.py           # Formal inspection notice drafting
│   ├── tools.py                # Standardized tool wrappers
│   └── orchestrator.py         # LangGraph-compatible execution pipeline
├── tests/
│   ├── __init__.py
│   ├── test_silence_scorer.py  # 3 known-broken, 3 working, fairness tests
│   ├── test_cross_reference.py # Similarity threshold & ranking tests
│   ├── test_guardrails.py      # Hedge check, PII, hallucination tests
│   └── test_pipeline.py        # End-to-end integration tests
└── logs/                       # JSON execution traces per asset
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Installation
```bash
# Clone or navigate to the repository
cd ghostwatch

# Install dependencies
pip install -r requirements.txt
```

### 3. IBM watsonx Configuration (Optional)
To connect live IBM Granite foundation models, copy the `.env.example` file and supply your IBM Cloud credentials:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
WATSONX_API_KEY=your-ibm-cloud-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```
*Note: If no IBM credentials are provided, GhostWatch seamlessly operates in **Demo Mode**, utilizing resilient in-memory vector embeddings and deterministic hedged template synthesis.*

### 4. Running the React Application & FastAPI Server

#### Option A: Single Command (FastAPI serves built React SPA)
```bash
python -m uvicorn api:app --port 8000
```
Open your browser at `http://127.0.0.1:8000` to access the full-stack React application and REST endpoints.

#### Option B: Live Development Mode (Vite Hot-Reloading + FastAPI)
```bash
# Terminal 1: Launch FastAPI Backend
python -m uvicorn api:app --port 8000

# Terminal 2: Launch React Dev Server
cd frontend
npm run dev
```
Open `http://localhost:5173`.

#### Option C: Streamlit Dashboard (Alternative Frontend)
```bash
streamlit run app.py
```
Open `http://localhost:8501`.

### 5. Running the Automated Test Suite
```bash
pytest tests/ -v
```
All 20 unit and integration tests validate the silence scorer, cross-reference engine, guardrails, and end-to-end pipeline.

---

## 📊 Evaluation & Verification Results

- **Processing Latency**: 50 municipal assets audited end-to-end in **0.50 seconds** (well under the 5-second PRD requirement).
- **Test Coverage**: **20 passed / 20 tests (100% pass rate)**.
- **Seeded Asset Validation**:
  - `SL-2023-114` (Solar Streetlight, Ward 7): Successfully flagged with 89% confidence, 3 corroborating complaints, and drafted escalation notice.
  - `WA-2023-156` (Water ATM, Ward 10): Flagged with 94% confidence, contractor AMC liability identified.
  - `SL-2026-001` (Solar Streetlight, Ward 1): Correctly categorized as healthy/monitor with 0 overdue maintenance.

---

## 👥 Authors & Acknowledgments

- **Lead Developer**: Antigravity AI & Pair Programmer
- **Program**: 1M1B AI for Sustainability Virtual Internship
- **Partners**: IBM SkillsBuild & AICTE
