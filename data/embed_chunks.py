"""
Embed chunks for RAG vector search.
Usage:
    python data/embed_chunks.py                                  # OpenRouter (uses .env key)
    python data/embed_chunks.py --backend openai                 # OpenAI API
    python data/embed_chunks.py --backend tfidf                  # local TF-IDF (no deps)
    python data/embed_chunks.py --backend tfidf --max-features 512
"""

import json
import os
import argparse
import sys
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent
CHUNKS_PATH = DATA_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.json"
EMBEDDINGS_NPY_PATH = DATA_DIR / "embeddings.npy"
BATCH_SIZE = 32


def load_chunks(path: Path) -> list[dict]:
    with open(path) as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {path}")
    return chunks


def read_api_key(var: str) -> str | None:
    val = os.environ.get(var)
    if val:
        return val
    env_path = Path(__file__).parents[1] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{var}="):
                return line.split("=", 1)[1].strip()
    return None


# ─── OpenRouter API ────────────────────────────────────────────────────


def embed_openrouter(
    chunks: list[dict],
    model: str = "openai/text-embedding-3-small",
) -> list[dict]:
    import requests

    api_key = read_api_key("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env or environment")
        sys.exit(1)

    print(f"Backend: OpenRouter  |  Model: {model}")
    texts = [c["text"] for c in chunks]
    all_vecs = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = requests.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": batch},
            timeout=120,
        )
        if resp.status_code == 402:
            print("ERROR: OpenRouter embedding requires billing credits (402)")
            print("  → Add credits at https://openrouter.ai/settings/credits")
            print("  → Or use --backend tfidf for a free local fallback")
            sys.exit(1)
        resp.raise_for_status()
        data = resp.json()
        for item in data["data"]:
            all_vecs.append(item["embedding"])
        print(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
        time.sleep(0.3)

    for chunk, vec in zip(chunks, all_vecs):
        chunk["embedding"] = vec
        chunk["embedding_model"] = model
        chunk["embedding_dim"] = len(vec)

    return chunks


# ─── OpenAI API ────────────────────────────────────────────────────────


def embed_openai(
    chunks: list[dict],
    model: str = "text-embedding-3-small",
) -> list[dict]:
    from openai import OpenAI

    api_key = read_api_key("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env or environment")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    texts = [c["text"] for c in chunks]
    all_vecs = []

    print(f"Backend: OpenAI  |  Model: {model}")
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=model, input=batch)
        all_vecs.extend(r.embedding for r in resp.data)
        print(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
        time.sleep(0.2)

    for chunk, vec in zip(chunks, all_vecs):
        chunk["embedding"] = vec
        chunk["embedding_model"] = model
        chunk["embedding_dim"] = len(vec)

    return chunks


# ─── TF-IDF (local, no ML framework needed) ───────────────────────────


def embed_tfidf(
    chunks: list[dict],
    model: str = "tfidf",
    max_features: int = 256,
) -> list[dict]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    texts = [c["text"] for c in chunks]
    print(f"Backend: TF-IDF  |  dim: {max_features}")

    vec = TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=(1, 2),
    )
    embeddings = vec.fit_transform(texts).toarray()
    print(f"  vocabulary size: {len(vec.vocabulary_)}")

    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
        chunk["embedding_model"] = f"{model}_dim{max_features}"
        chunk["embedding_dim"] = len(emb)

    return chunks


# ─── Save ──────────────────────────────────────────────────────────────


def save(chunks: list[dict]):
    EMBEDDINGS_PATH.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Saved: {EMBEDDINGS_PATH}")

    try:
        import numpy as np
        vecs = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        np.save(str(EMBEDDINGS_NPY_PATH), vecs)
        print(f"Saved: {EMBEDDINGS_NPY_PATH} ({vecs.shape})")
    except ImportError:
        print("numpy not available; skipping .npy export")

    print(f"\nDone — {len(chunks)} chunks embedded, dim={chunks[0]['embedding_dim']}")


# ─── CLI ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser("Embed scholarship chunks for RAG")
    parser.add_argument(
        "--backend",
        default="openrouter",
        choices=["openrouter", "openai", "tfidf"],
        help="Embedding backend (default: openrouter — uses OPENROUTER_API_KEY from .env)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (default depends on backend)",
    )
    parser.add_argument(
        "--input",
        default=str(CHUNKS_PATH),
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Limit chunks for testing (default: all)",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=256,
        help="TF-IDF max features / embedding dimension (default: 256)",
    )
    args = parser.parse_args()

    chunks = load_chunks(Path(args.input))
    if args.max_chunks > 0:
        chunks = chunks[: args.max_chunks]
        print(f"Testing with {len(chunks)} chunks")

    backends = {
        "openrouter": (embed_openrouter, "openai/text-embedding-3-small"),
        "openai": (embed_openai, "text-embedding-3-small"),
        "tfidf": (embed_tfidf, "tfidf"),
    }

    fn, default_model = backends[args.backend]
    model = args.model or default_model

    kwargs = {}
    if args.backend == "tfidf":
        kwargs["max_features"] = args.max_features

    chunks = fn(chunks, model=model, **kwargs)
    save(chunks)


if __name__ == "__main__":
    main()
