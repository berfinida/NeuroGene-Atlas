"""Phase 5 validation ledger, separated from historical Phase 4 evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/validation/phase5"
sys.path.insert(0, str(ROOT))


def run(name, command, cwd=ROOT, environment=None):
    OUT.mkdir(parents=True, exist_ok=True)
    entry = {"command": command, "cwd": str(cwd), "environment": environment or {},
             "started_utc": datetime.now(timezone.utc).isoformat()}
    result = subprocess.run(command, cwd=cwd, env=dict(os.environ, **(environment or {})),
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path = OUT / f"{name}.log"
    path.write_text(result.stdout)
    entry.update(exit_code=result.returncode, status="passed" if result.returncode == 0 else "failed",
                 log=str(path.relative_to(ROOT)))
    ledger = OUT / "commands.json"
    previous = json.loads(ledger.read_text()) if ledger.exists() else []
    previous.append(entry)
    ledger.write_text(json.dumps(previous, indent=2) + "\n")
    print(result.stdout, flush=True)
    return entry, result.stdout


def live_api(base):
    paths = ["datasets", "qc", "genes", "genes/export", "expression/ENSMUSG00000045103",
             "gene-search?q=Dmd", "volcano", "pathways", "network", "network/export/nodes",
             "network/export/edges", "replication", "replication/genes", "replication/pathways",
             "candidates", "evidence", "evidence/compare?genes=ENSMUSG00000030789",
             "scientific-audit", "statistical-sensitivity", "publication", "final-audit"]
    from backend.main import DOWNLOADS, app
    paths += [f"download/{a}" for a in DOWNLOADS]
    paths += [f"figures/{a}.{ext}" for a in ("pca", "volcano", "ma", "heatmap", "sample_distance") for ext in ("png", "pdf")]
    paths += [f"research/figures/{a}.{ext}" for a in ("effect_comparison", "replication_sensitivity", "candidate_sensitivity") for ext in ("png", "pdf")]
    paths += [f"research/report/{ext}" for ext in ("html", "pdf")]
    paths += [f"discovery/download/{a}" for a in ("candidates", "sensitivity", "replication", "comparison", "network_provenance", "replication_sensitivity", "pathway_comparison")]
    paths += [f"phase4/download/{a}" for a in ("evidence", "sensitivity", "audit", "manuscript", "provenance", "pathways")]
    from backend.main import FINAL_DOCUMENTS
    paths += [f"final/download/{name}" for name in FINAL_DOCUMENTS]
    paths += [f"final/download/NeuroGene_Atlas_Scientific_Report_FINAL.{ext}" for ext in ("html", "pdf")]
    for study in ("GSE156496", "GSE132741", "GSE284723"):
        paths += [f"studies/{study}"] + [f"studies/{study}/download/{a}" for a in ("counts", "metadata", "unshrunken", "apeglm", "pca", "distances", "session")]
    checked = []
    with httpx.Client(base_url=base, timeout=60) as client:
        manifest = client.get("/api/publication")
        manifest.raise_for_status()
        paths += [f"publication/download/{name}" for f in manifest.json() for name in f["files"]]
        paths += ["publication/download/figure_manifest.json", "publication/download/NeuroGene_Atlas_Publication_Figures.zip"]
        for path in paths:
            response = client.get(f"/api/{path}")
            assert response.status_code == 200, (path, response.status_code)
            assert len(response.content) > 2, path
            if response.headers.get("content-type", "").startswith("application/json"):
                assert response.json() is not None
            checked.append({"path": path, "status": response.status_code, "bytes": len(response.content)})
        schema = client.get("/openapi.json").json()
    covered = {route.path for route in app.routes if route.path.startswith("/api/")
               and any(route.path_regex.fullmatch("/api/" + urlsplit(p["path"]).path) for p in checked)}
    expected = {p for p in schema["paths"] if p.startswith("/api/")}
    assert covered == expected, f"Untested route templates: {expected - covered}"
    record = {"status": "passed", "base_url": base, "requests": checked, "covered_templates": sorted(covered),
              "api_route_templates": len([p for p in schema["paths"] if p.startswith("/api/")]),
              "coverage": "Every implemented GET route template and every scientific download choice; actual server, not mocks"}
    (OUT / "live_api.json").write_text(json.dumps(record, indent=2) + "\n")
    return {"status": "passed", "exit_code": 0, "requests": len(checked), "api_route_templates": record["api_route_templates"],
            "command": [sys.executable, "scripts/final_validate.py", "--api-url", base, "--out-dir", str(OUT)], "log": str((OUT / "live_api.json").relative_to(ROOT))}


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT)
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:3005")
    parser.add_argument("--api-url", default="http://127.0.0.1:8005")
    args = parser.parse_args()
    OUT = args.out_dir.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.build_only:
        result, _ = run("production_build", ["npm", "run", "build"], ROOT / "frontend", {"API_INTERNAL_URL": args.api_url})
        (OUT / "build.json").write_text(json.dumps(result, indent=2) + "\n")
        sys.exit(result["exit_code"])
    prior = OUT / "tests.json"
    if prior.exists():
        saved = OUT / "history" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        saved.mkdir(parents=True)
        for name in ("tests.json", "python.log", "playwright.log", "playwright_results.json"):
            if (OUT / name).exists():
                shutil.copy2(OUT / name, saved / name)
    checks = {}
    checks["python"], output = run("python", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    count = re.search(r"Ran (\d+) tests", output)
    checks["python"]["tests_run"] = int(count.group(1)) if count else None
    checks["python"]["api_tests"] = len(re.findall(r"^test_\S+ \(test_\w+\.\w*(?:API|APIIntegration)\.", output, re.M))
    checks["python_dependencies"], _ = run("pip_check", [sys.executable, "-m", "pip", "check"])
    checks["typescript"], _ = run("typecheck", ["npm", "run", "typecheck"], ROOT / "frontend")
    checks["dependency_audit"], _ = run("dependency_audit", ["npm", "audit", "--omit=dev", "--json"], ROOT / "frontend")
    try:
        checks["live_api"] = live_api(args.api_url)
    except Exception as error:
        checks["live_api"] = {"status": "failed", "error": str(error), "exit_code": 1}
    checks["playwright"], _ = run("playwright", ["npx", "playwright", "test"], ROOT / "frontend", {"E2E_BASE_URL": args.base_url})
    browser = ROOT / "frontend/test-results/results.json"
    if browser.exists():
        shutil.copy2(browser, OUT / "playwright_results.json")
        checks["playwright"]["stats"] = json.loads(browser.read_text())["stats"]
    screenshots = OUT / "screenshots"
    screenshots.mkdir(exist_ok=True)
    for image in (ROOT / "frontend/test-results").glob("*.png"):
        shutil.copy2(image, screenshots / image.name)
    checks["production_build"] = json.loads((OUT / "build.json").read_text())
    record = {"phase": 5, "audit_scope": "GitHub preparation" if OUT.name == "github" else "Phase 5",
              "status": "passed" if all(c["status"] == "passed" for c in checks.values()) else "failed",
              "checked_at_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
              "limitations": ["Chromium desktop/mobile emulation; not full WCAG or real-device certification",
                              "No public-deployment penetration testing", "Docker availability checked separately"]}
    prior.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    sys.exit(0 if record["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
