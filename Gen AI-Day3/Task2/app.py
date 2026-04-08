import streamlit as st
import os
import json
from datetime import datetime
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from transformers import pipeline

def append_to_debug_file(step_name: str, action: str, current_state: dict):
    """Utility to append observability traces to a local file."""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "action": action,
            "state_snapshot": current_state
        }
        with open("debugging_report.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        pass # Fail gracefully in the UI


# --- CSS / Aesthetics Setup ---
st.set_page_config(page_title="Sentiment Router App", page_icon="🔀", layout="wide")

st.markdown("""
<style>
    /* Vibrant, premium glassmorphism UI */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #2f1d43 0%, #0f1021 70%);
        background-attachment: fixed;
        color: #F8FAFC;
    }
    /* Add subtle animated colorful orbs in the background */
    .stApp::before {
        content: "";
        position: fixed;
        top: -100px; left: -100px;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(236,72,153,0.3) 0%, transparent 60%);
        border-radius: 50%;
        z-index: -1;
    }
    .stApp::after {
        content: "";
        position: fixed;
        bottom: -150px; right: -50px;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 60%);
        border-radius: 50%;
        z-index: -1;
    }
    
    .header-text {
        font-family: 'Outfit', 'Inter', sans-serif;
        background: linear-gradient(to right, #F472B6, #818CF8, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5em;
        margin-bottom: 0px;
        text-shadow: 0px 4px 15px rgba(244, 114, 182, 0.2);
        animation: fadeIn 1.2s ease-out;
    }
    .sub-header-text {
        font-family: 'Inter', sans-serif;
        color: #CBD5E1;
        margin-top: 5px;
        margin-bottom: 30px;
        font-size: 1.2em;
        font-weight: 300;
    }
    
    /* Interactive Glassmorphism Box */
    .box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 25px;
        margin-top: 15px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .box:hover {
        transform: translateY(-5px) scale(1.02);
        background: rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 40px rgba(129, 140, 248, 0.2);
        border: 1px solid rgba(129, 140, 248, 0.5);
    }
    
    /* Streamlit Input Customization */
    .stTextArea textarea {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        color: #F8FAFC !important;
        border-radius: 12px !important;
        font-size: 1.1em;
        transition: all 0.3s ease;
    }
    .stTextArea textarea:focus {
        border-color: #818CF8 !important;
        box-shadow: 0 0 15px rgba(129, 140, 248, 0.4) !important;
    }
    
    /* Sleek Connective Button */
    .stButton>button {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 20px;
        font-size: 1.1em;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #4F46E5 0%, #9333EA 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(168, 85, 247, 0.5);
        color: white;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:focus {
        outline: none;
        background-color: transparent !important;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# --- State Definition ---
class AgentState(TypedDict):
    query: str
    sentiment: str
    response: str
    history: List[Dict[str, Any]]

# --- Hugging Face Model (Cached to prevent re-downloads on Streamlit re-runs) ---
@st.cache_resource(show_spinner=False)
def load_sentiment_model():
    # Utilizing an optimized roberta model.
    with st.spinner("Downloading/Loading the local HuggingFace Sentiment Analysis Model (takes ~1-3 Mins if first time)..."):
        return pipeline(
            "sentiment-analysis", 
            model="cardiffnlp/twitter-roberta-base-sentiment-latest", 
            truncation=True
        )

# --- Graph Nodes Definition ---
def analyze_sentiment(state: AgentState):
    pipe = load_sentiment_model()
    result = pipe(state['query'])[0]
    label = result['label'].upper() # Outputs 'POSITIVE', 'NEUTRAL', 'NEGATIVE'
    score = result['score']
    
    # Store history for observability
    new_history = state.get("history", [])
    action_desc = f"Classified as {label} (confidence: {score:.2f})"
    new_history.append({
        "node": "Analyze Sentiment",
        "action": action_desc
    })
    
    # Log to Debug File
    append_to_debug_file("Analyze Sentiment", action_desc, {"query": state['query'], "sentiment": label})
    
    return {"sentiment": label, "history": new_history}

def handle_positive(state: AgentState):
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.7)
    prompt = f"The user just left a very positive message: '{state['query']}'. Write a short, warm, and appreciative response thanking them."
    res = llm.invoke(prompt)
    
    new_history = state.get("history", [])
    new_history.append({"node": "Handle Positive", "action": "Generated appreciative response."})
    
    append_to_debug_file("Handle Positive", "Generated appreciative response.", {"response": res.content})
    return {"response": res.content, "history": new_history}

def handle_negative(state: AgentState):
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.7)
    prompt = f"The user is frustrated or upset: '{state['query']}'. Write a professional, empathetic response apologizing and offering to escalate the issue."
    res = llm.invoke(prompt)
    
    new_history = state.get("history", [])
    new_history.append({"node": "Handle Negative", "action": "Generated empathetic escalation response."})
    
    append_to_debug_file("Handle Negative", "Generated empathetic escalation response.", {"response": res.content})
    return {"response": res.content, "history": new_history}

def handle_neutral(state: AgentState):
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.7)
    prompt = f"The user has a general inquiry/neutral message: '{state['query']}'. Write a helpful, standard support response addressing their query."
    res = llm.invoke(prompt)
    
    new_history = state.get("history", [])
    new_history.append({"node": "Handle Neutral", "action": "Generated standard support response."})
    
    append_to_debug_file("Handle Neutral", "Generated standard support response.", {"response": res.content})
    return {"response": res.content, "history": new_history}

# --- Conditional Edge Routing ---
def router(state: AgentState):
    # This acts as our branching logic decision point
    if state["sentiment"] == "POSITIVE":
        return "positive"
    elif state["sentiment"] == "NEGATIVE":
        return "negative"
    else:
        return "neutral"

# --- Build LangGraph ---
def build_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("sentiment_analysis", analyze_sentiment)
    workflow.add_node("positive_handler", handle_positive)
    workflow.add_node("negative_handler", handle_negative)
    workflow.add_node("neutral_handler", handle_neutral)

    # Set Entry Point
    workflow.set_entry_point("sentiment_analysis")

    # Add Conditional Edges
    workflow.add_conditional_edges(
        "sentiment_analysis",
        router,
        {
            "positive": "positive_handler",
            "negative": "negative_handler",
            "neutral": "neutral_handler"
        }
    )

    # Add End Edges
    workflow.add_edge("positive_handler", END)
    workflow.add_edge("negative_handler", END)
    workflow.add_edge("neutral_handler", END)

    return workflow.compile()

# --- Streamlit UI Main ---
def main():
    # Set the API keys securely in the background without UI exposure
    os.environ["GROQ_API_KEY"] = ""
    
    # LangSmith Hardcoded Tracing Config
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_PROJECT"] = "LangGraph_Sentiment_Router"
    os.environ["LANGCHAIN_API_KEY"] = ""

    st.markdown('<p class="header-text">Intelligent Routing System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header-text">Dynamic LangGraph Workflow with Sentiment Branching ⚡</p>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configuration")
        st.success("✅ Secure API Key Loaded (Hidden)")
        
        st.markdown("### 📊 Observability (LangSmith)")
        st.success("✅ LangSmith Tracing Auto-Enabled!")
        
        st.markdown("---")
        st.markdown("""
        **Architecture Overview:**
        1. **Input text** is submitted.
        2. **Hugging Face (`twitter-roberta`)** classifies sentiment.
        3. **LangGraph Router** branches execution.
        4. **Groq LLM** generates specialized response.
        """)
        st.markdown("---")
        st.caption("🚀 Fully automated conditional routing")
        st.caption("📁 Debugs logged to `debugging_report.jsonl`")

    # Interactive Tabs
    tab1, tab2 = st.tabs(["💬 Triage Chat", "🧩 Architecture Trace"])

    with tab1:
        query = st.text_area("Enter your message (e.g. feedback, support ticket):", placeholder="e.g. I absolutely love the new user interface!", height=150)
        
        if st.button("🚀 Process Query", use_container_width=True):
            if not query:
                st.warning("Please enter a query.")
                return
            
            # Pre-load model trigger so the user sees a loading spinner
            load_sentiment_model()

            graph = build_graph()
            initial_state = {"query": query, "sentiment": "", "response": "", "history": []}
            
            try:
                with st.spinner("🧠 LangGraph is conditionally routing your request..."):
                    final_state = graph.invoke(initial_state)

                text_lower = final_state['query'].lower()
                sentiment = final_state['sentiment']
                
                # Emotion mapping based on user request
                emoji = "😐"
                if any(word in text_lower for word in ["hate", "angry", "terrible", "worst", "furious", "mad"]):
                    emoji = "😭"
                elif any(word in text_lower for word in ["sad", "bad", "disappointed"]):
                    emoji = "😞"
                elif any(word in text_lower for word in ["love", "amazing", "heart", "incredible", "perfect"]):
                    emoji = "❤️"
                elif any(word in text_lower for word in ["happy", "good", "great", "nice"]):
                    emoji = "😊"
                else: # Fallback to standard sentiment
                    if sentiment == "POSITIVE": emoji = "😊"
                    elif sentiment == "NEGATIVE": emoji = "😞"

                # Sentiment UI Polish
                if sentiment == "POSITIVE":
                    st.balloons()
                    st.success(f"🎉 Detected Sentiment: **{sentiment}** {emoji}")
                elif sentiment == "NEGATIVE":
                    st.error(f"⚠️ Detected Sentiment: **{sentiment}** {emoji}")
                else:
                    st.warning(f"⚖️ Detected Sentiment: **{sentiment}** {emoji}")

                # Display Final Result
                st.markdown("### 🤖 Agent Response:")
                st.info(final_state["response"], icon=emoji)

                with tab2:
                    st.markdown("### 🔍 Process Observability Trace:")
                    for idx, step in enumerate(final_state["history"]):
                        # Color code nodes based on routing
                        color = "#3182ce" if "Sentiment" in step['node'] else ("#4ECDC4" if "Positive" in step['node'] else ("#FF6B6B" if "Negative" in step['node'] else "#ecc94b"))
                        st.markdown(f"""
                        <div class="box" style="border-left: 4px solid {color}; background-color: rgba(0,0,0,0.3);">
                            <strong>Step {idx+1}: {step['node']}</strong><br>
                            <span style="color:#A0AEC0;">{step['action']}</span>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
