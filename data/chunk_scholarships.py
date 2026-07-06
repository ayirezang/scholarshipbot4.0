"""
Chunking module for scholarship RAG pipeline.
Usage:  python data/chunk_scholarships.py
        python data/chunk_scholarships.py --strategy field
        python data/chunk_scholarships.py --strategy hybrid --overlap 50
"""

import csv
import json
import argparse
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent
CSV_PATH = DATA_DIR / "scholarships_deduped.csv"
CHUNKS_PATH = DATA_DIR / "chunks.json"
CHUNKS_CSV_PATH = DATA_DIR / "chunks.csv"

# ─── helpers ─────────────────────────────────────────────────────────────


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def non_empty(val: Any) -> bool:
    s = str(val).strip()
    return s not in ("", "n/a", "null", "none", "tbd", "tbc", "unspecified", "nan")


def fmt_field(name: str, val: Any) -> str:
    s = str(val).strip()
    if not s or s.upper() in ("N/A", "NULL", "TBD", "TBC", "NONE", "UNSPECIFIED", ""):
        return ""
    return f"{name}: {s}"


def token_estimate(text: str) -> int:
    return len(text.split())


def scholarship_context(row: dict) -> str:
    """Brief context prefix so each chunk can stand alone."""
    ctx = f"Scholarship: {row['Scholarship Name']}"
    if non_empty(row.get("Provider/Sponsor")):
        ctx += f"\nProvider: {row['Provider/Sponsor']}"
    if non_empty(row.get("Level")):
        ctx += f"\nLevel: {row['Level']}"
    if non_empty(row.get("Field of Study")):
        ctx += f"\nField: {row['Field of Study']}"
    if non_empty(row.get("Funding Type")):
        ctx += f"\nFunding: {row['Funding Type']}"
    return ctx


def make_chunk(
    row: dict,
    chunk_id: str,
    chunk_type: str,
    text: str,
    extra_meta: dict | None = None,
) -> dict:
    meta = {k: v for k, v in row.items() if non_empty(v)}
    if extra_meta:
        meta.update(extra_meta)
    return {
        "id": chunk_id,
        "scholarship_name": row["Scholarship Name"],
        "chunk_type": chunk_type,
        "text": text,
        "tokens": token_estimate(text),
        "metadata": meta,
    }


# ─── strategy: document ────────────────────────────────────────────────


def chunk_document(row: dict, overlap: int = 0) -> list[dict]:
    """One chunk per scholarship, optionally split with token overlap."""
    parts = [f"Scholarship: {row['Scholarship Name']}"]
    for col, val in row.items():
        if col == "Scholarship Name":
            continue
        if not non_empty(val):
            continue
        if col == "Description" and val:
            parts.append(str(val))
        elif val:
            parts.append(fmt_field(col, val))

    text = "\n".join(p for p in parts if p)
    tokens = text.split()
    base = slugify(row["Scholarship Name"])

    if overlap <= 0 or len(tokens) <= 200:
        return [
            make_chunk(row, base, "document", text)
        ]

    chunks = []
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + 200, len(tokens))
        chunk_text = " ".join(tokens[start:end])
        chunks.append(
            make_chunk(
                row,
                f"{base}__slide_{idx:03d}",
                "document",
                chunk_text,
                {"chunk_index": idx, "token_start": start, "token_end": end},
            )
        )
        idx += 1
        start += 200 - overlap
        if start >= len(tokens):
            break

    return chunks


# ─── strategy: field ────────────────────────────────────────────────────


def _overlap_text(ctx: str, detail: str, overlap: int) -> str:
    """Prepend context if overlap is set and detail is long enough."""
    if overlap > 0 and ctx:
        return f"{ctx}\n\n{detail}"
    return detail


def chunk_by_field(row: dict, overlap: int = 0) -> list[dict]:
    """One chunk per field. Overlap prepends scholarship context."""
    chunks = []
    base = slugify(row["Scholarship Name"])
    ctx = scholarship_context(row) if overlap > 0 else ""

    for col, val in row.items():
        if not non_empty(val):
            continue
        if col == "Scholarship Name":
            continue
        if col == "Description":
            text = _overlap_text(ctx, str(val).strip(), overlap)
            cid = f"{base}__description"
        else:
            text = f"{col}: {val}"
            if overlap > 0 and ctx:
                text = f"{ctx}\n\n{text}"
            cid = f"{base}__{slugify(col)}"

        chunks.append(
            make_chunk(row, cid, f"field:{col}", text)
        )

    return chunks


# ─── strategy: hybrid ───────────────────────────────────────────────────


def chunk_hybrid(row: dict, overlap: int = 0) -> list[dict]:
    """Summary chunk + field chunks. Overlap adds context to field chunks."""
    chunks = []
    base = slugify(row["Scholarship Name"])
    ctx = scholarship_context(row) if overlap > 0 else ""

    summary = f"Scholarship: {row['Scholarship Name']}"
    if non_empty(row.get("Description")):
        summary += f"\n{row['Description']}"
    if non_empty(row.get("Provider/Sponsor")):
        summary += f"\nProvider: {row['Provider/Sponsor']}"
    if non_empty(row.get("Level")):
        summary += f"\nLevel: {row['Level']}"
    if non_empty(row.get("Field of Study")):
        summary += f"\nField: {row['Field of Study']}"
    if non_empty(row.get("Funding Type")):
        summary += f"\nFunding: {row['Funding Type']}"

    tokens = summary.split()
    if overlap > 0 and len(tokens) > 200:
        start = 0
        idx = 0
        while start < len(tokens):
            end = min(start + 200, len(tokens))
            chunk_text = " ".join(tokens[start:end])
            chunks.append(
                make_chunk(
                    row,
                    f"{base}__summary_{idx:03d}",
                    "summary",
                    chunk_text,
                    {"chunk_index": idx, "token_start": start, "token_end": end},
                )
            )
            idx += 1
            start += 200 - overlap
    else:
        chunks.append(make_chunk(row, f"{base}__summary", "summary", summary))

    for col, val in row.items():
        if col in ("Scholarship Name", "Description", "Source"):
            continue
        if not non_empty(val):
            continue

        text = f"{col}: {val}"
        if overlap > 0 and ctx:
            text = f"{ctx}\n\n{text}"
        chunks.append(
            make_chunk(row, f"{base}__{slugify(col)}", f"field:{col}", text)
        )

    detail = str(row.get("Description", "")).strip()
    if detail:
        text = _overlap_text(ctx, detail, overlap)
        chunks.append(
            make_chunk(row, f"{base}__description", "field:Description", text)
        )

    return chunks


# ─── strategy: sliding window (token-based) ──────────────────────────────


def chunk_sliding_window(
    row: dict, chunk_size: int = 200, overlap: int = 40
) -> list[dict]:
    """Token-based sliding window over the full document text."""
    parts = [f"Scholarship: {row['Scholarship Name']}"]
    for col, val in row.items():
        if col == "Scholarship Name":
            continue
        if not non_empty(val):
            continue
        if col == "Description" and val:
            parts.append(str(val))
        elif val:
            parts.append(fmt_field(col, val))

    text = "\n".join(p for p in parts if p)
    tokens = text.split()
    chunks = []
    base = slugify(row["Scholarship Name"])

    if overlap <= 0 or chunk_size <= 0:
        chunk_size = len(tokens)

    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_text = " ".join(tokens[start:end])
        chunks.append(
            make_chunk(
                row,
                f"{base}__slide_{idx:03d}",
                "sliding_window",
                chunk_text,
                {"chunk_index": idx, "token_start": start, "token_end": end},
            )
        )
        idx += 1
        start += chunk_size - overlap
        if start >= len(tokens):
            break

    return chunks


# ─── orchestrator ──────────────────────────────────────────────────────


STRATEGIES = {
    "document": chunk_document,
    "field": chunk_by_field,
    "hybrid": chunk_hybrid,
    "sliding": chunk_sliding_window,
}


def chunk_all(
    rows: list[dict],
    strategy: str = "hybrid",
    overlap: int = 0,
    chunk_size: int = 200,
) -> list[dict]:
    fn = STRATEGIES.get(strategy)
    if not fn:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from: {list(STRATEGIES)}")

    chunks = []
    kwargs = {}
    if strategy == "sliding":
        kwargs = {"chunk_size": chunk_size, "overlap": overlap}
    else:
        kwargs = {"overlap": overlap}

    for row in rows:
        chunks.extend(fn(row, **kwargs))
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Chunk scholarship CSV for RAG")
    parser.add_argument(
        "--strategy",
        default="hybrid",
        choices=list(STRATEGIES),
        help="Chunking strategy (default: hybrid)",
    )
    parser.add_argument(
        "--input",
        default=str(CSV_PATH),
        help=f"Input CSV path (default: {CSV_PATH})",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=0,
        help="Overlap tokens or context lines (default: 0 = no overlap)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=200,
        help="Max tokens per chunk for sliding strategy (default: 200)",
    )
    args = parser.parse_args()

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} scholarships from {args.input}")
    chunks = chunk_all(
        rows,
        strategy=args.strategy,
        overlap=args.overlap,
        chunk_size=args.chunk_size,
    )
    print(
        f"Strategy: {args.strategy}"
        f"  |  overlap: {args.overlap}"
        f"  |  chunk_size: {args.chunk_size if args.strategy == 'sliding' else 'N/A'}"
    )
    print(f"Chunks created: {len(chunks)}")

    print(f"\nToken stats:")
    sizes = [c["tokens"] for c in chunks]
    print(f"  min:   {min(sizes)}")
    print(f"  max:   {max(sizes)}")
    print(f"  mean:  {sum(sizes) / len(sizes):.0f}")
    print(f"  total: {sum(sizes)} tokens across all chunks")

    CHUNKS_PATH.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote JSON: {CHUNKS_PATH}")

    CHUNK_FIELDS = ["id", "scholarship_name", "chunk_type", "text", "tokens"]
    with open(CHUNKS_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CHUNK_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(chunks)
    print(f"Wrote CSV:  {CHUNKS_CSV_PATH}")

    print(f"\nSample chunk (first):")
    sample = chunks[0]
    print(f"  id:    {sample['id']}")
    print(f"  type:  {sample['chunk_type']}")
    print(f"  text:  {sample['text'][:200]}...")
    print(f"  tokens: {sample['tokens']}")

    if args.overlap > 0:
        print(f"\nOverlap sample (second chunk):")
        if len(chunks) > 1:
            s2 = chunks[1]
            print(f"  id:    {s2['id']}")
            print(f"  type:  {s2['chunk_type']}")
            print(f"  text:  {s2['text'][:200]}...")


if __name__ == "__main__":
    main()
