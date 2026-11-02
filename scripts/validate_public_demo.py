"""Validate a local review candidate against real research services, never publish it."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://127.0.0.1:8010")
    parser.add_argument("--research-url", default="http://127.0.0.1:8008")
    parser.add_argument("--bundle-dir", type=Path, default=ROOT/"results/deployment/rc1")
    parser.add_argument("--out-dir", type=Path, default=ROOT/"results/validation/phase6_20261102")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    record = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
              "mode": "local preview, not public deployment", "requests": []}
    try:
        folder = args.bundle_dir / "public_candidate"
        manifest = json.loads((folder/"PUBLIC_MANIFEST.json").read_text())
        with zipfile.ZipFile(args.bundle_dir/"NeuroGene_Atlas_Public_Results_REVIEW_ONLY.zip") as archive:
            assert archive.testzip() is None
            assert set(archive.namelist()) == {f["path"] for f in manifest["files"]} | {"PUBLIC_MANIFEST.json"}
            for item in manifest["files"]:
                assert hashlib.sha256(archive.read(item["path"])).hexdigest() == item["sha256"]
                assert hashlib.sha256((folder/item["path"]).read_bytes()).hexdigest() == item["sha256"]
        for name, expected in manifest["snapshot_input_sha256"].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
        record["candidate_files_verified"] = len(manifest["files"])
        record["scientific_files_unchanged"] = len(manifest["snapshot_input_sha256"])
        with httpx.Client(base_url=args.api_url, timeout=30) as demo, httpx.Client(base_url=args.research_url, timeout=60) as research:
            def request(path, status=200):
                response = demo.get(path)
                assert response.status_code == status, (path, response.status_code)
                assert "X-Request-ID" in response.headers
                record["requests"].append({"path": path, "status": status, "bytes": len(response.content)})
                return response
            for path in ("/healthz", "/readyz", "/api/runtime"):
                request(path)
            assert request("/api/runtime").json()["mode"] == "preview"
            paths = ["datasets", "qc", "genes", "gene-search?q=Dmd", "expression/ENSMUSG00000045103", "volcano", "pathways",
                     "replication", "replication/genes", "replication/pathways", "candidates", "evidence", "statistical-sensitivity"]
            for study in ("GSE156496", "GSE132741", "GSE284723"):
                paths.append(f"studies/{study}")
                for artifact in ("pca", "distances"):
                    request(f"/api/studies/{study}/download/{artifact}")
            for path in paths:
                actual = request("/api/"+path).json()
                reference = research.get("/api/"+path)
                reference.raise_for_status()
                assert actual == reference.json(), path
            for confidence, count in ((.4, 17872), (.7, 4646), (.9, 1612)):
                path = f"/api/network?confidence={confidence}"
                actual = request(path).json()
                reference = research.get(path).json()
                assert actual["total_nodes"] == 1408 and actual["total_edges"] == count
                expected = {n["gene_id"]: n for n in reference["nodes"]}
                assert {n["gene_id"] for n in actual["nodes"]} == set(expected)
                for node in actual["nodes"]:
                    for metric in ("degree", "degree_centrality", "pagerank", "betweenness", "community"):
                        assert np.isclose(node[metric], expected[node["gene_id"]][metric], rtol=1e-8, atol=1e-10), metric
            for path in ("/api/download/unshrunken", "/api/download/apeglm", "/api/download/pathways", "/api/figures/pca.png", "/api/network/export/nodes"):
                request(path)
            for path in ("/api/download/report", "/api/download/provenance", "/api/publication", "/api/studies/GSE284723/download/counts", "/api/expression/ENSMUSG00000045103?scale=raw"):
                request(path, 403)
            request("/api/network?confidence=0.5", 422)
            assert demo.post("/api/genes").status_code == 405
            assert demo.get("/healthz", headers={"Host": "untrusted.example"}).status_code == 400
        record.update(status="passed", numerical_comparison="Existing research API values equal; cached network metrics rtol 1e-8 / atol 1e-10",
                      bundle_manifest_sha256=hashlib.sha256((folder/"PUBLIC_MANIFEST.json").read_bytes()).hexdigest())
    except Exception as error:
        record.update(status="failed", error=str(error))
        raise
    finally:
        record["completed_utc"] = datetime.now(timezone.utc).isoformat()
        (args.out_dir/"public_demo_api.json").write_text(json.dumps(record, indent=2)+"\n")
        print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
