import chromadb

client = chromadb.PersistentClient(path="data/chroma")
collection = client.get_or_create_collection(name="factchecks")

query = "vaccines cause autism in children"
results = collection.query(query_texts=[query], n_results=3)

for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    print(f"\n--- Result {i+1} ---")
    print(f"Claim: {doc}")
    print(f"Label: {meta['label_text']}")
    print(f"Subject: {meta['subject']}")