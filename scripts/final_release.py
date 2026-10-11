"""Seal FINAL bundles, then verify fresh installation and the extracted application."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile

import httpx
from pypdf import PdfReader

from package_release import allowed, create

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release"
sys.path.insert(0, str(ROOT))
NAMES = ("NeuroGene_Atlas_Source_FINAL.zip", "NeuroGene_Atlas_Research_Results_FINAL.zip")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package():
    tests = json.loads((ROOT / "results/validation/phase5/tests.json").read_text())
    reproduction = json.loads((ROOT / "results/validation/phase5/reproduction.json").read_text())
    assert tests["phase"] == 5 and tests["status"] == reproduction["status"] == "passed"
    pdf = ROOT / "results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.pdf"
    pages = PdfReader(pdf).pages
    text = " ".join(p.extract_text() for p in pages)
    for heading in ("Final Scientific Audit", "Final Technical Audit", "Publication Readiness", "Dataset Comparison Summary", "Candidate Gene Evidence", "Final Test Results"):
        assert heading in text, heading
    assert (ROOT / "results/reports/NeuroGene_Atlas_Scientific_Report_FINAL.html").read_text().count('src="data:image/png;base64,') == 14
    source, research = [], []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not allowed(path):
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {"data", "results"}:
            research.append(path)
        elif relative.parts[0] in {"frontend", "backend", "scripts", "tests", "docs", "config"} or len(relative.parts) == 1:
            source.append(path)
    from backend.main import FINAL_DOCUMENTS
    for name in FINAL_DOCUMENTS:
        assert ROOT / name in source and ROOT / "results/final/audit" / name in research
    for study in ("GSE156496", "GSE132741", "GSE284723"):
        assert ROOT / "data/processed" / study / "count_matrix.csv" in research
        assert ROOT / "results" / study / "deseq2/dds.rds" in research
    assert ROOT / "results/final/audit/SCIENTIFIC_MANUSCRIPT_DRAFT.md" in research
    OUT.mkdir(exist_ok=True)
    reports = [create(NAMES[0], source), create(NAMES[1], research)]
    record = {"phase": 5, "status": "passed", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "archives": reports, "pdf_pages": len(pages), "critical_results": "verified",
              "clean_extraction": "Separate post-sealing final_extracted_validation.json; not inferred"}
    (OUT / "final_release_validation.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "RELEASE_MANIFEST_SHA256.txt").write_text("".join(f"{r['sha256']}  {Path(r['path']).name}\n" for r in reports))
    print(json.dumps(record, indent=2))


def verify():
    logs = OUT / "final_extracted_logs"
    if logs.exists():
        saved = OUT / "final_extracted_history" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        saved.parent.mkdir(exist_ok=True)
        shutil.move(str(logs), saved)
    logs.mkdir(parents=True)
    commands = []
    record = {"phase": 5, "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
              "commands": commands, "archives": [], "checks": {}, "fresh_dependency_install": True,
              "limitations": ["Same host, Chromium emulation and existing browser executable", "R fits not run again during extraction"]}
    destination = OUT / "final_extracted_validation.json"

    def persist():
        destination.write_text(json.dumps(record, indent=2) + "\n")

    def run(name, command, cwd, environment=None):
        log = logs / f"{name}.log"
        entry = {"command": [str(c) for c in command], "cwd": str(cwd), "environment": environment or {},
                 "started_utc": datetime.now(timezone.utc).isoformat(), "log": str(log.relative_to(ROOT))}
        print("Executing:", entry["command"], flush=True)
        with log.open("w") as handle:
            result = subprocess.run(entry["command"], cwd=cwd, env=dict(os.environ, **(environment or {})), stdout=handle, stderr=subprocess.STDOUT)
        entry.update(exit_code=result.returncode, status="passed" if result.returncode == 0 else "failed")
        commands.append(entry)
        record["checks"][name] = entry
        persist()
        result.check_returncode()
        return log.read_text()

    servers = []
    handles = []

    def server(name, command, cwd, url):
        handle = (logs / f"{name}.log").open("w")
        handles.append(handle)
        process = subprocess.Popen([str(c) for c in command], cwd=cwd, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        servers.append(process)
        commands.append({"command": [str(c) for c in command], "cwd": str(cwd), "pid": process.pid, "kind": "server", "url": url,
                         "log": str((logs / f"{name}.log").relative_to(ROOT))})
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"{name} exited before readiness")
            try:
                if httpx.get(url, timeout=2).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(.2)
        raise RuntimeError(f"{name} not ready")

    try:
        declared = {line.split()[1]: line.split()[0] for line in (OUT / "RELEASE_MANIFEST_SHA256.txt").read_text().splitlines()}
        with tempfile.TemporaryDirectory(prefix="neurogene-final-clean-") as folder:
            target = Path(folder)
            for name, manifest_name in zip(NAMES, ("SOURCE_RELEASE_MANIFEST.json", "RESEARCH_RELEASE_MANIFEST.json")):
                path = OUT / name
                assert sha(path) == declared[name], f"Archive SHA mismatch: {name}"
                with zipfile.ZipFile(path) as archive:
                    assert archive.testzip() is None
                    files = json.loads(archive.read(manifest_name))["sha256"]
                    assert set(archive.namelist()) == set(files) | {manifest_name}
                    assert len(archive.namelist()) == len(set(archive.namelist()))
                    for filename in archive.namelist():
                        relative = Path(filename)
                        assert not relative.is_absolute() and ".." not in relative.parts
                        assert not set(relative.parts) & {"node_modules", ".venv", ".git", ".next", "__pycache__", "release"}
                        if filename != manifest_name:
                            assert hashlib.sha256(archive.read(filename)).hexdigest() == files[filename]
                    archive.extractall(target)
                record["archives"].append({"archive": name, "sha256": declared[name], "files_verified": len(files), "crc": "passed"})
            persist()
            run("venv_create", [sys.executable, "-m", "venv", str(target / ".venv")], target)
            python = target / ".venv/bin/python"
            run("python_install", [python, "-m", "pip", "install", "-r", "backend/requirements.lock.txt"], target)
            run("pip_check", [python, "-m", "pip", "check"], target)
            output = run("python", [python, "-m", "unittest", "discover", "-s", "tests", "-v"], target)
            count = re.search(r"Ran (\d+) tests", output)
            record["python_tests"] = int(count.group(1)) if count else None
            frontend = target / "frontend"
            run("npm_install", ["npm", "ci"], frontend)
            run("typescript", ["npm", "run", "typecheck"], frontend)
            run("production_build", ["npm", "run", "build"], frontend, {"API_INTERNAL_URL": "http://127.0.0.1:8006"})
            server("backend", [python, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8006"], target, "http://127.0.0.1:8006/api/datasets")
            server("frontend", ["npm", "run", "start", "--", "--port", "3006"], frontend, "http://127.0.0.1:3006")
            sys.path.insert(0, str(ROOT / "scripts"))
            # The runner imports from the extracted checkout and verifies every route there.
            run("live_api", [python, "-c", "import sys;sys.path.insert(0,'scripts');import final_validate;final_validate.live_api('http://127.0.0.1:8006')"], target)
            shutil.copy2(target / "results/validation/phase5/live_api.json", logs / "live_api_results.json")
            run("playwright", ["npx", "playwright", "test"], frontend, {"E2E_BASE_URL": "http://127.0.0.1:3006"})
            browser = json.loads((frontend / "test-results/results.json").read_text())
            record["browser_stats"] = browser["stats"]
            assert browser["stats"]["unexpected"] == browser["stats"]["skipped"] == browser["stats"]["flaky"] == 0
            shutil.copy2(frontend / "test-results/results.json", logs / "playwright_results.json")
            record.update(status="passed", clean_paired_extraction=True, application_start_verified=True,
                          completed_utc=datetime.now(timezone.utc).isoformat())
            for process in servers:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
            servers.clear()
    except Exception as error:
        record.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        for process in servers:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        for handle in handles:
            handle.close()
        persist()
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("package", "verify"))
    args = parser.parse_args()
    package() if args.action == "package" else verify()
