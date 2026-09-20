# Product Requirements Document

## GhostWatch — Detecting Silent Failures in Public Sustainability Infrastructure

**1M1B AI for Sustainability Virtual Internship — IBM SkillsBuild & AICTE**

---

## 1. Overview

**Problem statement:** How might we use AI to detect silently failed public sustainability assets so that municipal infrastructure investment can become more accountable and sustainable?

GhostWatch is an agentic AI system that cross-references municipal asset installation records, citizen grievance data, and maintenance logs to flag public sustainability infrastructure (solar streetlights, water ATMs, EV chargers, rainwater harvesting units) that has silently stopped functioning — without waiting for a formal complaint.

**SDG Alignment**
- **Primary:** SDG 11 — Sustainable Cities and Communities
- **Secondary:** SDG 9 — Industry, Innovation and Infrastructure; SDG 12 — Responsible Consumption and Production

---

## 2. Problem & Opportunity

| | |
|---|---|
| **Who is affected** | Residents losing access to services; municipal bodies wasting maintenance budgets; vendors facing no accountability trigger; public trust in sustainability spending |
| **Current gap** | Grievance systems only capture what citizens bother to report; asset registries record what *should* exist, not what *currently works*; no system treats **absence of maintenance activity** as a risk signal |
| **Why AI is needed** | Requires cross-referencing multiple noisy, unstructured data sources (registries, complaints, news mentions) and reasoning over indirect signals — not a single-query dashboard problem |

---

## 3. Goals & Success Metrics

### Goals
1. Surface silently-failed assets before citizens are forced to notice and complain
2. Give municipalities an evidence-backed, auditable flag — not a bare accusation
3. Demonstrate a working agentic + RAG pipeline suitable for the internship deliverable

### Success metrics (for prototype demo)
- Correctly flags a seeded set of "known broken" test assets with supporting evidence trail
- False-positive rate on "known working" test assets stays low (target: agent hedges confidence appropriately)
- End-to-end trace (input → agent reasoning → flag) is fully visible and explainable

---

## 4. Users & Use Cases

| User | Use case |
|---|---|
| Municipal maintenance officer | Reviews a prioritized list of likely-failed assets instead of scanning the whole city |
| Ward-level administrator | Gets a plain-language report with location, evidence, and recommended action |
| Vendor/contractor (indirect) | Held accountable via warranty-period cross-check when asset fails within contract window |
| Internship evaluator (demo audience) | Sees a transparent agent trace showing reasoning, not just an output |

**Primary user story:** *As a municipal maintenance officer, I want a ranked list of probably-broken public assets with evidence, so I can dispatch inspections without relying on citizens to complain.*

---

## 5. Scope

### In scope (prototype)
- Mock/sample asset registry (type, location, install date, warranty period)
- Mock/sample grievance corpus (text complaints with rough location)
- RAG retrieval over asset records and maintenance contract terms
- Agent pipeline: silence scoring → complaint cross-referencing → flag generation
- Streamlit dashboard with map view and evidence drill-down
- Responsible AI guardrails on flagging language

### Out of scope (for this internship deliverable)
- Live integration with real municipal databases or grievance portals
- Automated dispatch of inspection crews
- Legal/contractual enforcement actions
- Mobile app or citizen-facing reporting interface

---

## 6. Solution Architecture

| Layer | Component |
|---|---|
| Foundation model | IBM Granite instruct model (generation, reasoning) |
| Embeddings | Granite embedding model |
| Vector store | Milvus / Chroma (watsonx.ai vector index) |
| Orchestration | Agentic workflow via watsonx.ai Agent Lab or LangGraph |
| Safety layer | Granite Guardian — enforces hedged, evidence-linked language |
| Frontend | Streamlit dashboard |
| Data | Sample/mock asset registry + grievance corpus (CSV/JSON) |

### Agent tool chain
1. `load_asset_registry` — loads known assets with install date, type, location, expected lifespan, warranty
2. `retrieve_signals` (RAG) — retrieves grievance/news mentions relevant to each asset
3. `silence_scorer` — flags assets past their expected service-check interval with zero maintenance/complaint activity
4. `cross_reference_classifier` — matches vague complaint text to a specific registered asset via embedding similarity
5. `generate_flag_report` — produces evidence-backed, hedged-language flag with confidence score
6. `escalate` — drafts a notice to the relevant department/vendor for high-confidence flags

---

## 7. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | System shall ingest a structured asset registry (type, location, install date, warranty) |
| FR2 | System shall ingest unstructured grievance text and extract location/category signals |
| FR3 | System shall compute a "silence score" based on time-since-install vs. expected maintenance interval |
| FR4 | System shall match grievance text to specific assets using embedding similarity above a confidence threshold |
| FR5 | System shall generate a flag report including: asset ID, confidence level, evidence trail, recommended action |
| FR6 | System shall never assert failure as fact — output language must be hedged (e.g., "likely non-functional") |
| FR7 | Dashboard shall display flagged assets on a map, color-coded by confidence |
| FR8 | Dashboard shall allow drill-down into the evidence trail behind any flag |

---

## 8. Non-Functional Requirements

- **Transparency:** Every output must cite the specific records/complaints behind it
- **Explainability:** Agent reasoning steps must be loggable and displayable in the demo
- **Fairness:** Silence-based scoring must not systematically under-flag low-complaint-density wards (avoid penalizing areas with low reporting literacy)
- **Privacy:** No citizen personal identifiers stored or displayed — only location and complaint text

---

## 9. Responsible AI Considerations

| Principle | Implementation |
|---|---|
| **Fairness** | Silence score weighted independently of complaint volume, to avoid bias toward high-reporting wards |
| **Transparency** | All flags include full evidence trail; no unexplained verdicts |
| **Ethics** | Output framed as inspection recommendation, not confirmed fact; Guardian enforces hedged language |
| **Privacy** | Grievance text processed only for location/asset matching; no citizen identity retained |

---

## 10. Sample Interaction (Prototype Trace)

```
Input: Asset registry entry — Solar streetlight, Ward 7, installed 2023-02,
warranty 3 yrs, last maintenance log: none

Agent reasoning:
1. Installed 19 months ago, zero maintenance logs → silence flag raised
2. Retrieved grievance corpus → 2 complaints near same location mentioning
   "dark street" in past 60 days
3. Cross-reference confidence: 78% same asset
4. Output: "Ward 7 solar streetlight (Asset #SL-2023-114) — likely
   non-functional. No maintenance record in 19 months; 2 nearby grievances
   match location. Recommend inspection. Warranty active until 2026-02."
```

---

## 11. Deliverables (per internship guidelines)

1. **Project description** — title, SDG alignment, problem statement, AI solution overview, target users, Responsible AI considerations, expected impact
2. **Prototype/demo** — agent logic trace + Streamlit dashboard screenshots or flow diagram
3. **Impact statement** — what changes if implemented; who benefits and how

---

## 12. Risks & Open Questions

- **Data availability:** Real asset registries may not be publicly accessible — prototype will use a constructed sample dataset
- **False positives:** Silence alone is a weak signal; needs to be combined with corroborating evidence before escalation
- **Scope of "expected maintenance interval":** Varies by asset type and needs a defensible baseline (manufacturer specs or municipal SLAs)
