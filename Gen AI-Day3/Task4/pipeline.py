import os
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

class RealEstateGraphState(TypedDict):
    query: str
    context: str
    draft: str
    final_report: str
    current_step: str

# Dummy Real Estate Data
DUMMY_DATA = [
    "Downtown Austin Commercial Property XYZ: Asking price $5.2M. Cap rate 6.5%. Leased to tech startup till 2030. High ROI potential due to tech boom.",
    "South Congress Residential Complex: 10 units. Asking $3.1M. Cap rate 5%. Average rent $2500/unit. Neighborhood analysis shows a 15% YoY appreciation.",
    "Austin Market Trend Q3: Interest rates stabilizing around 6%. Tech sector driving demand in downtown. Commercial office space availability is tight, at 5% vacancy.",
    "Zilker Park 3BHK: Premium residential. Asking $1.5M. Expected rental income $6k/month. Low risk, steady appreciation, highly sought after location.",
    "East Austin Mixed-Use Development: Asking price $8.4M. Contains retail on ground floor and 20 luxury apartments above. Projected ROI 8% within 3 years.",
    "Houston Central Investment: 50 unit complex, asking $12M. Cap rate 4%. Value-add opportunity needing renovation."
]

_vdb_instance = None

def get_vector_db():
    global _vdb_instance
    if _vdb_instance is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vdb_instance = Chroma.from_texts(DUMMY_DATA, embeddings)
    return _vdb_instance

def get_llm():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set!")
    return ChatGroq(model_name="llama-3.3-70b-versatile", api_key=api_key, temperature=0.2)

def researcher_agent(state: RealEstateGraphState):
    query = state.get("query", "")
    vdb = get_vector_db()
    
    docs = vdb.similarity_search(query, k=3)
    context = "\n- ".join([d.page_content for d in docs])
    
    return {"context": context, "current_step": "researcher"}

def writer_agent(state: RealEstateGraphState):
    llm = get_llm()
    query = state.get("query")
    context = state.get("context")
    
    prompt = f"""You are a skilled real estate analyst and writer. 
Based on the following market context, draft a structured report answering the query.

Query: {query}
Market Data/Context: 
- {context}

Please draft a report including:
1. Executive Summary
2. Market Insights / Comps
3. ROI Potential & Risks (if applicable)

Draft Report:"""
    
    res = llm.invoke(prompt)
    return {"draft": res.content, "current_step": "writer"}

def editor_agent(state: RealEstateGraphState):
    llm = get_llm()
    draft = state.get("draft")
    
    prompt = f"""You are a senior executive editor for a prestigious real estate intelligence firm.
Review the following draft for professional tone, analytical clarity, and strong formatting. 
Ensure the final artifact looks like a premium market report suitable for high-net-worth investors or institutional brokers.
Format heavily using Markdown (headers, bullet points, bold text). Remove any superficial language.

Draft:
{draft}

Final Output:"""

    res = llm.invoke(prompt)
    return {"final_report": res.content, "current_step": "editor"}

def build_graph():
    builder = StateGraph(RealEstateGraphState)
    builder.add_node("researcher", researcher_agent)
    builder.add_node("writer", writer_agent)
    builder.add_node("editor", editor_agent)
    
    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "editor")
    builder.add_edge("editor", END)
    
    return builder.compile()
