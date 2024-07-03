import chromadb
from chromadb.config import Settings
import os

class MemoryManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.persist_directory
        ))
        self.collection = self.client.get_or_create_collection("memories")

    def save_memory(self, text):
        self.collection.add(
            documents=[text],
            metadatas=[{"source": "user_interaction"}],
            ids=[str(hash(text))]
        )
        return f"Memory saved: {text[:50]}..."

    def recall_memories(self, query, k=3):
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        if results['documents'][0]:
            memories = [f"Memory {i+1}: {doc}" for i, doc in enumerate(results['documents'][0])]
            return "\n\n".join(memories)
        else:
            return "No relevant memories found."
