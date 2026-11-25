#!/usr/bin/env python3
"""Download and verify the pinned B2W-Reviews01 source CSV."""
from __future__ import annotations

import argparse
import hashlib
import ssl
import tempfile
from pathlib import Path
from urllib.request import urlopen

import certifi


SOURCE_URL = (
    "https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/"
    "4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv"
)
SOURCE_SHA256 = "821fb0bf9f7230b0fba4e4f9fadd75a66d1a9ff0b1657810791d33007eb2ab38"
DEFAULT_PATH = Path("data/raw/b2w-reviews01/B2W-Reviews01.csv")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_b2w_source(path: Path = DEFAULT_PATH) -> Path:
    """Reuse a verified copy or download atomically from the pinned revision."""
    if path.exists():
        actual = sha256_file(path)
        if actual != SOURCE_SHA256:
            raise ValueError(f"B2W SHA-256 inesperado em {path}: {actual}")
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    context = ssl.create_default_context(cafile=certifi.where())
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".b2w-", suffix=".part", delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with urlopen(SOURCE_URL, context=context, timeout=60) as response:
                while chunk := response.read(1024 * 1024):
                    temporary.write(chunk)
        actual = sha256_file(temporary_path)
        if actual != SOURCE_SHA256:
            raise ValueError(f"B2W baixado com SHA-256 inesperado: {actual}")
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    print(f"B2W verificado: {ensure_b2w_source(args.output)}")


if __name__ == "__main__":
    main()
