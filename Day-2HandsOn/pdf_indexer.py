import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables from .env file
load_dotenv()

PERSIST_DIR = "./chroma_db_storage"

def get_embeddings():
    """
    Returns the embedding model.
    Tries OpenAI first. If no API key is provided, falls back to local HuggingFace embeddings.
    """
    if os.environ.get("OPENAI_API_KEY"):
        print("Using OpenAI Embeddings")
        return OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        print("OPENAI_API_KEY not found. Falling back to local HuggingFace Embeddings (BGE-small)")
        return HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def load_document(file_path: str):
    """Loads a PDF and returns a list of Document objects."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file '{file_path}' not found. Please place a PDF here and try again.")
    print(f"Loading '{file_path}'...")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages.")
    return documents

def chunk_documents(documents):
    """Splits documents into smaller chunks with optimal overlap."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", "(?<=\. )", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} pages into {len(chunks)} chunks.")
    return chunks

def build_index(chunks):
    """Embeds text chunks and saves them to a persistent Chroma database."""
    embeddings = get_embeddings()
    print("Building and persisting index. This might take a moment...")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
        collection_name="manual"
    )
    print(f"Index successfully built and persisted to '{PERSIST_DIR}'.")
    return vector_store

def retrieve_answers(query: str, k: int = 4):
    """Loads the persisted DB and performs a semantic search."""
    embeddings = get_embeddings()
    
    print(f"\nSearching for: '{query}'")
    vector_store = Chroma(
        persist_directory=PERSIST_DIR, 
        embedding_function=embeddings,
        collection_name="manual"
    )
    
    results = vector_store.similarity_search_with_score(query, k=k)
    
    print(f"\n--- Top {k} Results ---\n")
    for doc, score in results:
        page = doc.metadata.get("page", "N/A")
        print(f"[Score: {score:.4f} | Page: {page}]")
        print(f"Content: {doc.page_content[:250].strip()}...\n")

if __name__ == "__main__":
    pdf_filename = "sample.pdf"
    
    # Check if index already exists to avoid rebuilding
    if not os.path.exists(PERSIST_DIR):
        print("No existing DB found. Starting ingestion workflow...")
        try:
            docs = load_document(pdf_filename)
        except Exception as e:
            print(f"Error: {e}")
            print("\nPlease add a PDF file named 'sample.pdf' to the current directory and run again.")
            exit(1)
            
        chunks = chunk_documents(docs)
        build_index(chunks)
    else:
        print(f"Using existing database at '{PERSIST_DIR}'.")
    
    # Run a test query
    print("\nReady to query!")
    while True:
        user_query = input("\nEnter a search query (or type 'quit' to exit): ")
        if user_query.lower() in ['quit', 'exit', 'q']:
            break
        retrieve_answers(user_query)
