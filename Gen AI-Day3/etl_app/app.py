import streamlit as st
import pandas as pd
import tempfile
import os
import requests
import io
from pipeline import build_pipeline

# Styling and Page Config
st.set_page_config(page_title="AI Data ETL Pipeline", layout="wide")

# Custom CSS for aesthetic styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .header-text {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: bold;
    }
    .sub-header {
        color: #4ECDC4;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-text">LangGraph + Pandas ETL Orchestrator</div>', unsafe_allow_html=True)
st.write("A production-ready 3-step linear data processing pipeline designed for clarity and robustness.")

# -----------------
# Educational Content (Markdown Requirements)
# -----------------
with st.expander("📖 View ETL Architecture & Concepts (Click to Expand)", expanded=True):
    st.markdown("""
    ### Overview
    This pipeline demonstrates a real-world linear ETL pattern orchestrating Pandas data manipulation steps utilizing LangGraph as the orchestrator. State is managed via a `TypedDict` across nodes, allowing clear observability of data mutations.

    ### Step 1: Extract
    - **Purpose**: Ingest structured or semi-structured data from source systems.
    - **Input**: Raw file (CSV, Database Connection String).
    - **Output**: Unprocessed Pandas DataFrame.
    - **Common Pitfalls**: Incorrect encoding (e.g. latin-1 vs utf-8), memory crashes on large files without chunking, parsing errors on corrupted rows.

    ### Step 2: Transform
    - **Purpose**: Clean, normalize, and enrich the data.
    - **Input**: Unprocessed Pandas DataFrame.
    - **Output**: Cleaned and formatted Pandas DataFrame.
    - **Common Pitfalls**: Over-aggressive deduplication dropping valid data, silently ignoring NaN/null values leading to upstream errors, failing to cast types properly resulting in invalid aggregations.
    - *Operations implemented*: Deduplication, NA dropping, Type-casting amounts, Category Normalization, & AI-based note sentiment analysis.

    ### Step 3: Load
    - **Purpose**: Store the processed and enriched data into its final destination.
    - **Input**: Cleaned DataFrame.
    - **Output**: Persisted File (CSV) or Table entry.
    - **Common Pitfalls**: Overwriting existing data destructively, schema mismatches between source and destination, transaction failures leading to partial loads.

    ### Code Example
    Here is a simplified structural view of how this is orchestrated:
    ```python
    from langgraph.graph import StateGraph, START, END
    from typing import TypedDict
    import pandas as pd

    class PipelineState(TypedDict):
        raw_data: pd.DataFrame
        cleaned_data: pd.DataFrame
        # ... other state fields

    def extract(state): ...
    def transform(state): ...
    def load(state): ...

    workflow = StateGraph(PipelineState)
    workflow.add_node("extract", extract)
    workflow.add_node("transform", transform)
    workflow.add_node("load", load)

    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "transform")
    workflow.add_edge("transform", "load")
    workflow.add_edge("load", END)

    app = workflow.compile()
    app.invoke({"input_file_path": "data.csv"})
    ```
    """)

st.markdown("---")
st.markdown('<h2 class="sub-header">Interactive Pipeline</h2>', unsafe_allow_html=True)

# -----------------
# App Logic
# -----------------

# Interactive File Uploader
uploaded_file = st.file_uploader("Upload a CSV file to process", type=["csv"])

if st.button("Use Sample Data"):
    if os.path.exists("sample_data.csv"):
        with open("sample_data.csv", "rb") as f:
            uploaded_file = io.BytesIO(f.read())
            uploaded_file.name = "sample_data.csv"
    else:
        st.error("Sample dataset missing.")

if uploaded_file is not None:
    # Save uploaded file to temp to pass to Extract Node
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    st.success(f"File '{uploaded_file.name}' loaded successfully!")
    
    if st.button("🚀 Run Pipeline"):
        with st.spinner("Processing Data through LangGraph Pipeline..."):
            # Initialize pipeline
            pipeline = build_pipeline()
            
            # Initial state
            initial_state = {
                "input_file_path": tmp_path,
                "raw_data": None,
                "cleaned_data": None,
                "enriched_data": None,
                "final_data": None,
                "logs": []
            }
            
            # Run LangGraph Pipeline
            final_state = pipeline.invoke(initial_state)
            
            # Display execution logs
            st.markdown("### Execution Logs")
            for log in final_state['logs']:
                st.info(log)
            
            # Display results in tabs
            col1, col2, col3 = st.tabs(["1. Extracted Data (Raw)", "2. Transformed Data (Clean/Enriched)", "3. Loaded Data (Final)"])
            
            with col1:
                st.write("Data exactly as extracted from source.")
                if final_state.get('raw_data') is not None:
                    st.dataframe(final_state['raw_data'], use_container_width=True)
            
            with col2:
                st.write("Data after missing values handled, deduplication, normalizations, and LLM Enrichment.")
                if final_state.get('enriched_data') is not None:
                    st.dataframe(final_state['enriched_data'], use_container_width=True)
                elif final_state.get('cleaned_data') is not None:
                    st.dataframe(final_state['cleaned_data'], use_container_width=True)
            
            with col3:
                st.write("Final output data that would be written to destination.")
                if final_state.get('final_data') is not None:
                    st.dataframe(final_state['final_data'], use_container_width=True)
                    
                    csv = final_state['final_data'].to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Processed Output CSV",
                        data=csv,
                        file_name='processed_output.csv',
                        mime='text/csv',
                    )
                    
        # Cleanup temp file
        os.unlink(tmp_path)
