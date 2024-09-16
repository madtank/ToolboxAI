import chromadb
import uuid
import json
from datetime import datetime

class MemoryManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.memories_collection = self.client.get_or_create_collection("memories")
        self.user_profile_collection = self.client.get_or_create_collection("user_profile")
        self.messages_collection = self.client.get_or_create_collection("messages")  # Updated line 

    def save_memory(self, text, metadata=None):
        memory_id = str(uuid.uuid4())
        self.memories_collection.add(
            documents=[text],
            metadatas=[metadata or {"source": "user_interaction"}],
            ids=[memory_id]
        )
        return f"Memory saved with ID: {memory_id}"

    def recall_memories(self, query, k=3):
        results = {}
        for collection_name in ["memories", "user_profile", "messages"]:
            collection = getattr(self, f"{collection_name}_collection")
            collection_results = collection.query(
                query_texts=[query],
                n_results=k
            )
            results[collection_name] = collection_results

        # Combine and sort results from all collections
        combined_results = []
        for collection_name, collection_results in results.items():
            for i, (doc, metadata, distance) in enumerate(zip(
                collection_results['documents'][0], 
                collection_results['metadatas'][0], 
                collection_results['distances'][0]
            )):
                combined_results.append({
                    "collection": collection_name,
                    "id": collection_results['ids'][0][i],
                    "content": doc,
                    "metadata": metadata,
                    "distance": distance
                })

        # Sort by distance (most relevant first)
        combined_results.sort(key=lambda x: x['distance'])

        # Format the results
        formatted_results = []
        for i, result in enumerate(combined_results[:k]):
            memory_info = f"Memory {i+1}:\n"
            memory_info += f"Collection: {result['collection']}\n"
            memory_info += f"ID: {result['id']}\n"
            memory_info += f"Content: {result['content']}\n"
            memory_info += f"Metadata: {result['metadata']}\n"
            memory_info += f"Semantic Distance: {result['distance']}\n"
            formatted_results.append(memory_info)

        return "\n\n".join(formatted_results)

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
            existing_profile = self.user_profile_collection.get(ids=["user_profile"])
            if existing_profile['documents']:
                self.user_profile_collection.update(
                    ids=["user_profile"],
                    documents=[profile_data],
                    metadatas=[{"source": "user_profile", "updated": True}]
                )
            else:
                self.user_profile_collection.add(
                    documents=[profile_data],
                    metadatas=[{"source": "user_profile"}],
                    ids=["user_profile"]
                )
            return "User profile updated successfully."
        except Exception as e:
            return f"Error updating user profile: {str(e)}"

    def get_user_profile(self):
        results = self.user_profile_collection.get(ids=["user_profile"])
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

    def save_conversation(self, messages):
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Convert messages to a string format
        conversation_text = json.dumps(messages)
        
        self.messages_collection.add(
            documents=[conversation_text],
            metadatas=[{"timestamp": timestamp, "type": "conversation"}],
            ids=[conversation_id]
        )
        return f"Conversation saved with ID: {conversation_id}"

    def retrieve_recent_conversations(self, k=5):
        results = self.messages_collection.query(
            query_texts=["recent conversation"],
            n_results=k,
            where={"role": "user"}  # Assuming we identify conversations by user messages
        )
        if results['documents'][0]:
            conversations = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                conversation_info = f"Conversation {i+1}:\n"
                conversation_info += f"ID: {metadata['conversation_id']}\n"
                conversation_info += f"Timestamp: {metadata['timestamp']}\n"
                conversation_info += f"Content: {doc[:100]}...\n"  # Show first 100 characters
                conversations.append(conversation_info)
            return "\n\n".join(conversations)
        else:
            return "No recent conversations found."

    def save_message(self, message, conversation_id=None):
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        message_text = json.dumps(message)

        metadata = {
            "timestamp": timestamp,
            "role": message["role"],
            "conversation_id": conversation_id,
            "category": "conversation"
        }

        self.messages_collection.add(
            documents=[message_text],
            metadatas=[metadata],
            ids=[message_id]
        )
        return message_id, conversation_id

    def retrieve_conversation(self, conversation_id, limit=None):
        results = self.messages_collection.query(
            query_texts=[""],
            where={"conversation_id": conversation_id},
            n_results=limit or 1000
        )
        if results['documents'][0]:
            messages = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                message = json.loads(doc)
                message['timestamp'] = metadata['timestamp']
                messages.append(message)
            return sorted(messages, key=lambda x: x['timestamp'])
        else:
            return []

    def retrieve_conversation_history(self, conversation_id, limit=None):
        results = self.messages_collection.query(
            query_texts=[""],
            where={"conversation_id": conversation_id},
            n_results=limit or 1000
        )
        if results['documents'][0]:
            messages = []
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                message = json.loads(doc)
                message['timestamp'] = metadata['timestamp']
                messages.append(message)
            return sorted(messages, key=lambda x: x['timestamp'])
        else:
            return []