import chromadb
import os

class MemoryManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        print("Initializing Chroma client. This may take a moment on first run as it downloads necessary models.")
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection("memories")
        print("Chroma client initialized successfully.")

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
    def get_user_profile(self, info_type):
        query = f"user profile {info_type}"
        if info_type == "all":
            query = "user profile preferences hobbies personal information"
        
        results = self.collection.query(
            query_texts=[query],
            n_results=10  # Adjust this number as needed
        )
        if results['documents'][0]:
            return "\n".join(results['documents'][0])
        else:
            return f"No user profile information found for {info_type}."