import streamlit as st
import os
import time

st.set_page_config(page_title="Real Estate Insight AI", page_icon="🏢", layout="wide")

# Custom CSS for a colourful and reactive UI
st.markdown("""
<style>
/* Custom background, typography, and button specs */
.stApp {
    background-color: #f7f9fc;
    color: #1f2937;
}
.title-container {
    padding: 2rem;
    border-radius: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.stTextInput > div > div > input {
    border-radius: 8px;
    border: 2px solid #cbd5e1;
}
.stButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    font-weight: bold;
    border-radius: 8px;
    border: none;
    padding: 0.5rem 2rem;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}
.agent-step {
    padding: 1.5rem;
    border-radius: 10px;
    background: white;
    border-left: 4px solid;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    animation: fadeIn 0.5s ease-in-out;
}
.agent-researcher { border-left-color: #3b82f6; }
.agent-writer { border-left-color: #f59e0b; }
.agent-editor { border-left-color: #10b981; }

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-container"><h1>🏢 Real Estate Intelligence Multi-Agent System</h1><p>Researcher → Writer → Editor pipeline powered by LangGraph, ChromaDB & Groq</p></div>', unsafe_allow_html=True)

# Automatically set the provided API Key
os.environ["GROQ_API_KEY"] = ""

query = st.text_input("Enter your real estate research query:", placeholder="e.g., Analyze the ROI potential and risks for commercial properties in Austin")

if st.button("Generate Report") and query:
        from pipeline import build_graph
        try:
            with st.spinner("Initializing Pipeline..."):
                graph = build_graph()
            
            st.markdown("### ⚙️ Pipeline Execution")
            
            report_container = st.empty()
            
            # Use streaming to get step-by-step updates
            for event in graph.stream({"query": query}):
                for node_name, state_update in event.items():
                    step_name = state_update.get("current_step", "")
                    
                    if step_name == "researcher":
                        st.markdown(f"""
                        <div class="agent-step agent-researcher">
                            <h4>🔍 Researcher Agent Active</h4>
                            <p>Searched vector database (ChromaDB) for market context.</p>
                            <details><summary>View Context Retrieved</summary>
                            <pre style="white-space: pre-wrap;">{state_update.get('context', '')}</pre>
                            </details>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1) # Add slight delay for UI polish
                        
                    elif step_name == "writer":
                        st.markdown(f"""
                        <div class="agent-step agent-writer">
                            <h4>✍️ Writer Agent Active</h4>
                            <p>Drafted initial report structure based on market data.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(1)
                        
                    elif step_name == "editor":
                        st.markdown(f"""
                        <div class="agent-step agent-editor">
                            <h4>👔 Editor Agent Active</h4>
                            <p>Refined text, improved formatting, and ensured professional tone.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        report_container.markdown("---")
                        report_container.markdown("### 📊 Final Intelligence Report")
                        report_container.markdown(state_update.get("final_report", ""))
                        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
