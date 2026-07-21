import chromadb

# 1. Connect to your existing local database
print("Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./terra_vector_db")
collection = chroma_client.get_collection(name="thinking_traces")

# 2. Retrieve all documents
# Calling .get() without any filters returns everything in the collection
results = collection.get()

print(f"\n--- FOUND {len(results['ids'])} TRACES ---\n")

# 3. Loop through and print them beautifully
for i in range(len(results['ids'])):
    case_id = results['ids'][i]
    title = results['metadatas'][i]['title']
    trace = results['documents'][i]
    
    print(f"[{case_id}] {title}")
    print("-" * 40)
    print(f"{trace}\n")
    print("=" * 60 + "\n")