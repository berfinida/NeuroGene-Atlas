"""Build a LOCAL review candidate from frozen results; never approve or upload data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import main as api
from scripts.repository_audit import findings

OUT = ROOT / "results/deployment"
LOCAL = re.compile(r"/(?:Users|private|var/folders|opt/homebrew|Library)/|file:[/]{2}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def classify(name, data):
    if findings(data) or LOCAL.search(data.decode("utf-8", errors="ignore")) or name.endswith((".rds", ".log")) or name.startswith("results/validation/"):
        return "4_private", "Runtime/serialized evidence or machine-specific metadata; never expose verbatim"
    if name.startswith("data/") or "network" in name or "sessionInfo" in name or name.endswith(".zip"):
        return "3_review", "Contributor/provider rights, archive scope or provenance requires review"
    if name.endswith(".md") or name.endswith("summary.json"):
        return "1_summary", "Authored methods/aggregate summaries; proposed public scope, owner approval still required"
    return "2_derived", "Derived scientific outputs; license/attribution and owner approval required before exposure"


def sanitize(value):
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if isinstance(value, str) and LOCAL.search(value):
        return "[machine-specific metadata withheld; private provenance retained]"
    return value


def main(output=OUT):
    global OUT
    OUT = Path(output).resolve()
    if api.SETTINGS.mode != "research" or api.ROOT != ROOT:
        raise ValueError("Build candidate only from the original local research workspace")
    baseline = json.loads((ROOT / "results/validation/phase5/reproduction.json").read_text())["original_sha256"]
    for name, expected in baseline.items():
        assert sha((ROOT/name).read_bytes()) == expected, name
    OUT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / "release/NeuroGene_Atlas_Research_Results_FINAL.zip"
    assert sha(archive.read_bytes()) == "f211ba30301105074bde3d59596ca1645edadd1b1e993ab8f14f088f7751c3bd"
    inventory = []
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for item in bundle.infolist():
            data = bundle.read(item.filename)
            category, reason = classify(item.filename, data)
            inventory.append({"path": item.filename, "bytes": len(data), "sha256": sha(data), "category": category, "reason": reason})
    (OUT / "data_exposure_inventory.json").write_text(json.dumps(inventory, indent=2)+"\n")
    candidate = OUT / "public_candidate"
    if candidate.exists():
        raise ValueError("Candidate already exists; preserve it or explicitly choose a fresh output")
    candidate.mkdir()
    files = []

    def write(name, data, source=None, operation="byte-preserving copy"):
        if findings(data) or LOCAL.search(data.decode("utf-8", errors="ignore")):
            raise ValueError("Unsafe candidate metadata: " + name)
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        category, reason = classify(name, data)
        files.append({"path": name, "bytes": len(data), "sha256": sha(data),
                      "source": source or "verified existing API snapshot", "source_sha256": sha((ROOT/source).read_bytes()) if source else None,
                      "transformation": operation, "category": category, "review": reason})

    names = ["config/gse156496.json"]
    de = "results/GSE156496/deseq2/"
    names += [de+n for n in ("summary.json", "sample_metadata.csv", "pca_samples.csv", "sample_distances.csv",
                             "deseq2_D51_vs_WT_unshrunken.csv", "deseq2_D51_vs_WT_apeglm.csv",
                             "normalized_counts.csv", "vst_counts.csv", "reactome_enrichment.csv", "reactome_provenance.json", "report.md")]
    names += [de+f"figures/{stem}.{ext}" for stem in ("pca", "volcano", "ma", "heatmap", "sample_distance") for ext in ("png", "pdf")]
    names += ["results/discovery/"+n for n in ("network/edges.csv", "network/nodes_0.4.csv", "network/nodes_0.7.csv", "network/nodes_0.9.csv", "network/provenance.json",
                "replication/summary.json", "replication/comparison_default.csv", "replication/comparison_no_replacement.csv", "replication/pathway_comparison.csv",
                "replication/gene_comparison.csv", "replication/sensitivity.csv", "candidates/rankings.csv", "candidates/sensitivity.csv", "candidates/methods.json")]
    names += ["results/phase4/"+n for n in ("candidate_evidence.csv", "audit.json", "qc/fit_audit.json", "statistical_sensitivity.csv", "pathway_comparison.csv")]
    names += [f"results/phase4/qc/{study}_{kind}.csv" for study in ("GSE156496", "GSE132741", "GSE284723") for kind in ("pca", "distances")]
    names += ["results/reports/figures/"+f"{stem}.{ext}" for stem in ("effect_comparison", "replication_sensitivity", "candidate_sensitivity") for ext in ("png", "pdf")]
    names += ["SCIENTIFIC_AUDIT_REPORT.md", "SCIENTIFIC_MANUSCRIPT_DRAFT.md"]
    for name in names:
        data = (ROOT / name).read_bytes()
        operation = "byte-preserving copy"
        if name.endswith(".json"):
            cleaned = sanitize(json.loads(data))
            data = (json.dumps(cleaned, indent=2, ensure_ascii=True)+"\n").encode()
            operation = "JSON serialization; machine-path values withheld, scientific numeric values unchanged"
        write(name, data, name, operation)
    for study in ("GSE156496", "GSE132741", "GSE284723"):
        write(f"snapshots/{study}.json", (json.dumps(sanitize(api.study_dataset(study)), indent=2)+"\n").encode(),
              operation="Snapshot of existing verified study endpoint; raw count matrices not copied")
    write("snapshots/final_audit.json", (json.dumps(sanitize(api.final_audit()), indent=2)+"\n").encode(),
          operation="Aggregate existing reproduction audit; command logs and per-file runtime paths not copied")
    manifest = {"schema": 1, "version": "0.6.0-rc.1", "publication": "NOT APPROVED; LOCAL REVIEW CANDIDATE ONLY",
                "scientific_files_unchanged": len(baseline), "files": files,
                "original_research_archive_sha256": sha(archive.read_bytes()),
                "snapshot_input_sha256": baseline,
                "excluded": ["raw counts and GEO downloads", "RDS fits", "runtime logs", "bulk research/report archives", "publication collection"],
                "warning": "Exploratory mouse research, not clinical validation; GSE284723 GEO 10 / deposit 9 / article 8 unresolved",
                "attribution": {"STRING": "v12.0 / Mus musculus 10090; CC-BY-4.0; derived DEG-induced graph/metrics; provider terms require review", "Reactome": "v95 mouse mapping/enrichment; database data CC0; distinct illustration/software terms", "GEO": "GSE156496 / GSE132741 / GSE284723; public access is not blanket redistribution approval"}}
    (candidate / "PUBLIC_MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n")
    zipped = OUT / "NeuroGene_Atlas_Public_Results_REVIEW_ONLY.zip"
    with zipfile.ZipFile(zipped, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(candidate.rglob("*")):
            if path.is_file():
                bundle.write(path, str(path.relative_to(candidate)))
    summary = {"status": "local_candidate_prepared_not_publicly_approved", "archive_members": len(inventory),
               "inventory_categories": {c: sum(i["category"] == c for i in inventory) for c in sorted({i["category"] for i in inventory})},
               "candidate_files": len(files), "uncompressed_bytes": sum(f["bytes"] for f in files), "zip_bytes": zipped.stat().st_size,
               "zip_sha256": sha(zipped.read_bytes()), "manifest_sha256": sha((candidate/"PUBLIC_MANIFEST.json").read_bytes()),
               "scientific_files_unchanged": len(baseline), "numerical_transformations": "none; JSON redaction/serialization only", "public_upload": False}
    (OUT / "bundle_validation.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    main(parser.parse_args().output_dir)
