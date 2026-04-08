# Real Estate Research Multi-Agent System

This plan outlines the design and implementation of a 3-agent LangGraph system tailored for the real estate industry, utilizing Groq API for LLM reasoning and ChromaDB for retrieval-augmented research.

## User Review Required

- **API Usage:** I will use the provided Groq API key instead of the OpenAI API, as it serves as a highly performant equivalent LLM provider.
- **UI Framework:** I propose using Streamlit with custom CSS to create a fast, colorful, reactive, and interactive Python-native UI to demonstrate the LangGraph pipeline. Is this acceptable?
- **Vector DB Context:** For ChromaDB, I will mock a sample dataset of real estate market listings and insights to demonstrate RAG functionality.

## Proposed Changes

We will create a new directory `RealEstateAgents` to hold our application files.

---

### Backend Logic & LangGraph Orchestration

#### [NEW] [RealEstateAgents/pipeline.py](file:///c:/Users/divya/Desktop/Generative-AI%20session/Gen%20AI-Day3/RealEstateAgents/pipeline.py)
This will contain the core logic:
- **State Definition:** TypedDict representing the graph state (`query`, `context`, `draft`, `final_report`, `status`).
- **ChromaDB Setup:** Initialize an ephemeral ChromaDB collection and load it with realistic real estate dummy data (comps, market reports).
- **Researcher Agent:** Performs vector search in ChromaDB based on the query and extracts market trends, comps, and insights.
- **Writer Agent:** Uses Groq LLM to draft a structured report based on the context provided by the Researcher.
- **Editor Agent:** Uses Groq LLM to review the draft, correct tone, ensure formatting, and finalize the professional report.
- **LangGraph Setup:** Nodes and edges connecting Researcher -> Writer -> Editor.

#### [NEW] [RealEstateAgents/app.py](file:///c:/Users/divya/Desktop/Generative-AI%20session/Gen%20AI-Day3/RealEstateAgents/app.py)
This will contain the Streamlit UI:
- **Colourful & Reactive UI:** Custom CSS for a premium look, vibrant buttons, and clear typography.
- **Session State:** To hold conversation and process steps.
- **Agent Tracing:** A real-time reactive display showing which agent is currently active and processing.
- **Final Output Render:** Formatting the resulting Markdown report beautifully.

#### [NEW] [RealEstateAgents/requirements.txt](file:///c:/Users/divya/Desktop/Generative-AI%20session/Gen%20AI-Day3/RealEstateAgents/requirements.txt)
Contains dependencies:
```text
langgraph
langchain
langchain-groq
langchain-community
chromadb
streamlit
sentence-transformers
```

## Open Questions

- Would you like any specific geographic region or property type (e.g., commercial vs residential) hardcoded into the sample dummy data for the ChromaDB store?
- Are there specific UI color themes you prefer for the "colourful" requirement?

## Verification Plan

### Automated Tests
- We will install requirements, run `test_pipeline.py` or manually execute queries to ensure the graph compiles and passes state correctly.

### Manual Verification
- Launch the Streamlit application.
- Input a sample query like "Analyze the ROI potential for a 3BHK in downtown Austin".
- Verify that the UI visualizes the steps (Researcher -> Writer -> Editor) and renders a professional final report using Groq.
