import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

# Mount static files for our beautiful UI
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

PERSIST_DIR = "./chroma_db_storage"
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global vector store reference
vector_store = None

# Initialize Embeddings
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# Initialize ChatGroq (Make sure GROQ_API_KEY is in .env)
llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.2)

# Load existing DB if it exists
if os.path.exists(PERSIST_DIR):
    vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings, collection_name="manual")

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vector_store
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Load and chunk
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        # Build Vector Store
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=PERSIST_DIR,
            collection_name="manual"
        )
        return {"status": "success", "message": f"Successfully indexed {file.filename} ({len(chunks)} chunks)."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(request: ChatRequest):
    global vector_store
    if vector_store is None:
        raise HTTPException(status_code=400, detail="Database not initialized. Please upload a PDF first.")
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    response = qa_chain.invoke({"query": request.query})
    
    # Extract sources safely
    sources = []
    if "source_documents" in response:
        for doc in response["source_documents"]:
            sources.append(f"Page {doc.metadata.get('page', 'N/A')}")
            
    return {
        "answer": response["result"],
        "sources": list(set(sources))
    }
