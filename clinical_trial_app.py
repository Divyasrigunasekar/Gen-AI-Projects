from flask import Flask, render_template, request, jsonify
from langchain_groq import ChatGroq
import json
import os
from datetime import datetime

app = Flask(__name__)

# Initialize Groq LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    print("⚠️  WARNING: GROQ_API_KEY not set. Set it before running the app.")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=GROQ_API_KEY
)

# ============ MOCK DATA & STORAGE ============
protocols = {}  # {protocol_id: {"criteria": {...}, "created": timestamp}}
decisions = {}  # {decision_id: {full audit trail}}
decision_counter = 0


# ============ LLM FUNCTIONS ============
def extract_protocol_criteria(protocol_text):
    """Extract eligibility criteria from protocol text using LLM"""
    prompt = f"""You are a clinical trial analyst. Extract eligibility criteria from the protocol below.
    Return JSON with keys: inclusion (list), exclusion (list), primary_conditions (list).
    
    Protocol:
    {protocol_text}
    
    Return ONLY valid JSON, no other text."""
    
    try:
        response = llm.invoke(prompt)
        result = response.content.strip()
        return json.loads(result)
    except:
        return {"inclusion": [], "exclusion": [], "primary_conditions": []}


def extract_patient_data(ehr_text):
    """Extract clinical data from EHR text using LLM"""
    prompt = f"""You are a clinical data abstractor. Extract key clinical data from the EHR below.
    Return JSON with keys: age (int), gender (str), conditions (list), medications (list), labs (dict).
    
    EHR:
    {ehr_text}
    
    Return ONLY valid JSON, no other text."""
    
    try:
        response = llm.invoke(prompt)
        result = response.content.strip()
        return json.loads(result)
    except:
        return {"age": 0, "gender": "", "conditions": [], "medications": [], "labs": {}}


def evaluate_eligibility(criteria_json, patient_json):
    """Main eligibility reasoning engine using LLM"""
    # Build a simpler prompt that's easier to parse
    inclusion = "\n".join([f"- {c}" for c in criteria_json.get('inclusion', [])])
    exclusion = "\n".join([f"- {c}" for c in criteria_json.get('exclusion', [])])
    
    prompt = f"""Analyze patient eligibility. Return ONLY valid JSON.

INCLUSION:
{inclusion}

EXCLUSION:
{exclusion}

PATIENT: {json.dumps(patient_json)}

RESPONSE FORMAT (copy this exactly):
{{"score": 85, "recommendation": "ELIGIBLE", "reasoning": ["reason1", "reason2"], "flags": []}}"""
    
    try:
        response = llm.invoke(prompt)
        result = response.content.strip()
        
        print(f"Raw LLM: {result[:100]}")
        
        # Aggressive cleaning
        result = result.replace('```json', '').replace('```', '')
        result = result.strip()
        
        # If it starts with something weird, find the JSON
        if not result.startswith('{'):
            start = result.find('{')
            if start != -1:
                result = result[start:]
        
        # Remove trailing stuff
        if '}' in result:
            end = result.rfind('}') + 1
            result = result[:end]
        
        # Parse it
        parsed = json.loads(result)
        
        # Ensure all fields exist
        parsed.setdefault('score', 50)
        parsed.setdefault('recommendation', 'REQUIRES_REVIEW')
        parsed.setdefault('reasoning', ['No reasoning available'])
        parsed.setdefault('flags', [])
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
        print(f"Failed parsing: {result[:200]}")
        # Return a basic but valid response
        return {
            "score": 50,
            "recommendation": "REQUIRES_REVIEW",
            "reasoning": ["Manual review needed - LLM response format issue"],
            "flags": ["Format error"]
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "score": 0,
            "recommendation": "REQUIRES_REVIEW", 
            "reasoning": [str(e)],
            "flags": ["Processing error"]
        }


def log_decision(protocol_id, patient_name, criteria, patient_data, decision, llm_model="groq/llama-3.1-8b-instant"):
    """Create immutable audit log entry"""
    global decision_counter
    decision_counter += 1
    decision_id = f"DEC-{decision_counter:04d}"
    
    audit_record = {
        "decision_id": decision_id,
        "timestamp": datetime.now().isoformat(),
        "protocol_id": protocol_id,
        "patient_name": patient_name,
        "eligibility_score": decision.get("score", 0),
        "recommendation": decision.get("recommendation", "UNKNOWN"),
        "reasoning_chain": decision.get("reasoning", []),
        "flags": decision.get("flags", []),
        "llm_model_used": llm_model,
        "clinician_review": {"status": "pending", "reviewed_by": None}
    }
    
    decisions[decision_id] = audit_record
    return audit_record


# ============ ROUTES ============

@app.route("/", methods=["GET"])
def index():
    return render_template("clinical_trial.html")


@app.route("/api/upload-protocol", methods=["POST"])
def upload_protocol():
    """Parse and store trial protocol"""
    try:
        data = request.json
        protocol_text = data.get("protocol_text", "")
        protocol_name = data.get("protocol_name", "Protocol")
        
        if not protocol_text:
            return jsonify({"error": "Protocol text required"}), 400
        
        # Extract criteria using LLM
        criteria = extract_protocol_criteria(protocol_text)
        
        # Store protocol
        protocol_id = f"TRIAL-{len(protocols)+1:04d}"
        protocols[protocol_id] = {
            "name": protocol_name,
            "criteria": criteria,
            "raw_text": protocol_text,
            "created": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "protocol_id": protocol_id,
            "extracted_criteria": criteria
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check-eligibility", methods=["POST"])
def check_eligibility():
    """Check patient eligibility against trial protocol"""
    try:
        data = request.json
        protocol_id = data.get("protocol_id")
        ehr_text = data.get("ehr_text", "")
        patient_name = data.get("patient_name", "Patient")
        
        if not protocol_id or protocol_id not in protocols:
            return jsonify({"error": "Protocol not found"}), 400
        
        if not ehr_text:
            return jsonify({"error": "Patient EHR required"}), 400
        
        # Extract patient data
        patient_data = extract_patient_data(ehr_text)
        
        # Get protocol criteria
        protocol = protocols[protocol_id]
        criteria = protocol["criteria"]
        
        # Evaluate eligibility
        decision = evaluate_eligibility(criteria, patient_data)
        
        # Log decision (audit trail)
        audit_record = log_decision(
            protocol_id, 
            patient_name, 
            criteria, 
            patient_data, 
            decision
        )
        
        return jsonify({
            "success": True,
            "decision_id": audit_record["decision_id"],
            "patient_data": patient_data,
            "extracted_criteria": criteria,
            "eligibility_score": decision.get("score"),
            "recommendation": decision.get("recommendation"),
            "reasoning": decision.get("reasoning"),
            "flags": decision.get("flags"),
            "audit_trail": audit_record
        })
    except Exception as e:
        return jsonify({"error": str(e), "trace": str(type(e))}), 500


@app.route("/api/audit-trail/<decision_id>", methods=["GET"])
def get_audit_trail(decision_id):
    """Retrieve immutable audit trail for a decision"""
    if decision_id not in decisions:
        return jsonify({"error": "Decision not found"}), 404
    
    return jsonify(decisions[decision_id])


@app.route("/api/protocols", methods=["GET"])
def list_protocols():
    """List all stored protocols"""
    protocol_list = [
        {
            "protocol_id": pid,
            "name": p["name"],
            "created": p["created"],
            "criteria_count": len(p.get("criteria", {}).get("inclusion", []))
        }
        for pid, p in protocols.items()
    ]
    return jsonify(protocol_list)


@app.route("/api/decisions", methods=["GET"])
def list_decisions():
    """List all decisions with audit trails"""
    decision_list = [
        {
            "decision_id": did,
            "timestamp": d["timestamp"],
            "patient_name": d["patient_name"],
            "protocol_id": d["protocol_id"],
            "recommendation": d["recommendation"],
            "score": d["eligibility_score"]
        }
        for did, d in decisions.items()
    ]
    return jsonify(decision_list)


@app.route("/api/export-audit-report", methods=["GET"])
def export_audit_report():
    """Export all audit logs (compliance report)"""
    return jsonify({
        "report_type": "clinical_trial_audit_log",
        "generated": datetime.now().isoformat(),
        "total_decisions": len(decisions),
        "decisions": list(decisions.values())
    })


if __name__ == "__main__":
    print("=" * 60)
    print("Clinical Trial Eligibility System (LangChain + Flask)")
    print("=" * 60)
    print(f"Groq API configured: {'✓' if GROQ_API_KEY else '✗'}")
    print("Starting server at http://localhost:5004")
    print("=" * 60)
    app.run(debug=True, host="localhost", port=5004)
