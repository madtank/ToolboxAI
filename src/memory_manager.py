import chromadb
import uuid

class MemoryManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.memories_collection = self.client.get_or_create_collection("memories")
        self.profile_collection = self.client.get_or_create_collection("user_profile")

    def save_memory(self, text, metadata=None):
        memory_id = str(uuid.uuid4())
        self.memories_collection.add(
            documents=[text],
            metadatas=[metadata or {"source": "user_interaction"}],
            ids=[memory_id]
        )
        return f"Memory saved with ID: {memory_id}"

    def recall_memories(self, query, k=3):
        results = self.memories_collection.query(
            query_texts=[query],
            n_results=k
        )
        if results['documents'][0]:
            memories = []
            for i, (doc, metadata, distance) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
                memory_info = f"Memory {i+1}:\n"
                memory_info += f"ID: {results['ids'][0][i]}\n"
                memory_info += f"Content: {doc}\n"
                memory_info += f"Metadata: {metadata}\n"
                memory_info += f"Semantic Distance: {distance}\n"
                memories.append(memory_info)
            return "\n\n".join(memories)
        else:
            return "No relevant memories found based on the semantic search."

    def update_memory(self, memory_id, new_text, new_metadata=None):
        try:
            current_memory = self.memories_collection.get(ids=[memory_id])
            if not current_memory['documents']:
                return f"Memory with ID {memory_id} not found."
            
            self.memories_collection.update(
                ids=[memory_id],
                documents=[new_text],
                metadatas=[new_metadata or {"source": "user_interaction", "updated": True}]
            )
            return f"Memory with ID {memory_id} updated successfully."
        except Exception as e:
            return f"Error updating memory: {str(e)}"

    def delete_memory(self, memory_id):
        try:
            self.memories_collection.delete(ids=[memory_id])
            return f"Memory with ID {memory_id} deleted successfully."
        except Exception as e:
            return f"Error deleting memory: {str(e)}"

    def update_user_profile(self, profile_data):
        try:
            existing_profile = self.profile_collection.get(ids=["user_profile"])
            if existing_profile['documents']:
                self.profile_collection.update(
                    ids=["user_profile"],
                    documents=[profile_data],
                    metadatas=[{"source": "user_profile", "updated": True}]
                )
            else:
                self.profile_collection.add(
                    documents=[profile_data],
                    metadatas=[{"source": "user_profile"}],
                    ids=["user_profile"]
                )
            return "User profile updated successfully."
        except Exception as e:
            return f"Error updating user profile: {str(e)}"

    def get_user_profile(self):
        results = self.profile_collection.get(ids=["user_profile"])
        if results['documents']:
            return results['documents'][0]
        else:
            return "No user profile found."

    def list_all_memories(self):
        results = self.memories_collection.get()
        if results['documents']:
            memories = [f"Memory ID: {id}, Content: {doc}" for id, doc in zip(results['ids'], results['documents'])]
            return "\n\n".join(memories)
        else:
            return "No memories found."