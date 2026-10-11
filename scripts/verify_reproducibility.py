"""Rebuild inputs from GEO, rerun DESeq2 in isolation, and compare without overwriting results."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from rna_seq.phase_a_gse156496 import parse_series_metadata, validate_counts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/GSE156496/deseq2"
VALIDATION = ROOT / "results/validation"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(rscript):
    VALIDATION.mkdir(parents=True, exist_ok=True)
    prior = json.loads((OUT / "provenance.json").read_text())
    mismatches = [name for name, expected in prior["sha256"].items() if digest(ROOT / name) != expected]
    raw_names = [name for name in prior["sha256"] if name.startswith("data/raw/")]
    if set(raw_names) & set(mismatches):
        raise ValueError("Original GEO input checksums changed")
    cfg = json.loads((ROOT / "config/gse156496.json").read_text())
    scratch = ROOT / ".runtime/reproduction"
    inputs = scratch / "processed"
    generated = scratch / "deseq2"
    inputs.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ROOT / "data/raw/GSE156496/GSE156496_RNAseq_RawCountTable.txt.gz", sep="\t")
    expected = pd.DataFrame(cfg["expected_samples"])
    geo = parse_series_metadata(ROOT / "data/raw/GSE156496/GSE156496_series_matrix.txt.gz")
    metadata = expected.merge(geo, on="geo_accession", validate="one_to_one")
    metadata["validated_condition"] = metadata.geo_genotype.map({"WT":"WT", "Delta 51":"D51"})
    assert (metadata.condition == metadata.validated_condition).all()
    validate_counts(raw, metadata.count_column.tolist())
    raw.set_index("Geneid")[metadata.count_column.tolist()].to_csv(inputs / "count_matrix.csv")
    metadata.to_csv(inputs / "sample_metadata.csv", index=False)
    for filename in ["count_matrix.csv", "sample_metadata.csv"]:
        pd.testing.assert_frame_equal(pd.read_csv(inputs / filename), pd.read_csv(ROOT / "data/processed/GSE156496" / filename))
    env = dict(os.environ, NEUROGENE_INPUT_DIR=str(inputs), NEUROGENE_OUTPUT_DIR=str(generated))
    cmd = [rscript, str(ROOT / "scripts/rna_seq/deseq2_gse156496.R")]
    with (VALIDATION / "deseq2_reproduction.log").open("w") as log:
        subprocess.run(cmd, cwd=tempfile.gettempdir(), env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    comparisons = {}
    for filename in ["deseq2_D51_vs_WT_unshrunken.csv", "deseq2_D51_vs_WT_apeglm.csv", "normalized_counts.csv", "vst_counts.csv", "pca_samples.csv", "sample_distances.csv", "sample_metadata.csv", "heatmap_row_zscores.csv"]:
        old = pd.read_csv(OUT / filename)
        new = pd.read_csv(generated / filename)
        pd.testing.assert_frame_equal(old, new, check_exact=False, rtol=1e-8, atol=1e-10)
        nums = old.select_dtypes(include="number").columns
        delta = np.abs(old[nums].to_numpy() - new[nums].to_numpy())
        comparisons[filename] = {"rows":len(old), "max_absolute_difference": float(np.nanmax(delta)), "matched":True}
    stored = json.loads((OUT / "summary.json").read_text())
    rerun = json.loads((generated / "summary.json").read_text())
    assert stored["package_versions"] == rerun["package_versions"]
    for key in ["genes_tested", "significant_padj", "significant_padj_0_05_abs_lfc_1", "upregulated", "downregulated"]:
        assert stored[key] == rerun[key]
    report = {"status":"passed", "command":cmd, "rtol":1e-8, "atol":1e-10, "original_input_sha256_verified":True,
              "prior_manifest_mismatches":mismatches, "explanation":"Previous bundle was stale after the prior rerun; numeric scientific results compared independently before refreshing provenance.",
              "package_versions":rerun["package_versions"], "comparisons":comparisons,
              "figure_comparison":"Files regenerated; byte equality not required for PDF timestamps or R serialized objects."}
    (VALIDATION / "reproducibility.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rscript", default="Rscript")
    main(parser.parse_args().rscript)
