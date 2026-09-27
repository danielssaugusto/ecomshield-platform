"""Execute a real OWASP ZAP baseline (passive) scan against a running local API.

Requires Docker or a portable ZAP installation. No findings are fabricated by
this script; the HTML and JSON files come from ZAP itself.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


def run_native(
    zap_home: Path, target: str, output_dir: Path, import_openapi: bool,
) -> int:
    """Run passive-only Automation Framework jobs with a portable ZAP install."""
    executable = zap_home / "zap.sh"
    if not executable.is_file():
        raise FileNotFoundError(f"Executável do ZAP não encontrado: {executable}")

    # JSON strings are also valid YAML strings, avoiding unsafe interpolation.
    url = json.dumps(target)
    report_dir = json.dumps(str(output_dir))
    openapi_job = f"""  - type: openapi
    parameters:
      apiUrl: {json.dumps(target + '/openapi.json')}
      targetUrl: {url}
      context: EcomShield
""" if import_openapi else ""
    plan = f"""env:
  contexts:
    - name: EcomShield
      urls: [{url}]
  parameters:
    failOnError: true
    failOnWarning: false
    progressToStdout: true
jobs:
  - type: requestor
    requests:
      - url: {json.dumps(target + '/health')}
        responseCode: 200
      - url: {json.dumps(target + '/openapi.json')}
        responseCode: 200
      - url: {json.dumps(target + '/docs')}
        responseCode: 200
      - url: {json.dumps(target + '/redoc')}
        responseCode: 200
      - url: {json.dumps(target + '/static/swagger-ui-bundle.js')}
        responseCode: 200
      - url: {json.dumps(target + '/static/swagger-ui.css')}
        responseCode: 200
      - url: {json.dumps(target + '/static/redoc.standalone.js')}
        responseCode: 200
      - url: {json.dumps(target + '/users/me')}
        responseCode: 401
{openapi_job}  - type: passiveScan-wait
    parameters:
      maxDuration: 5
  - type: report
    parameters:
      template: traditional-html
      reportDir: {report_dir}
      reportFile: zap_report.html
      reportTitle: EcomShield TP2 - ZAP Passive Scan
  - type: report
    parameters:
      template: traditional-json
      reportDir: {report_dir}
      reportFile: zap_report.json
      reportTitle: EcomShield TP2 - ZAP Passive Scan
"""
    with tempfile.TemporaryDirectory(prefix="ecomshield-zap-") as temporary:
        temp_root = Path(temporary)
        plan_path = temp_root / "plan.yaml"
        zap_data_dir = temp_root / "home"
        zap_data_dir.mkdir()
        plan_path.write_text(plan, encoding="utf-8")
        command = [
            "sh", str(executable), "-cmd", "-dir", str(zap_data_dir),
            "-autorun", str(plan_path),
        ]
        result = subprocess.run(
            command, check=False, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, errors="replace",
        )
        (output_dir / "zap_scan.log").write_text(result.stdout, encoding="utf-8")
        print(result.stdout[-4000:])
        return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        help="Base URL da API; o padrão depende do modo Docker ou portátil",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument(
        "--zap-home", type=Path,
        help="Diretório do ZAP portátil; quando omitido, usa a imagem Docker oficial",
    )
    parser.add_argument(
        "--import-openapi", action="store_true",
        help="Explora endpoints da especificação; pode enviar POSTs. Use só com banco descartável.",
    )
    args = parser.parse_args()

    target = args.target or (
        "http://127.0.0.1:8000" if args.zap_home
        else "http://host.docker.internal:8000"
    )

    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        parser.error("--target deve ser uma URL HTTP(S) completa")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.zap_home:
        status = run_native(
            args.zap_home.resolve(), target.rstrip("/"), output_dir,
            args.import_openapi,
        )
    else:
        if args.import_openapi:
            parser.error("--import-openapi é suportado apenas no modo ZAP portátil")
        if shutil.which("docker") is None:
            parser.error("Docker não está instalado; use --zap-home com um ZAP portátil")
        command = [
            "docker", "run", "--rm", "-v", f"{output_dir}:/zap/wrk/:rw",
            "ghcr.io/zaproxy/zaproxy:stable", "zap-baseline.py",
            "-t", target, "-m", "1", "-T", "5",
            "-r", "zap_report.html", "-J", "zap_report.json",
        ]
        status = subprocess.run(command, check=False).returncode

    reports_exist = all(
        (output_dir / name).is_file()
        for name in ("zap_report.html", "zap_report.json")
    )
    if reports_exist and (status == 0 or (not args.zap_home and status in {1, 2})):
        print(f"Relatórios reais do ZAP em {output_dir} (código de saída: {status})")
    else:
        print("Scan incompleto; verifique os logs e não use relatórios parciais.")
        return status or 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
