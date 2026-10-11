#!/usr/bin/env python3
"""Validate and prepare the GSE156496 bulk RNA-seq count matrix."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "gse156496.json"
RAW_COUNTS = ROOT / "data" / "raw" / "GSE156496" / "GSE156496_RNAseq_RawCountTable.txt.gz"
SERIES_MATRIX = ROOT / "data" / "raw" / "GSE156496" / "GSE156496_series_matrix.txt.gz"
PROCESSED = ROOT / "data" / "processed" / "GSE156496"
RESULTS = ROOT / "results" / "GSE156496"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def parse_series_metadata(path: Path) -> pd.DataFrame:
    rows: dict[str, list[list[str]]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row in reader:
            if not row:
                continue
            if row[0] == "!series_matrix_table_begin":
                break
            if row[0].startswith("!Sample_"):
                rows.setdefault(row[0], []).append(row[1:])

    accessions = [v.strip('"') for v in rows["!Sample_geo_accession"][0]]
    titles = [v.strip('"') for v in rows["!Sample_title"][0]]
    organisms = [v.strip('"') for v in rows["!Sample_organism_ch1"][0]]
    sources = [v.strip('"') for v in rows["!Sample_source_name_ch1"][0]]

    genotype_rows = [
        vals for vals in rows.get("!Sample_characteristics_ch1", [])
        if vals and vals[0].strip('"').startswith("genotype:")
    ]
    if not genotype_rows:
        raise ValueError("Could not locate genotype metadata in GEO series matrix.")
    genotypes = [v.strip('"').split(":", 1)[1].strip() for v in genotype_rows[0]]

    return pd.DataFrame(
        {
            "geo_accession": accessions,
            "title": titles,
            "organism": organisms,
            "source_name": sources,
            "geo_genotype": genotypes,
        }
    )


def validate_counts(df: pd.DataFrame, sample_columns: list[str]) -> list[str]:
    issues: list[str] = []
    required = {"GeneName", "Geneid", "Length", *sample_columns}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Count table missing required columns: {missing}")
    if df["Geneid"].duplicated().any():
        issues.append("Duplicated Ensembl gene IDs were detected.")
    if df["GeneName"].isna().any() or df["Geneid"].isna().any():
        issues.append("Missing gene names or gene IDs were detected.")
    count_values = df[sample_columns]
    if (count_values < 0).any().any():
        raise ValueError("Negative count values detected.")
    if not np.equal(count_values.to_numpy(), np.floor(count_values.to_numpy())).all():
        raise ValueError("Non-integer count values detected.")
    if (df["Length"] <= 0).any():
        issues.append("One or more genes have non-positive feature lengths.")
    return issues


def median_ratio_size_factors(counts: pd.DataFrame) -> pd.Series:
    values = counts.to_numpy(dtype=float)
    positive = values > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_values = np.where(positive, np.log(values), np.nan)
    geo_means = np.exp(np.nanmean(log_values, axis=1))
    eligible = np.isfinite(geo_means) & (geo_means > 0)
    ratios = counts.loc[eligible].div(geo_means[eligible], axis=0)
    return ratios.replace([np.inf, -np.inf], np.nan).median(axis=0)


def bh_adjust(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    ranked = p_values[order]
    n = len(p_values)
    adjusted = np.empty(n)
    running = 1.0
    for i in range(n - 1, -1, -1):
        running = min(running, ranked[i] * n / (i + 1))
        adjusted[order[i]] = running
    return np.clip(adjusted, 0, 1)


def normal_two_sided_p(z: np.ndarray) -> np.ndarray:
    return np.array([math.erfc(abs(float(v)) / math.sqrt(2.0)) for v in z])


def exploratory_de(counts: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    size_factors = median_ratio_size_factors(counts)
    normalized = counts.div(size_factors, axis=1)
    log_norm = np.log2(normalized + 1.0)
    wt = metadata.loc[metadata["condition"] == "WT", "count_column"].tolist()
    d51 = metadata.loc[metadata["condition"] == "D51", "count_column"].tolist()
    wt_values = log_norm[wt]
    d51_values = log_norm[d51]
    log2fc = d51_values.mean(axis=1) - wt_values.mean(axis=1)
    var_wt = wt_values.var(axis=1, ddof=1)
    var_d51 = d51_values.var(axis=1, ddof=1)
    se = np.sqrt((var_wt / len(wt)) + (var_d51 / len(d51))).replace(0, np.nan)
    z = (log2fc / se).replace([np.inf, -np.inf], np.nan).fillna(0).to_numpy()
    p_values = normal_two_sided_p(z)
    padj = bh_adjust(p_values)
    return pd.DataFrame(
        {
            "gene_id": counts.index,
            "gene_name": counts.attrs["gene_names"].reindex(counts.index).to_numpy(),
            "base_mean": normalized.mean(axis=1).to_numpy(),
            "log2_fold_change_D51_vs_WT": log2fc.to_numpy(),
            "p_value_normal_approximation": p_values,
            "adjusted_p_value_bh": padj,
            "method_note": "Exploratory log-normal approximation; not DESeq2 and not final DE evidence.",
        }
    ).sort_values("adjusted_p_value_bh")


def pca_from_log_counts(log_counts: pd.DataFrame) -> pd.DataFrame:
    matrix = log_counts.T
    centered = matrix - matrix.mean(axis=0)
    _, s, vt = np.linalg.svd(centered.to_numpy(), full_matrices=False)
    scores = centered.to_numpy() @ vt.T
    variance = (s ** 2) / (len(matrix) - 1)
    explained = variance / variance.sum()
    return pd.DataFrame(
        {
            "sample": matrix.index,
            "PC1": scores[:, 0],
            "PC2": scores[:, 1],
            "PC1_variance_explained": explained[0],
            "PC2_variance_explained": explained[1],
        }
    )


def main() -> None:
    config = read_config()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    expected = pd.DataFrame(config["expected_samples"])
    geo_metadata = parse_series_metadata(SERIES_MATRIX)
    metadata = expected.merge(geo_metadata, on="geo_accession", how="left", validate="one_to_one")
    if metadata["title"].isna().any():
        raise ValueError("Not all configured GSM accessions were found in the GEO series matrix.")
    metadata["validated_condition"] = metadata["geo_genotype"].map({"WT": "WT", "Delta 51": "D51"})
    if not (metadata["condition"] == metadata["validated_condition"]).all():
        raise ValueError("Configured sample conditions do not match GEO genotype metadata.")

    raw = pd.read_csv(RAW_COUNTS, sep="\t")
    sample_columns = metadata["count_column"].tolist()
    validation_issues = validate_counts(raw, sample_columns)

    counts = raw[["Geneid", *sample_columns]].set_index("Geneid")
    counts.attrs["gene_names"] = raw.set_index("Geneid")["GeneName"]
    counts.to_csv(PROCESSED / "count_matrix.csv")
    metadata.to_csv(PROCESSED / "sample_metadata.csv", index=False)

    library_sizes = counts.sum(axis=0).rename("library_size").reset_index()
    library_sizes.columns = ["sample", "library_size"]
    library_sizes = library_sizes.merge(metadata, left_on="sample", right_on="count_column")
    library_sizes.to_csv(RESULTS / "library_sizes.csv", index=False)

    low_count = config["low_count_filter"]
    keep = (counts >= low_count["minimum_count"]).sum(axis=1) >= low_count["minimum_samples"]
    filtered = counts.loc[keep]
    size_factors = median_ratio_size_factors(filtered)
    normalized = filtered.div(size_factors, axis=1)
    log_counts = np.log2(normalized + 1.0)
    log_counts.to_csv(RESULTS / "log2_sizefactor_normalized_counts.csv")

    pca = pca_from_log_counts(log_counts)
    pca = pca.merge(metadata, left_on="sample", right_on="count_column")
    pca.to_csv(RESULTS / "pca_samples.csv", index=False)

    distances = pd.DataFrame(
        np.linalg.norm(log_counts.T.to_numpy()[:, None, :] - log_counts.T.to_numpy()[None, :, :], axis=2),
        index=log_counts.columns,
        columns=log_counts.columns,
    )
    distances.to_csv(RESULTS / "sample_distances.csv")
    log_counts.corr().to_csv(RESULTS / "sample_correlations.csv")

    de = exploratory_de(filtered, metadata)
    de.to_csv(RESULTS / "exploratory_de_not_deseq2.csv", index=False)

    qc_summary = {
        "accession": config["accession"],
        "organism": config["organism"],
        "taxid": config["taxid"],
        "genome_build": config["genome_build"],
        "n_genes_raw": int(len(raw)),
        "n_genes_after_low_count_filter": int(len(filtered)),
        "n_samples": int(len(sample_columns)),
        "sample_columns": sample_columns,
        "library_size_min": int(library_sizes["library_size"].min()),
        "library_size_max": int(library_sizes["library_size"].max()),
        "size_factors": {k: float(v) for k, v in size_factors.items()},
        "validation_issues": validation_issues,
        "deseq2_status": "not_run_Rscript_unavailable_in_current_environment",
    }
    (RESULTS / "qc_summary.json").write_text(json.dumps(qc_summary, indent=2) + "\n")

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "inputs": {
            str(RAW_COUNTS.relative_to(ROOT)): sha256(RAW_COUNTS),
            str(SERIES_MATRIX.relative_to(ROOT)): sha256(SERIES_MATRIX),
        },
        "outputs": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in sorted([*PROCESSED.glob("*"), *RESULTS.glob("*")])
            if path.is_file() and path.name != "analysis_manifest.json"
        },
        "limitations": [
            "Rscript is unavailable in the current execution environment, so DESeq2 was not executed.",
            "exploratory_de_not_deseq2.csv is a computational smoke-test output, not final differential expression evidence.",
        ],
    }
    (RESULTS / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(qc_summary, indent=2))


if __name__ == "__main__":
    main()
