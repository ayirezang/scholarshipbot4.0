"""
Clean the messy scholarships CSV for RAG ingestion.
Usage: python data/clean_scholarships.py
"""

import csv
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent
RAW_PATH_DEFAULT = "/Users/mac/Documents/AiClass/scholarships_messy_bulky.csv"
CLEAN_PATH = DATA_DIR / "scholarships_clean.csv"
DEDUPED_PATH = DATA_DIR / "scholarships_deduped.csv"

COLUMNS = [
    "Scholarship Name", "Provider/Sponsor", "Level", "Field of Study",
    "Country/Region", "Funding Type", "Need Based?", "Min Grade/GPA",
    "Deadline", "Amount", "Description", "Source",
]

TOPIC_KEYWORDS = {
    "scholarship", "grant", "bursary", "fellowship", "award",
    "fund", "program", "scholars", "competition",
}

INFO_TITLES = {
    "identifying scholarship scams", "frequently asked questions about scholarships",
    "common scholarship deadlines timeline", "requesting letters of recommendation",
    "writing a strong scholarship essay", "how to search for scholarships",
    "what happens if you lose eligibility", "combining scholarships with other financial aid",
    "what is a scholarship?", "merit-based vs need-based scholarships",
    "renewable vs one-time scholarships", "standard scholarship application requirements",
    "how scholarship funds are disbursed", "types of scholarships overview",
    "scholarships for international students", "scholarships for first-generation college students",
    "community and local scholarships", "stem scholarships",
    "are scholarships taxable?", "scholarship interview preparation",
    "n/a", "tbd",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_info_row(name: str) -> bool:
    if not name:
        return True
    cleaned = normalize(name).lower().rstrip("?.,;:!-")
    return cleaned in INFO_TITLES or cleaned.startswith("how ") or cleaned.startswith("what ") or cleaned.startswith("are ")


def is_actual_scholarship(row: dict) -> bool:
    name = (row.get("Scholarship Name") or "").strip()
    desc = (row.get("Description") or "").strip()
    if not name or name.upper() in ("N/A", "TBD", "NULL", ""):
        return False
    if is_info_row(name):
        return False
    if desc and desc.startswith("Q:"):
        return False
    if not desc and not row.get("Provider/Sponsor", "").strip():
        return False
    return True


def normalize_level(val: str) -> str:
    v = normalize(val).lower()
    mapping = {
        "undergraduate": "undergraduate", "ug": "undergraduate",
        "undergrad": "undergraduate", "bachelor's": "undergraduate",
        "bachelors": "undergraduate", "bachelor": "undergraduate",
        "postgraduate": "postgraduate", "postgrad": "postgraduate",
        "post graduate": "postgraduate", "master's": "postgraduate",
        "masters": "postgraduate", "master": "postgraduate",
        "phd": "phd", "doctoral": "phd", "doctorate": "phd",
        "high school": "high_school", "high_school": "high_school",
        "secondary school": "high_school", "secondary": "high_school",
        "hs": "high_school", "graduate": "postgraduate",
        "all levels": "all",
    }
    return mapping.get(v, v)


def normalize_field(val: str) -> str:
    v = normalize(val).lower()
    mapping = {
        "any": "any",
        "coding": "computer_science", "computer science": "computer_science",
        "cs": "computer_science", "software development": "computer_science",
        "writing": "writing", "creative writing": "writing",
        "art_design": "art_design", "art & design": "art_design", "art and design": "art_design",
        "art": "art_design", "design": "art_design",
        "athletics": "athletics", "sports": "athletics", "sport": "athletics",
        "business": "business", "entrepreneurship": "business",
        "medicine": "medicine", "med": "medicine", "medical": "medicine",
        "engineering": "engineering",
    }
    return mapping.get(v, v)


def normalize_funding(val: str) -> str:
    v = normalize(val).lower()
    if not v or v in ("tbc", "tbd", "n/a", "null", "unspecified", ""):
        return ""
    if v in ("full funding", "fully funded", "full-ride", "full_ride", "fullride",
             "100% funded", "fully_funded", "full_ride"):
        return "fully_funded"
    if v in ("partial funding", "partial_funding", "partially funded"):
        return "partial"
    return v


def normalize_need_based(val: str) -> str:
    v = normalize(val).lower()
    if v in ("yes", "y", "true", "1", "t"):
        return "yes"
    if v in ("no", "n", "false", "0", "f"):
        return "no"
    return ""


def clean_row(row: dict) -> dict:
    cleaned = {}
    for col in COLUMNS:
        raw = (row.get(col) or "").strip()
        cleaned[col] = normalize(raw)
    cleaned["Level"] = normalize_level(cleaned["Level"])
    cleaned["Field of Study"] = normalize_field(cleaned["Field of Study"])
    cleaned["Funding Type"] = normalize_funding(cleaned["Funding Type"])
    cleaned["Need Based?"] = normalize_need_based(cleaned["Need Based?"])
    return cleaned


def is_duplicate_of(existing: list[dict], candidate: dict) -> bool:
    c_name = normalize(candidate["Scholarship Name"]).lower()
    c_prov = normalize(candidate.get("Provider/Sponsor", "")).lower()
    for e in existing:
        e_name = normalize(e["Scholarship Name"]).lower()
        e_prov = normalize(e.get("Provider/Sponsor", "")).lower()
        if c_name == e_name and c_prov == e_prov:
            return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Clean messy scholarships CSV")
    parser.add_argument("--input", default=RAW_PATH_DEFAULT, help="Path to raw CSV")
    parser.add_argument("--output-dir", default=str(DATA_DIR), help="Output directory")
    args = parser.parse_args()

    raw_path = Path(args.input)
    if not raw_path.exists():
        print(f"ERROR: input file not found: {raw_path}")
        sys.exit(1)

    clean_path = Path(args.output_dir) / "scholarships_clean.csv"
    deduped_path = Path(args.output_dir) / "scholarships_deduped.csv"

    with open(raw_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Raw rows: {len(raw_rows)}")

    scholarships = []
    info_rows = 0
    empty_rows = 0

    for row in raw_rows:
        name = (row.get("Scholarship Name") or "").strip()
        if not name or name.upper() in ("N/A", "TBD", "NULL", ""):
            empty_rows += 1
            continue
        if is_info_row(name):
            info_rows += 1
            continue

        cleaned = clean_row(row)
        if is_actual_scholarship(cleaned):
            scholarships.append(cleaned)

    print(f"Info/FAQ rows removed: {info_rows}")
    print(f"Empty/placeholder rows removed: {empty_rows}")
    print(f"Actual scholarships after cleaning: {len(scholarships)}")

    with open(clean_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(scholarships)
    print(f"Cleaned CSV written to: {clean_path}")

    deduped = []
    dupe_count = 0
    for s in scholarships:
        if not is_duplicate_of(deduped, s):
            deduped.append(s)
        else:
            dupe_count += 1

    print(f"Duplicates removed: {dupe_count}")
    print(f"Unique scholarships: {len(deduped)}")

    with open(deduped_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(deduped)
    print(f"Deduped CSV written to: {deduped_path}")

    print("\n--- Unique Scholarship Names (deduped) ---")
    for s in deduped:
        print(f"  • {s['Scholarship Name']}")


if __name__ == "__main__":
    main()
