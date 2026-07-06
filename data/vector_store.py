"""
Vector store for scholarship RAG.
Backs embeddings into ChromaDB for fast semantic search.
If ChromaDB is not available, falls back to numpy+sklearn.

Usage:
    python data/vector_store.py --build          # index embeddings.json into DB
    python data/vector_store.py --query "funding for african students"  # search
"""

import json
import argparse
import sys
import warnings
from pathlib import Path

DATA_DIR = Path(__file__).parent
EMBEDDINGS_PATH = DATA_DIR / "embeddings.json"
CHROMA_DIR = DATA_DIR / "chroma_db"


# ─── ChromaDB store ────────────────────────────────────────────────────


class ChromaStore:
    def __init__(self, persist_dir: str | Path = CHROMA_DIR):
        import chromadb

        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = None

    def build(self, chunks: list[dict]):
        import chromadb
        import numpy as np

        collection_name = "scholarships"
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for c in chunks:
            ids.append(c["id"])
            documents.append(c["text"])
            metadatas.append({
                "scholarship_name": c["scholarship_name"],
                "chunk_type": c["chunk_type"],
                **{k: str(v) for k, v in c.get("metadata", {}).items()
                   if isinstance(v, (str, int, float, bool))},
            })
            embeddings.append(c["embedding"])

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=np.array(embeddings, dtype=np.float32),
        )

        print(f"ChromaDB: indexed {len(ids)} chunks into '{collection_name}'")
        print(f"ChromaDB: persisted to {CHROMA_DIR}")

    def query(self, query_text: str, embedding: list[float], top_k: int = 5):
        if self.collection is None:
            try:
                self.collection = self.client.get_collection("scholarships")
            except Exception:
                self.collection = self.client.create_collection("scholarships")

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )

        return [
            {
                "id": results["ids"][0][i],
                "scholarship_name": results["metadatas"][0][i].get("scholarship_name", ""),
                "chunk_type": results["metadatas"][0][i].get("chunk_type", ""),
                "text": results["documents"][0][i],
                "score": results["distances"][0][i] if results.get("distances") else None,
            }
            for i in range(len(results["ids"][0]))
        ]


# ─── Fallback: numpy + sklearn ─────────────────────────────────────────


class NumpyStore:
    def __init__(self):
        self.chunks = []
        self.mat = None
        self.norm = None

    def build(self, chunks: list[dict]):
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        self.chunks = chunks
        self.mat = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        print(f"NumpyStore: indexed {len(chunks)} chunks, dim={self.mat.shape[1]}")

    def query(self, query_text: str, embedding: list[float], top_k: int = 5):
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        vec = np.array([embedding], dtype=np.float32)
        scores = cosine_similarity(vec, self.mat)[0]
        top_idx = np.argsort(scores)[::-1][:top_k]

        return [
            {
                "id": self.chunks[i]["id"],
                "scholarship_name": self.chunks[i]["scholarship_name"],
                "chunk_type": self.chunks[i]["chunk_type"],
                "text": self.chunks[i]["text"],
                "score": float(scores[i]),
            }
            for i in top_idx
        ]


# ─── Factory ───────────────────────────────────────────────────────────


def get_store():
    chromadb_available = False
    try:
        import chromadb  # noqa: F401
        chromadb_available = True
    except ImportError:
        pass

    if chromadb_available:
        print("Using ChromaDB (persistent)")
        return ChromaStore()

    try:
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401
        print("Falling back to NumpyStore (sklearn)")
        return NumpyStore()
    except ImportError:
        print("ERROR: neither ChromaDB nor scikit-learn are available.")
        print("  pip install scikit-learn")
        sys.exit(1)


def load_embeddings(path: Path = EMBEDDINGS_PATH) -> list[dict]:
    with open(path) as f:
        chunks = json.load(f)
    return chunks


# ─── CLI ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser("Vector store for scholarship RAG")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build vector index from embeddings.json",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query string to search (requires --embedding or will re-embed on the fly)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results (default: 5)",
    )
    parser.add_argument(
        "--input",
        default=str(EMBEDDINGS_PATH),
    )
    parser.add_argument(
        "--re-embed",
        action="store_true",
        help="Re-embed query using TF-IDF (for querying without API)",
    )
    args = parser.parse_args()

    if args.build:
        chunks = load_embeddings(Path(args.input))
        store = get_store()
        store.build(chunks)
        print("Done. Ready for --query.")

    elif args.query:
        store = get_store()
        chunks = load_embeddings(Path(args.input))

        if isinstance(store, ChromaStore):
            try:
                store.collection = store.client.get_collection("scholarships")
            except Exception:
                pass
        elif isinstance(store, NumpyStore) and not store.chunks:
            store.build(chunks)

        if args.re_embed:
            from sklearn.feature_extraction.text import TfidfVectorizer
            texts = [c["text"] for c in chunks]
            vec = TfidfVectorizer(max_features=256, stop_words="english", ngram_range=(1, 2))
            vec.fit(texts)
            embedding = vec.transform([args.query]).toarray()[0].tolist()
        else:
            embedding = chunks[0]["embedding"]

        results = store.query(args.query, embedding, top_k=args.top_k)

        print(f"\nTop {args.top_k} results for: \"{args.query}\"\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['chunk_type']}] {r['scholarship_name']}")
            print(f"   Score: {r['score']:.4f}" if r['score'] else "")
            print(f"   {r['text'][:200]}...")
            print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
