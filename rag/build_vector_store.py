"""
Embeds liar2 fact-check claims into a persistent Chroma vector store.
Run once (or whenever the source data changes) to (re)build the RAG knowledge base.
"""

from datasets import load_dataset
import chromadb

# Human-readable label mapping, confirmed earlier from the dataset's ClassLabel metadata
LABEL_MAP = {
    0: "pants-fire",
    1: "false",
    2: "barely-true",
    3: "half-true",
    4: "mostly-true",
    5: "true",
}

BATCH_SIZE = 500
CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "factchecks"


def clean_metadata(row: dict) -> dict:
    """Chroma rejects None values in metadata, so replace them with empty strings."""
    return {
        "label": row["label"],
        "label_text": LABEL_MAP.get(row["label"], "unknown"),
        "subject": row["subject"] or "",
        "speaker": row["speaker"] or "",
        "date": row["date"] or "",
        "state_info": row["state_info"] or "",
        "justification": row["justification"] or "",
    }


def main():
    print("Loading liar2 dataset (all splits)...")
    ds = load_dataset("chengxuphd/liar2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_added = 0

    for split_name in ["train", "validation", "test"]:
        split = ds[split_name]
        print(f"Processing split '{split_name}' ({len(split)} rows)...")

        ids_batch, docs_batch, meta_batch = [], [], []

        for row in split:
            ids_batch.append(f"{split_name}_{row['id']}")
            docs_batch.append(row["statement"])
            meta_batch.append(clean_metadata(row))

            if len(ids_batch) >= BATCH_SIZE:
                collection.add(ids=ids_batch, documents=docs_batch, metadatas=meta_batch)
                total_added += len(ids_batch)
                print(f"  Added {total_added} claims so far...")
                ids_batch, docs_batch, meta_batch = [], [], []

        # Add any leftover rows that didn't fill a full batch
        if ids_batch:
            collection.add(ids=ids_batch, documents=docs_batch, metadatas=meta_batch)
            total_added += len(ids_batch)

    print(f"Done. Total claims embedded: {total_added}")
    print(f"Collection count (verify): {collection.count()}")


if __name__ == "__main__":
    main()