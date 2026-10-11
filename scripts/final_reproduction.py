"""Reconstruct three inputs and compare isolated R reruns without replacing evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/validation/phase5"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(old, new):
    left, right = pd.read_csv(old), pd.read_csv(new)
    pd.testing.assert_frame_equal(left, right, check_exact=False, rtol=1e-8, atol=1e-10)
    numeric = left.select_dtypes(include="number").columns
    delta = np.abs(left[numeric].to_numpy() - right[numeric].to_numpy())
    finite = delta[np.isfinite(delta)]
    return {"rows": len(left), "matched": True,
            "max_absolute_difference": float(finite.max()) if finite.size else 0.0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rscript", default="Rscript")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    preserved = [p for base in ("data", "results/GSE156496", "results/GSE132741", "results/GSE284723",
                                "results/phase4", "results/discovery", "results/publication")
                 for p in (ROOT / base).rglob("*") if p.is_file()]
    original = {str(p.relative_to(ROOT)): sha(p) for p in preserved}
    record = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
              "rtol": 1e-8, "atol": 1e-10, "commands": [], "studies": {},
              "environment": "New Python venv; existing pinned R 4.4.3 environment on the same host, not a second R installation"}
    destination = OUT / "reproduction.json"

    def run(command, cwd):
        index = len(record["commands"])
        log = OUT / f"reproduction_{index:02d}.log"
        entry = {"command": command, "cwd": str(cwd), "started_utc": datetime.now(timezone.utc).isoformat(),
                 "log": str(log.relative_to(ROOT))}
        print("Executing:", command, flush=True)
        with log.open("w") as handle:
            result = subprocess.run(command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT)
        entry["exit_code"] = result.returncode
        record["commands"].append(entry)
        destination.write_text(json.dumps(record, indent=2) + "\n")
        result.check_returncode()

    try:
        with tempfile.TemporaryDirectory(prefix="neurogene-reproduction-phase5-") as folder:
            scratch = Path(folder)
            for base in ("scripts", "config", "data/raw", "results/phase4/geo_review"):
                shutil.copytree(ROOT / base, scratch / base, ignore=shutil.ignore_patterns("__pycache__"))
            sys.path.insert(0, str(ROOT / "scripts"))
            from rna_seq.phase_a_gse156496 import parse_series_metadata, validate_counts
            cfg = json.loads((scratch / "config/gse156496.json").read_text())
            raw = pd.read_csv(scratch / "data/raw/GSE156496/GSE156496_RNAseq_RawCountTable.txt.gz", sep="\t")
            meta = pd.DataFrame(cfg["expected_samples"]).merge(
                parse_series_metadata(scratch / "data/raw/GSE156496/GSE156496_series_matrix.txt.gz"),
                on="geo_accession", validate="one_to_one")
            meta["validated_condition"] = meta.geo_genotype.map({"WT": "WT", "Delta 51": "D51"})
            assert (meta.condition == meta.validated_condition).all()
            validate_counts(raw, meta.count_column.tolist())
            inputs = scratch / "data/processed/GSE156496"
            inputs.mkdir(parents=True)
            raw.set_index("Geneid")[meta.count_column.tolist()].to_csv(inputs / "count_matrix.csv")
            meta.to_csv(inputs / "sample_metadata.csv", index=False)
            for script in ("prepare_independent", "prepare_third"):
                run([sys.executable, "-m", f"scripts.discovery.{script}"], scratch)
            for study in ("GSE156496", "GSE132741", "GSE284723"):
                prepared = {}
                for name in ("count_matrix.csv", "sample_metadata.csv"):
                    relative = Path("data/processed") / study / name
                    prepared[name] = compare(ROOT / relative, scratch / relative)
                script = {"GSE156496": "rna_seq/deseq2_gse156496.R", "GSE132741": "discovery/independent_deseq2.R",
                          "GSE284723": "discovery/third_deseq2.R"}[study]
                run([args.rscript, str(scratch / "scripts" / script)], scratch)
                relative = Path("results") / study / "deseq2"
                generated = scratch / relative
                tables = {p.name: compare(ROOT / relative / p.name, p)
                          for p in generated.glob("*.csv") if (ROOT / relative / p.name).exists()}
                stored = json.loads((ROOT / relative / "summary.json").read_text())
                fresh = json.loads((generated / "summary.json").read_text())
                versions = "package_versions" if study == "GSE156496" else "versions"
                assert stored[versions] == fresh[versions]
                if study == "GSE156496":
                    keys = ("genes_tested", "significant_padj_0_05_abs_lfc_1", "upregulated", "downregulated")
                elif study == "GSE132741":
                    keys = ("genes_tested", "degs", "up", "down", "no_replacement_degs", "outlier_replaced_genes")
                else:
                    keys = ("scenarios",)
                assert all(stored[key] == fresh[key] for key in keys)
                record["studies"][study] = {"inputs": prepared, "tables": tables, "versions": fresh[versions],
                                            "summary_verified": list(keys), "status": "passed"}
                destination.write_text(json.dumps(record, indent=2) + "\n")
        assert all(sha(ROOT / name) == expected for name, expected in original.items())
        record.update(status="passed", completed_utc=datetime.now(timezone.utc).isoformat(),
                      original_scientific_files_unchanged=len(original), original_sha256=original,
                      limitations=["Same host and R installation; not independent analyst/environment replication",
                                   "No FASTQ realignment, causal experiment or clinical validation",
                                   "Context-adjusted fit and figure bytes not regenerated in this rerun"])
    except Exception as error:
        record.update(status="failed", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        destination.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "studies": {k: len(v["tables"]) for k, v in record["studies"].items()}}, indent=2))


if __name__ == "__main__":
    main()
