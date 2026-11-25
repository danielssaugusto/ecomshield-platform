"""Stream a reproducible, private ConsumerBR annotation pilot without labels.

The source is a large ZIP; HTTP range reads avoid downloading/extracting it.
Only the complaint text is exported. Company is a sampling stratum, not a label.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

import fsspec

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://zenodo.org/api/records/18022568/files/ConsumerBR.zip/content"
SOURCE_DOI = "10.5281/zenodo.18022568"
SOURCE_ARCHIVE_MD5 = "d301043b0dd0ad7658a6edcd42372c7a"
COMPANIES = (
    "Magazine Luiza - Loja Online",
    "Mercado Livre",
    "Americanas.com",
    "Casasbahia.com",
    "Amazon.com.br",
    "Shopee Brasil",
    "Submarino",
    "Carrefour.com",
)
ROWS_PER_COMPANY = 40
RESERVED_PER_COMPANY = 10
SCAN_ROWS = 30_000
SALT = "ecomshield-consumerbr-pilot-v1"
PRIVATE_DIR = ROOT / "outputs/tp3-consumerbr"
MANIFEST = ROOT / "reports/tp3_data/consumerbr_pilot_manifest.json"


def clean_text(value: str) -> str:
    """Collapse whitespace while preserving the published anonymization tags."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip()


def normalized_key(value: str) -> str:
    return clean_text(value).casefold()


def sampling_key(source_id: str) -> str:
    return hashlib.sha256(f"{SALT}:{source_id}".encode()).hexdigest()


def read_candidates(scan_rows: int) -> tuple[list[dict], dict]:
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    candidates: list[dict] = []
    with (
        fsspec.open(SOURCE_URL, mode="rb", block_size=1 << 20) as remote,
        zipfile.ZipFile(remote) as archive,
        archive.open("ConsumerBR.csv") as member,
    ):
        reader = csv.DictReader(io.TextIOWrapper(member, encoding="utf-8-sig", errors="replace"))
        expected = {"ID", "empresa", "reclamacao_labeled"}
        if expected.difference(reader.fieldnames or []):
            raise ValueError("O esquema ConsumerBR mudou.")
        for index, row in enumerate(reader):
            if index >= scan_rows:
                break
            company = row["empresa"]
            if company not in COMPANIES:
                continue
            counts[company] += 1
            complaint = clean_text(row["reclamacao_labeled"])
            if not 80 <= len(complaint) <= 1800:
                continue
            text_key = normalized_key(complaint)
            if text_key in seen:
                continue
            seen.add(text_key)
            source_id = row["ID"]
            if not re.fullmatch(r"[0-9a-f]{64}", source_id):
                raise ValueError("ID de origem inesperado.")
            candidates.append({
                "sample_id": f"cbr-{source_id[:16]}",
                "source_id": source_id,
                "company": company,
                "complaint_text": complaint,
                "rank": sampling_key(source_id),
            })
    return candidates, dict(counts)


def choose_rows(candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    by_company: dict[str, list[dict]] = {name: [] for name in COMPANIES}
    for row in candidates:
        by_company[row["company"]].append(row)
    chosen: list[dict] = []
    eligible_counts = {}
    for company in COMPANIES:
        rows = sorted(by_company[company], key=lambda row: row["rank"])
        eligible_counts[company] = len(rows)
        if len(rows) < ROWS_PER_COMPANY:
            raise ValueError(f"{company}: {len(rows)} elegíveis, mínimo {ROWS_PER_COMPANY}.")
        chosen.extend(rows[:ROWS_PER_COMPANY])
    if len({row["sample_id"] for row in chosen}) != len(chosen):
        raise ValueError("IDs truncados não são únicos.")
    development: list[dict] = []
    reserved: list[dict] = []
    for company in COMPANIES:
        group = sorted((row for row in chosen if row["company"] == company), key=lambda row: row["rank"])
        reserved.extend(group[:RESERVED_PER_COMPANY])
        development.extend(group[RESERVED_PER_COMPANY:])
    return sorted(development, key=lambda row: row["sample_id"]), sorted(reserved, key=lambda row: row["sample_id"]), eligible_counts


def write_private_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["sample_id", "source_id", "company", "complaint_text"])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-rows", type=int, default=SCAN_ROWS)
    args = parser.parse_args()
    if args.scan_rows < SCAN_ROWS:
        raise ValueError("O piloto validado exige pelo menos 30.000 linhas de origem.")
    candidates, raw_company_counts = read_candidates(args.scan_rows)
    development, reserved, eligible_counts = choose_rows(candidates)
    dev_path = PRIVATE_DIR / "pilot_development.csv"
    reserved_path = PRIVATE_DIR / "pilot_reserved_unlabeled.csv"
    write_private_csv(dev_path, development)
    write_private_csv(reserved_path, reserved)
    manifest = {
        "source_doi": SOURCE_DOI,
        "source_url": SOURCE_URL,
        "source_archive_md5_as_published": SOURCE_ARCHIVE_MD5,
        "source_license": "CC BY 4.0",
        "archive_verified_in_full": False,
        "first_source_rows_scanned": args.scan_rows,
        "selection": "exact company strata; unique 80–1800-character complaints; SHA-256 rank",
        "salt": SALT,
        "rows_per_company": ROWS_PER_COMPANY,
        "reserved_per_company": RESERVED_PER_COMPANY,
        "development_rows": len(development),
        "reserved_rows": len(reserved),
        "raw_company_counts": raw_company_counts,
        "eligible_company_counts": eligible_counts,
        "development_id_sha256": hashlib.sha256("\n".join(row["sample_id"] for row in development).encode()).hexdigest(),
        "reserved_id_sha256": hashlib.sha256("\n".join(row["sample_id"] for row in reserved).encode()).hexdigest(),
        "development_file_sha256": hashlib.sha256(dev_path.read_bytes()).hexdigest(),
        "reserved_file_sha256": hashlib.sha256(reserved_path.read_bytes()).hexdigest(),
        "human_intent_labels_available": False,
        "test_status": "reserved and unlabeled; do not use for model selection",
        "limitations": [
            "Convenience frame: first N rows of source, not a random sample of all ConsumerBR.",
            "Company-stratified complaints, not representative prevalence of live support.",
            "Published anonymization may leave residual personal information; keep private and review.",
            "Company and source metadata are sampling/audit fields, not intent labels or model features.",
        ],
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ConsumerBR: {len(development)} desenvolvimento; {len(reserved)} reservado sem rótulos.")
    print(f"Planilha-fonte privada: {dev_path}")
    print(f"Reserva privada: {reserved_path}")


if __name__ == "__main__":
    main()
