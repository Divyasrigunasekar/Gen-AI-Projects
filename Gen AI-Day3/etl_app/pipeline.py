import os
import pandas as pd
import io
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Define the state taking place in the graph
class PipelineState(TypedDict):
    raw_data: Optional[pd.DataFrame]
    cleaned_data: Optional[pd.DataFrame]
    enriched_data: Optional[pd.DataFrame]
    final_data: Optional[pd.DataFrame]
    logs: list[str]
    input_file_path: Optional[str]

def extract_node(state: PipelineState):
    """
    Extract: Load data from source (CSV in this case).
    Purpose: Read structural data into a manipulatable format (Pandas DataFrame).
    Common Pitfalls: Encoding issues, missing headers, large file sizes crashing memory.
    """
    print("Executing Extract Node...")
    logs = state.get("logs", [])
    
    try:
        # Load the CSV
        df = pd.read_csv(state["input_file_path"])
        logs.append(f"Successfully extracted {len(df)} rows from {state['input_file_path']}.")
        
        return {"raw_data": df, "logs": logs}
    except Exception as e:
        logs.append(f"Error during extraction: {str(e)}")
        return {"logs": logs}

def transform_cleaning_node(state: PipelineState):
    """
    Transform (Cleaning): Handle missing values, deduplication, type casting.
    Purpose: Ensure data quality and consistency.
    """
    print("Executing Transform Cleaning Node...")
    df = state.get("raw_data")
    logs = state.get("logs", [])
    
    if df is None or df.empty:
        logs.append("No data to clean.")
        return {"logs": logs}
        
    initial_len = len(df)
    
    # 1. Deduplication
    if 'TransactionID' in df.columns:
        df = df.drop_duplicates(subset=['TransactionID'], keep='first')
    
    # 2. Handling Missing Values
    if 'UserID' in df.columns:
        df = df.dropna(subset=['UserID'])
    
    # 3. Type Conversion & Normalization
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].astype(str).str.replace('[\$,]', '', regex=True).replace('', 'NaN').astype(float)
        df['Amount'] = df['Amount'].fillna(df['Amount'].median())
    
    if 'ProductCategory' in df.columns:
        df['ProductCategory'] = df['ProductCategory'].astype(str).str.title()
        
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    final_len = len(df)
    logs.append(f"Cleaned data. Reduced rows from {initial_len} to {final_len}.")
    
    return {"cleaned_data": df.copy(), "logs": logs}

def transform_enrich_node(state: PipelineState):
    """
    Transform (AI Enrichment): Use Groq LLM to analyze texts/notes.
    """
    print("Executing Transform AI Enrich Node...")
    df = state.get("cleaned_data")
    logs = state.get("logs", [])
    
    if df is None or df.empty:
        return {"logs": logs}

    try:
        # Initialize Groq LLM
        # Assumes GROQ_API_KEY is in environment
        llm = ChatGroq(model="llama3-8b-8192", temperature=0)
        
        def analyze_note(note):
            if pd.isna(note) or note == "":
                return "Neutral"
            try:
                response = llm.invoke([
                    HumanMessage(content=f"Analyze the sentiment of this transaction note. Return ONLY one word: Positive, Negative, or Neutral. Note: '{note}'")
                ])
                return response.content.strip()
            except Exception:
                return "Error"

        if 'Notes' in df.columns:
            df['Sentiment'] = df['Notes'].apply(analyze_note)
            logs.append("Groq LLM successfully analyzed sentiment on Notes.")
        
    except Exception as e:
        logs.append(f"Groq LLM Enrichment skipped or failed: {str(e)}. (Check if API key is valid)")
        
    return {"enriched_data": df, "logs": logs}

def load_node(state: PipelineState):
    """
    Load: Save the processed data to a target destination.
    Purpose: Store the high-quality, processed data for consumption (analytics, ML).
    """
    print("Executing Load Node...")
    df = state.get("enriched_data")
    if df is None:
        df = state.get("cleaned_data")
        
    logs = state.get("logs", [])
    
    if df is None:
        return {"logs": logs}

    output_path = "output_data.csv"
    try:
        df.to_csv(output_path, index=False)
        logs.append(f"Successfully loaded output data to {output_path}.")
    except Exception as e:
        logs.append(f"Error saving to CSV: {str(e)}")

    return {"final_data": df, "logs": logs}

# Build the Graph
def build_pipeline():
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("extract", extract_node)
    workflow.add_node("transform_clean", transform_cleaning_node)
    workflow.add_node("transform_enrich", transform_enrich_node)
    workflow.add_node("load", load_node)
    
    # Add edges
    workflow.add_edge(START, "extract")
    workflow.add_edge("extract", "transform_clean")
    workflow.add_edge("transform_clean", "transform_enrich")
    workflow.add_edge("transform_enrich", "load")
    workflow.add_edge("load", END)
    
    # Compile
    app = workflow.compile()
    return app
