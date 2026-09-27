#!/usr/bin/env python3
"""Execute a real OWASP ZAP baseline (passive) scan against a running local API.

Requires Docker and an API reachable from its container. No findings are
fabricated by this script; the HTML and JSON files come from ZAP itself.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        default="http://host.docker.internal:8000",
        help="Base URL reachable by the ZAP container",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()

    if shutil.which("docker") is None:
        parser.error("Docker não está instalado; nenhum relatório ZAP foi gerado")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        "docker", "run", "--rm", "-v", f"{output_dir}:/zap/wrk/:rw",
        "ghcr.io/zaproxy/zaproxy:stable", "zap-baseline.py",
        "-t", args.target, "-m", "1", "-T", "5",
        "-r", "zap_report.html", "-J", "zap_report.json",
    ]
    result = subprocess.run(command, check=False)
    if result.returncode == 3:
        print("O ZAP falhou; verifique os logs e a URL da API. Não use relatórios antigos.")
    elif result.returncode in (0, 1, 2):
        print(f"Relatórios reais do ZAP em {output_dir}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
