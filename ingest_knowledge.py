import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

def build_compliance_vector_store():
    # 1. Map documents to their English-only page ranges
    # This prevents vector pollution from the bilingual Gazette formatting
    pdf_sources = {
        "SWM_2026.pdf": (18, 56), 
        "C&D_rules_2025.pdf": (19, 34),
        "e-waste_rules_2022.pdf": (21, 38),
        "HOWM-Sixth-Amendment-Rules-2022.pdf": (9, 16),
        "PWM_Gazette.pdf": (1, 16), 
        "Bulk Waste Generator Book.pdf": (1, 42)
    }

    docs = []
    
    print("Extracting and filtering PDF documents...")
    # 2. Load and filter pages
    for file_name, (start_page, end_page) in pdf_sources.items():
        file_path = f"./data/policies/{file_name}"
        if not os.path.exists(file_path):
            print(f"Skipping {file_name}: File not found.")
            continue
            
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Isolate the English sections (zero-indexed)
        english_pages = pages[start_page-1:end_page]
        docs.extend(english_pages)

    # 3. Chunk the documents
    # Using RecursiveCharacterTextSplitter keeps related sentences together
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Total chunks generated: {len(chunks)}")

    # 4. Initialize Embeddings
    # Using a lightweight, open-source model perfect for local prototyping
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # 5. Ingest into ChromaDB
    chroma_db_dir = "./chroma_db"
    print("Building ChromaDB vector store...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=chroma_db_dir
    )
    
    print(f"Success! Knowledge base saved to {chroma_db_dir}")

if __name__ == "__main__":
    build_compliance_vector_store()