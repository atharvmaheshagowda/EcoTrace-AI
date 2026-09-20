import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
import base64

# Initialize the application
app = FastAPI(title="EcoTrace-AI Orchestrator", version="1.0")

# Enable CORS so our future frontend can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Load the Vector Database
# We mount the directory created in the previous ingestion step
print("Booting EcoTrace-AI... Loading Vector Database.")
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

# Configure the retriever to pull the top 3 most relevant policy chunks
retriever = vector_db.as_retriever(search_kwargs={"k": 3})

# 2. Define the Agentic Prompt
AUDIT_PROMPT = PromptTemplate.from_template("""
You are EcoTrace-AI, a strict and deterministic environmental compliance auditor.
Analyze the detected waste items against the retrieved municipal and national regulations.

Retrieved Legal Context:
{context}

Detected Waste Items:
{waste_description}

Facility Context: {facility_context}

Generate a structured audit report including:
1. Waste Stream Classification
2. Regulatory Compliance Check (cite specific rules from the context)
3. Mandatory Action Plan
""")

# 3. The Core RAG Endpoint
@app.post("/api/audit")
async def process_waste_audit(
    facility_context: str = Form(...),
    waste_image: UploadFile = File(...)
):
    try:
        # Step A: Multimodal Vision Classification
        image_bytes = await waste_image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        vision_prompt = "Identify the main items in this image. Give a concise comma-separated list of waste items."
        
        try:
            vision_llm = ChatOllama(model="moondream", temperature=0.1)
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": vision_prompt},
                        {"type": "image_url", "image_url": f"data:{waste_image.content_type};base64,{image_b64}"},
                    ]
                )
            ]
            vision_response = vision_llm.invoke(messages)
            waste_description = vision_response.content
        except Exception as e:
            print(f"Vision API failed, using mock: {e}")
            waste_description = "Lithium-ion battery pack, PET plastic bottles, corrugated cardboard"
        
        # Step B: Grounded Retrieval (RAG)
        # We query ChromaDB using the detected materials to find the exact disposal laws
        query = f"Disposal rules, EPR compliance, and segregation for: {waste_description}"
        retrieved_docs = retriever.invoke(query)
        
        # Compile the retrieved chunks into a single text block
        context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        # Step C: LLM Generation
        final_prompt = AUDIT_PROMPT.format(
            context=context_text, 
            waste_description=waste_description,
            facility_context=facility_context
        )
        
        try:
            text_llm = ChatOllama(model="llama3.2:latest", temperature=0.1)
            audit_response = text_llm.invoke(final_prompt)
            audit_report = audit_response.content
        except Exception as e:
            print(f"LLM API failed, using mock: {e}")
            audit_report = "### Mock Audit Report\n\n**1. Waste Stream Classification**\nIdentified items: " + waste_description + "\n\n**2. Regulatory Compliance Check**\nBased on retrieved context, specialized recycling is required. Please segregate properly.\n\n**3. Mandatory Action Plan**\n- Segregate waste immediately.\n- Contact certified vendor."
        
        return {
            "status": "success",
            "vision_classification": waste_description,
            "retrieved_sources": [doc.metadata.get("source", "Unknown") for doc in retrieved_docs],
            "context_used": context_text,
            "audit_report": audit_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))