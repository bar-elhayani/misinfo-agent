"""
Embeds FEVER claims into a persistent Chroma vector store.
Source: https://fever.ai (train + shared_task_dev splits), CC BY-SA 3.0.
Run once (or whenever the source data changes) to (re)build the RAG knowledge base.
"""

import json

import chromadb

BATCH_SIZE = 500
CHROMA_PATH = "data/chroma"
COLLECTION_NAME = "factchecks"

FILES = {
    "train": "data/raw/fever/train.jsonl",
    "dev": "data/raw/fever/shared_task_dev.jsonl",
}


def extract_evidence_refs(evidence) -> tuple[str, str]:
    """
    FEVER's evidence field is a nested list of
    [annotation_id, evidence_id, wiki_url, sentence_id] tuples,
    or [annotation_id, evidence_id, None, None] for NOT ENOUGH INFO.
    Chroma metadata must be flat scalars, so we flatten to
    comma-separated strings of unique wiki pages and sentence ids.
    """
    wiki_urls, sentence_ids = set(), set()
    for evidence_set in evidence:
        for _, _, wiki_url, sentence_id in evidence_set:
            if wiki_url is not None:
                wiki_urls.add(wiki_url)
            if sentence_id is not None:
                sentence_ids.add(str(sentence_id))
    return ", ".join(sorted(wiki_urls)), ", ".join(sorted(sentence_ids))


def build_metadata(row: dict) -> dict:
    wiki_urls, sentence_ids = extract_evidence_refs(row["evidence"])
    return {
        "label": row["label"],
        "verifiable": row["verifiable"],
        "evidence_wiki_urls": wiki_urls,
        "evidence_sentence_ids": sentence_ids,
    }


def main():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    total_added = 0

    for split_name, path in FILES.items():
        print(f"Processing split '{split_name}' from {path}...")

        ids_batch, docs_batch, meta_batch = [], [], []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)

                ids_batch.append(f"{split_name}_{row['id']}")
                docs_batch.append(row["claim"])
                meta_batch.append(build_metadata(row))

                if len(ids_batch) >= BATCH_SIZE:
                    collection.add(ids=ids_batch, documents=docs_batch, metadatas=meta_batch)
                    total_added += len(ids_batch)
                    print(f"  Added {total_added} claims so far...")
                    ids_batch, docs_batch, meta_batch = [], [], []

        if ids_batch:
            collection.add(ids=ids_batch, documents=docs_batch, metadatas=meta_batch)
            total_added += len(ids_batch)

    print(f"Done. Total claims embedded: {total_added}")
    print(f"Collection count (verify): {collection.count()}")


if __name__ == "__main__":
    main()