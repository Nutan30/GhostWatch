"""
GhostWatch Configuration Module
================================
Centralised settings, paths, thresholds, and credential detection.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")

# ── Paths ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

ASSET_REGISTRY_PATH = DATA_DIR / "asset_registry.csv"
GRIEVANCES_PATH = DATA_DIR / "grievances.csv"

# ── Thresholds ───────────────────────────────────────────────────
CROSS_REF_THRESHOLD = 0.70        # minimum combined similarity for complaint→asset match
ESCALATION_THRESHOLD = 0.75       # minimum confidence to trigger escalation
RAG_TOP_K = 5                     # number of RAG results per query
RAG_SIMILARITY_THRESHOLD = 0.65   # minimum RAG similarity to consider

# ── IBM watsonx credentials ─────────────────────────────────────
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

GRANITE_GUARDIAN_API_KEY = os.getenv("GRANITE_GUARDIAN_API_KEY", "")
GRANITE_GUARDIAN_URL = os.getenv("GRANITE_GUARDIAN_URL", "")

IBM_CREDENTIALS_AVAILABLE = bool(WATSONX_API_KEY and WATSONX_PROJECT_ID)
GUARDIAN_AVAILABLE = bool(GRANITE_GUARDIAN_API_KEY)

# ── Model selection ──────────────────────────────────────────────
LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
IBM_EMBEDDING_MODEL = "ibm/slate-125m-english-rtrvr"

IBM_LLM_MODEL = "ibm/granite-13b-instruct-v2"

# ── Demo mode ────────────────────────────────────────────────────
DEMO_MODE = not IBM_CREDENTIALS_AVAILABLE
