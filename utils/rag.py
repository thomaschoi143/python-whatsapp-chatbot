from langchain_mongodb import MongoDBAtlasVectorSearch
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from uuid import uuid4
from langchain_core.documents import Document
from pathlib import Path
import fitz  # PyMuPDF
from typing import List
import re

load_dotenv()
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

client = MongoClient(MONGODB_ATLAS_CLUSTER_URI)


DB_NAME = "chatbot-rag"
COLLECTION_NAME = "chatbot-vectorstore"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "chatbot-vectorstore-index"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)

script_dir = Path(__file__).parent


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text


def chunk_text(text: str, chunk_size: int, overlap: int, metadata: dict) -> List[str]:
    """Splits text into overlapping chunks."""
    doc_items = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        doc_items.append(Document(page_content=chunk, metadata=metadata))
        start += chunk_size - overlap  # Move start with overlap
    return doc_items


def extract_source(filename: str) -> str:
    match = re.match(r"(\d+)-(\d+)-([a-zA-Z]+)", filename)
    return f"W{match.group(1)}L{match.group(2)}-{match.group(3)}" if match else "unknown"


def upload_documents(directory_path, chunk_size, overlap):
    total_doc_items = 0
    for file in os.listdir(directory_path):
        if file.endswith(".pdf"):
            doc_items = []
            pdf_path = os.path.join(directory_path, file)
            text = extract_text_from_pdf(pdf_path)
            source = extract_source(file)
            doc_items = chunk_text(text, chunk_size, overlap, {"source": source, "subject": directory_path.name})
            uuids = [str(uuid4()) for _ in range(len(doc_items))]

            total_doc_items += len(doc_items)
            vector_store.add_documents(documents=doc_items, ids=uuids)
            print(f"Uploaded {len(doc_items)} items from {file}")

    print(f"Uploaded items in total: {total_doc_items}")


def clear_collection():
    MONGODB_COLLECTION.delete_many({})
    print("Vector store collection was cleared")


# chunk_size = 2000  # Adjust as needed
# overlap = 500  # Adjust as needed
# folder = Path("../data/slides/comp30027")
# clear_collection()
# upload_documents(script_dir / folder, chunk_size, overlap)

retriever = vector_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.2},
)
results = retriever.invoke("Who is the lecturer of this lecture")
for res in results:
    print(f"* {res.page_content} [{res.metadata}]")
