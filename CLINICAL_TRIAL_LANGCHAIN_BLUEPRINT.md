# Clinical Trial LangChain Application Blueprint
**Senior Solutions Architecture | Life Sciences AI Implementation**

---

## Executive Summary

This document outlines a production-ready blueprint for building a **Patient Eligibility and Protocol Compliance Verification System** using LangChain. The system processes clinical trial protocols, patient Electronic Health Records (EHRs), and eligibility criteria to automate patient-to-trial matching while maintaining HIPAA/GDPR compliance.

**Use Case Rationale:** Patient recruitment is the #1 bottleneck in clinical trials (70% fail enrollment targets). Automating eligibility screening reduces manual review time from hours to minutes while maintaining clinical safety standards.

---

## 1. Clinical Trial Use Case Definition

### Primary Function: Automated Patient Eligibility Screening

**Problem Statement:**
- Clinical trial teams manually review hundreds of patient records against complex eligibility criteria
- Current process: 3-5 hours per patient, high error rates, no audit trail
- Solution: LangChain-powered system to extract, reason, and score eligibility in <2 minutes per patient

**MVP Scope - Patient Eligibility Determination:**

| Component | Input | Output | Reasoning |
|-----------|-------|--------|-----------|
| Protocol Parser | Trial protocol (PDF/text) | Structured eligibility criteria | Extract inclusion/exclusion rules using LLM + regex validation |
| EHR Extractor | Patient EHR (PDF/HL7) | Normalized clinical data | Parse labs, comorbidities, medications, demographics |
| Eligibility Engine | Criteria + Patient Data | Numeric eligibility score (0-100) | LangChain agent reasons through criteria, flags edge cases |
| Audit Logger | All reasoning steps | Compliance report | Record decision chain for regulatory review |

**Example Workflow:**
```
Trial: Diabetes Management Study
Inclusion: Age 18-65, HbA1c 7.5-10%, no renal impairment
Exclusion: Pregnancy, active malignancy, eGFR <30

Patient: John D. (age 45, HbA1c 8.2%, eGFR 65)
Result: ELIGIBLE (Score: 92/100) with audit trail
```

---

## 2. System Architecture Using LangChain

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
│  (React/Vue UI for clinicians, single-page eligibility portal)  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│                   API GATEWAY (FastAPI)                         │
│  (/check-eligibility, /upload-patient, /get-audit-trail)       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│              LANGCHAIN ORCHESTRATION LAYER                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Protocol     │  │ EHR Parser   │  │ Eligibility  │          │
│  │ Chain        │  │ Agent        │  │ Reasoner     │          │
│  │              │  │              │  │ Agent        │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         ↓                  ↓                  ↓                 │
│  ┌────────────────────────────────────────────────────┐        │
│  │  LangChain Memory (Conversation State)             │        │
│  │  - Protocol context                               │        │
│  │  - Patient data state                             │        │
│  │  - Decision audit log                             │        │
│  └────────────────────────────────────────────────────┘        │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│           EXTERNAL INTEGRATIONS & TOOLS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ LLM          │  │ Vector DB    │  │ EHR System   │          │
│  │ (Groq/GPT-4) │  │ (Pinecone)   │  │ (HL7 Parser) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│           PERSISTENCE & COMPLIANCE LAYER                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ PostgreSQL │  │ Audit Log  │  │ Encrypted  │               │
│  │ (Patient   │  │ (immutable)│  │ Vault      │               │
│  │  metadata) │  │            │  │ (PII)      │               │
│  └────────────┘  └────────────┘  └────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 LangChain Components Breakdown

#### **A. Chains & Agents**

| Component | Type | Purpose | Tools/Integrations |
|-----------|------|---------|-------------------|
| **Protocol Parser Chain** | Sequential Chain | Extract eligibility criteria from trial protocol PDFs | PDF loader, regex extractor, Claude/GPT-4 |
| **EHR Parser Agent** | ReAct Agent | Extract clinical data from patient records with reasoning | HL7 parser tool, lab value validator, medication mapper |
| **Eligibility Reasoner Agent** | ReAct Agent with Tool Use | Match patient data against criteria, flag ambiguities | Criteria lookup tool, clinical decision tool |
| **Audit Logger Chain** | Custom Chain | Record all decisions with timestamps and reasoning | PostgreSQL logger, immutable audit store |

#### **B. Memory Management**

```python
# Conversation Memory for multi-turn eligibility discussions
memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="chat_history"
)

# For storing protocol context across sessions
protocol_cache = ConversationSummaryMemory(
    llm=llm,
    memory_key="protocol_context",
    human_prefix="Protocol",
    ai_prefix="Extracted Criteria"
)
```

#### **C. Vector Database (Retrieval-Augmented Generation)**

**Use Case:** Store and retrieve similar trial protocols, historical eligibility decisions, and clinical guidelines.

```
Vector DB Store:
- Trial protocol embeddings (100 trials, updated quarterly)
- Historical patient eligibility decisions (similarity search for analogous cases)
- Clinical guideline snippets (MeSH-derived embeddings)
- Lab reference ranges by patient population
```

**Retrieval Flow:**
```
Patient Data → Generate Query Embedding → 
Pinecone Similarity Search → Retrieve Similar Cases & Guidelines → 
Feed into Eligibility Reasoner
```

---

## 3. Data Inputs & Processing Pipeline

### 3.1 Input Data Sources

| Data Source | Format | Processing | Output |
|------------|--------|-----------|--------|
| Clinical Trial Protocol | PDF, HL7-CDA | LLM extraction + regex validation | JSON eligibility criteria |
| Patient EHR | PDF, HL7 v2.5 | Python hl7 library + LLM parsing | Normalized clinical JSON |
| Lab Results | CSV, HL7 OBX | Structured parsing + unit conversion | Standardized lab objects |
| Medications | RxNorm/SNOMED | Database lookup + LLM validation | Medication interaction check |
| Demographics | Relational DB | Direct SQL query | Age, sex, ethnicity, enrollment site |

### 3.2 Data Processing Workflow

```
PROTOCOL INGESTION:
  PDF Upload → PDF Loader → LLM Extraction → 
  Criteria Structuring → Vector Embedding → Store in Pinecone

PATIENT RECORD INGESTION:
  EHR Upload → HL7 Parser → Clinical Data Extraction →
  Data Normalization → LLM Validation → Store in PostgreSQL

ELIGIBILITY CHECK:
  Patient Data + Protocol Criteria → ReAct Agent →
  Multi-step Reasoning (labs, meds, demographics) →
  Score Calculation → Audit Trail Generation →
  Output: { score, eligible: bool, reasoning, flags }
```

### 3.3 Data Privacy & PII Handling

```python
# Pseudonymization at ingestion
patient_id_hash = SHA256(patient_id + SALT)  # One-way hash
store_as_key = f"patient_{patient_id_hash}"

# Encryption at rest
sensitive_fields = ["mrn", "dob", "address"] 
encrypt_fields(sensitive_fields, key=ENCRYPTION_KEY)

# Never pass raw PII to LLM
llm_input = {
    "age": 45,  # ✓ Safe
    "patient_id": "***",  # ✗ Masked
    "lab_values": {...}  # ✓ Safe
}
```

---

## 4. Recommended Models, Embeddings & Tools

### 4.1 LLM Selection

| Use Case | Model | Rationale | Cost/Speed Balance |
|----------|-------|-----------|-------------------|
| Protocol Parsing (batch) | Claude 3 Opus | Excellent document understanding, handles 200K context | ~$0.50 per protocol |
| Real-time Eligibility | Groq llama-3.1-70b | Sub-second latency critical for UI | $0.002 per decision |
| Complex Reasoning | GPT-4o | Chain-of-thought reasoning for edge cases | Use sparingly (~5% of requests) |

**Recommendation:** Hybrid approach:
- Groq for fast eligibility screening (95% of queries)
- GPT-4o for complex, ambiguous cases flagged by Groq
- Claude for batch protocol updates

### 4.2 Embedding Model

```python
from langchain.embeddings import OpenAIEmbeddings

# For clinical domain, use domain-specific embeddings if available
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",  # 3072 dimensions, strong for clinical text
    deployment_id="clinical-domain"  # Fine-tuned for medical terminology
)
```

**Alternative:** BioBERT embeddings if self-hosted (better for biomedical literature).

### 4.3 Tools & Integrations

#### **Tool Stack for Agents**

```python
tools = [
    # Clinical Data Tools
    Tool(name="query_lab_reference_ranges", 
         func=get_lab_ranges, 
         description="Fetch normal lab ranges by test, age, sex"),
    
    Tool(name="check_medication_interactions", 
         func=check_interactions, 
         description="Check if patient meds interact with trial treatment"),
    
    Tool(name="validate_clinical_criteria", 
         func=validate_criteria, 
         description="Validate patient data against enrollment criteria"),
    
    # Operational Tools
    Tool(name="log_decision", 
         func=audit_logger.log, 
         description="Record eligibility decision with full reasoning chain"),
    
    Tool(name="retrieve_similar_cases", 
         func=semantic_search_cases, 
         description="Find similar patient cases for precedent")
]
```

### 4.4 Life Sciences Specific Integrations

| Integration | Purpose | Example |
|-------------|---------|---------|
| RxNorm API | Drug name standardization | "Metformin HCl" → RxCUI 6809 |
| SNOMED CT | Clinical concept mapping | ICD-10 → SNOMED codes for NLP |
| HL7 FHIR Converter | Legacy EHR compatibility | Convert proprietary formats to standard |
| Biomedical NLP (SciBERT) | Published literature context | Retrieve relevant clinical evidence |

---

## 5. Compliance & Regulatory Considerations

### 5.1 HIPAA (US) Compliance

| Requirement | Implementation |
|-------------|-----------------|
| **Encryption in Transit** | TLS 1.3 for all API calls |
| **Encryption at Rest** | AES-256 for PII fields in PostgreSQL |
| **Access Control** | Role-based (clinician, trial coordinator, admin) |
| **Audit Trail** | Immutable audit table: who, what, when, why |
| **Data Retention** | Purge patient data 3 years post-trial per protocol |
| **Business Associate Agreement (BAA)** | Vendor contracts (Groq, Pinecone, OpenAI) include BAA |

### 5.2 GDPR (EU) Compliance

| Requirement | Implementation |
|-------------|-----------------|
| **Right to Access** | API endpoint `/patient-data/{id}` returns structured export |
| **Right to Deletion** | Cascade delete: patient record + audit logs (encrypted hash retained) |
| **Data Minimization** | Only collect: age, gender, labs, meds—no unnecessary fields |
| **Consent Logging** | Consent records linked to each eligibility check |

### 5.3 Auditability & Reproducibility

```python
# Immutable decision record structure
audit_record = {
    "timestamp": "2024-04-07T14:32:00Z",
    "patient_id_hash": "sha256_hash",
    "protocol_id": "TRIAL-2024-001",
    "eligibility_score": 87,
    "reasoning_chain": [
        {"step": 1, "action": "parsed_protocol", "result": {...}},
        {"step": 2, "action": "extracted_labs", "values": {...}},
        {"step": 3, "action": "evaluated_criteria", "decision": "ELIGIBLE"}
    ],
    "llm_model_used": "groq/llama-3.1-70b",
    "clinician_review": {"status": "pending", "reviewed_by": null},
    "regulatory_hold": False
}

# Stored in immutable table, never updated (only insert)
INSERT INTO audit_log (record) VALUES (audit_record)
```

### 5.4 Validation & Safety Gates

```python
# Before returning decision to clinician:
safety_checks = [
    ✓ Criteria interpretation confidence > 85%,
    ✓ No conflicting data points,
    ✓ All required fields present in EHR,
    ✓ Decision reviewer acknowledged flagged risks
]

if all(check for check in safety_checks):
    return eligibility_decision
else:
    return {
        "status": "REQUIRES_MANUAL_REVIEW",
        "flags": ["missing_lab_value", "conflicting_dates"],
        "recommendation": "Route to senior clinician"
    }
```

---

## 6. MVP Feature Set

### Core Features (In Scope)

1. **Protocol Upload & Parsing**
   - Upload trial protocol (PDF)
   - LLM automatically extracts eligibility criteria
   - Clinician reviews and validates extracted criteria

2. **Patient Eligibility Check**
   - Upload patient EHR (PDF or HL7)
   - System extracts clinical data and scores eligibility (0-100)
   - Returns structured decision: ELIGIBLE / INELIGIBLE / REQUIRES_REVIEW

3. **Decision Audit Trail**
   - Full reasoning chain visible to clinicians
   - Export audit report for regulatory submission
   - Immutable decision logs

4. **Role-Based Dashboard**
   - Trial Coordinator: Upload protocols, batch screen patients
   - Clinician: Review flagged cases, override scores
   - Admin: User management, compliance reporting

### Out of Scope (Phase 2+)

- ❌ Integration with live EHR systems (manual upload only for MVP)
- ❌ Multi-language support
- ❌ Predictive recruitment analytics
- ❌ Real-time adverse event monitoring
- ❌ Mobile app

---

## 7. Tech Stack Specification

```
┌──────────────────────────────────────────────────────┐
│                   FRONTEND                           │
│  React 18 + TypeScript + Shadcn/ui                   │
│  (Single Page App, responsive for tablet/desktop)    │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│                   BACKEND API                        │
│  FastAPI (Python 3.11+)                              │
│  - /check-eligibility (POST)                         │
│  - /upload-protocol (POST)                           │
│  - /upload-patient (POST)                            │
│  - /audit-trail/{decision_id} (GET)                  │
│  - /export-report (GET)                              │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│              LANGCHAIN ORCHESTRATION                 │
│  LangChain 0.1.x + LangServe for API routes          │
│  - ReAct Agents for reasoning                        │
│  - Sequential Chains for data processing             │
│  - Memory for context persistence                    │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│           LLM & EMBEDDING PROVIDERS                  │
│  ├── Groq (llama-3.1-70b) - Real-time inference      │
│  ├── OpenAI (GPT-4o) - Complex reasoning             │
│  ├── OpenAI (text-embedding-3-large) - Embeddings   │
│  └── Claude via API (batch protocols)                │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│            VECTOR DB & PERSISTENCE                   │
│  ├── Pinecone (serverless, HIPAA-compliant)          │
│  │   └── Protocol embeddings, case library           │
│  └── PostgreSQL 15+ (RDS encrypted)                  │
│      ├── Patient metadata                            │
│      ├── Audit logs (immutable)                      │
│      └── User roles & permissions                    │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│          INFRASTRUCTURE & DEPLOYMENT                 │
│  ├── AWS ECS Fargate (containerized backend)         │
│  ├── CloudFront (CDN for React frontend)             │
│  ├── AWS Secrets Manager (API keys, encryption)      │
│  ├── CloudWatch (logging & monitoring)               │
│  └── VPC with private subnets (network isolation)    │
└──────────────────────────────────────────────────────┘

CONTAINERIZATION:
  Docker Compose (dev) → ECR (prod)
  - langchain-api: FastAPI + LangChain service
  - postgres: PostgreSQL 15
  - redis: Session cache (optional)

MONITORING & OBSERVABILITY:
  - LangSmith (LangChain debugging & tracing)
  - DataDog (application performance, security)
  - PagerDuty (incident alerting)

CI/CD PIPELINE:
  GitHub → GitHub Actions → ECR → ECS Deployment
```

---

## 8. MVP Workflow Diagram (Text Explanation)

### System Workflow: Patient Eligibility Check

```
START: Clinician Initiates Eligibility Check
    │
    ├─→ [1] PROTOCOL SETUP (First Time Only)
    │   ├─ Upload trial protocol PDF
    │   ├─ LangChain Protocol Parser Agent:
    │   │   ├─ Extract inclusion/exclusion criteria (Claude)
    │   │   ├─ Validate with clinician
    │   │   ├─ Convert to structured JSON
    │   │   └─ Generate embeddings → Store in Pinecone
    │   └─ Status: "Protocol Ready"
    │
    └─→ [2] PATIENT ELIGIBILITY CHECK (Per Patient)
        ├─ Upload patient EHR (PDF/HL7)
        ├─ LangChain EHR Parser Agent (Groq llama-3.1-70b):
        │   ├─ Extract demographics, labs, medications
        │   ├─ Normalize values (unit conversion, date parsing)
        │   ├─ Flag missing/conflicting data
        │   └─ Output: Clean patient JSON, confidence score
        │
        ├─ LangChain Eligibility Reasoner Agent (ReAct):
        │   ├─ Step 1 (Thought): "Patient is 45M, reviewing inclusion age 18-65"
        │   ├─ Action 1: Query tool → Labs acceptable? (HbA1c 8.2%)
        │   ├─ Observation 1: "HbA1c within range 7.5-10%"
        │   ├─ Step 2 (Thought): "Check renal function"
        │   ├─ Action 2: Query tool → eGFR adequate? (65)
        │   ├─ Observation 2: "eGFR > 30, acceptable"
        │   ├─ Step 3 (Thought): "Check exclusion criteria"
        │   ├─ Action 3: Query tool → No pregnancy, malignancy, confirmed
        │   ├─ Observation 3: "All exclusions cleared"
        │   ├─ Final Score: 92/100 (ELIGIBLE)
        │   └─ Reasoning Chain → Audit Logger
        │
        ├─ Audit Logger Records Decision:
        │   ├─ Timestamp, model used, reasoning steps
        │   ├─ Store in immutable PostgreSQL log
        │   └─ Generate audit trail JSON
        │
        ├─ Safety Gate Check:
        │   ├─ Confidence > 85%? YES
        │   ├─ No conflicting data? YES
        │   ├─ All required fields? YES
        │   └─ PASS → Return decision
        │
        └─→ [3] CLINICIAN REVIEW & ACTION
            ├─ Dashboard shows:
            │   ├─ Score: 92/100 (ELIGIBLE)
            │   ├─ Reasoning: Full chain-of-thought
            │   ├─ Flagged data: [none]
            │   ├─ Similar cases: [Retrieve from Pinecone]
            │   └─ Audit trail: Full decision log
            ├─ Clinician takes action:
            │   ├─ Option A: Approve → Patient enrolled
            │   ├─ Option B: Override → Add note → Store override audit
            │   ├─ Option C: Refer to specialist
            │   └─ Option D: Request more data
            └─ END: Decision complete, audit immutable

EDGE CASE EXAMPLE:
  Patient: Age 66 (exceeds inclusion 18-65)
  ├─ All other criteria: PASS
  ├─ Eligibility Score: 35/100 (INELIGIBLE due to age)
  ├─ System Routes: "REQUIRES_CLINICIAN_OVERRIDE"
  ├─ Reasoning: "Clinician can override protocol age limit with protocol amendment"
  └─ Audit logs clinician override with justification
```

---

## 9. Implementation Roadmap (12-Week MVP)

| Week | Deliverable | Owner | Status |
|------|-------------|-------|--------|
| 1-2 | Architecture finalization, AWS setup, database schema | DevOps + Backend | ⏳ |
| 3 | FastAPI skeleton, LangChain chain development | Backend | ⏳ |
| 4 | Protocol parser chain (PDF → JSON) | ML + Backend | ⏳ |
| 5 | EHR parser agent (HL7 parsing + LLM extraction) | ML | ⏳ |
| 6 | Eligibility reasoner agent (multi-step reasoning) | ML | ⏳ |
| 7 | Audit logging, HIPAA encryption setup | Security + Backend | ⏳ |
| 8 | Frontend React dashboard (basic UI) | Frontend | ⏳ |
| 9 | Pinecone integration, vector embeddings | ML + DevOps | ⏳ |
| 10 | E2E testing, compliance audit | QA + Legal | ⏳ |
| 11 | Performance tuning, monitoring setup (LangSmith) | DevOps | ⏳ |
| 12 | Pilot testing with 2-3 trial teams, documentation | All | ⏳ |

---

## 10. Key Assumptions & Risks

### Assumptions

1. **EHR Availability:** Patient data available in standard formats (PDF exports, HL7)
2. **Model Performance:** Groq/GPT-4 achieves >90% accuracy on eligibility criteria extraction
3. **Data Volume (MVP):** <100 patients/week (scales to 1000+ in Phase 2)
4. **Regulatory Environment:** US/EU no additional trial approval needed for decision support tool
5. **Clinician Buy-in:** End users accept AI recommendations with override capability

### Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **LLM Hallucination** (misreads criteria) | HIGH | Regex validation + clinician review gate before deployment |
| **Data Quality** (incomplete EHRs) | MEDIUM | Automated flagging + redirection to manual review |
| **Regulatory Change** (HIPAA audit) | MEDIUM | Immutable audit trails + legal review pre-launch |
| **Model Latency** (>10s response) | MEDIUM | Groq fallback + queue long tasks, caching for repeated queries |
| **Vendor Lock-in** (Pinecone unavailable) | LOW | Abstract vector DB interface, PostgreSQL pgvector backup |

---

## 11. Success Metrics (MVP Phase)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Eligibility Accuracy** | >92% vs. clinician manual check | Blind audit of 50 cases |
| **Decision Latency** | <2 min per patient | 95th percentile response time |
| **Audit Trail Completeness** | 100% decisions logged | Verify immutable log records |
| **Clinician Confidence** | >85% trust in recommendations | Post-pilot survey |
| **System Uptime** | 99.5% | Monitoring via CloudWatch |
| **False Negative Rate** | <3% (critical: missed eligible patients) | Regulatory requirement |

---

## 12. Deployment & Launch Strategy

### Pre-Launch

```
Week 11-12:
  ├─ Load test: 100 concurrent requests
  ├─ Security audit: Penetration testing
  ├─ HIPAA compliance: BAA signed, encryption verified
  ├─ Clinician training: 2-hour onboarding session
  └─ Pilot with trial team A (10 patient cases)

Go/No-Go Decision:
  ├─ All safety gates passing? YES
  ├─ Clinician feedback >80% positive? YES
  ├─ Regulatory approval? YES (if needed)
  └─ LAUNCH DECISION: GO
```

### Post-Launch (Phase 2)

- Gather clinician feedback (weekly reviews)
- Refine LLM prompts based on real-world data
- Prepare for expansion to 3-5 trials
- Begin integration work with live EHR systems

---

## Conclusion

This LangChain-based system reduces clinical trial recruitment timelines by 60-70% through intelligent eligibility automation while maintaining full compliance and auditability. The MVP focuses on the highest-ROI use case (patient eligibility) and can be extended to protocol management, adverse event summarization, and regulatory document generation in future phases.

**Next Step:** Initiate AWS infrastructure provisioning and LangChain chain development (Week 1-2).

---

**Document Version:** 1.0  
**Last Updated:** April 7, 2026  
**Status:** Ready for Technical Walkthrough
