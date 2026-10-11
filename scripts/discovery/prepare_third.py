"""Prepare the deposited conditional-knockout counts without rounding or imputation."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    accession = "GSE284723"
    review = json.loads((ROOT / "results/phase4/geo_review/GSE284723.json").read_text())
    raw = ROOT / "data/raw" / accession / f"{accession}_rawCounts.xlsx"
    counts = pd.read_excel(raw, sheet_name="raw counts", engine="openpyxl")
    summary_rows = counts.EnsemblID.astype(str).str.startswith("__")
    summaries = counts.loc[summary_rows].copy()
    counts = counts.loc[~summary_rows].copy()
    original = counts.pop("EnsemblID").astype(str)
    assert original.str.fullmatch(r"ENSMUSG\d+\.\d+").all()
    identifiers = original.str.replace(r"\.\d+$", "", regex=True)
    assert not identifiers.duplicated().any()
    values = counts.to_numpy()
    assert np.isfinite(values).all() and (values >= 0).all()
    assert (values == np.floor(values)).all() and values.max() < np.iinfo(np.int32).max
    samples = {s["title"].lower(): s for s in review["samples"]}
    metadata = []
    for column in counts.columns:
        sample = samples[column.replace(" ", "").lower()]
        fields = sample["characteristics"]
        assert sample["species"] == "Mus musculus" and fields["cell type"] == "TA muscle"
        genotype = fields["genotype"]
        assert genotype in ("Dmd flox52/Y", "Dmd flox52/Y: HSA mKO")
        metadata.append(dict(count_column=column, accession=sample["accession"],
                             condition="mKO" if "HSA mKO" in genotype else "Control",
                             genotype=genotype, age=fields["age"], tissue=fields["cell type"],
                             organism=sample["species"], sex_reported="not reported",
                             independent_animal_id_reported="not reported"))
    assert len(metadata) == len(samples) == 9
    frame = pd.DataFrame(metadata)
    assert frame.condition.value_counts().to_dict() == {"Control": 5, "mKO": 4}
    out = ROOT / "data/processed" / accession
    out.mkdir(parents=True, exist_ok=True)
    summaries.to_csv(out / "htseq_summary_rows.csv", index=False)
    counts.index = pd.Index(identifiers, name="gene_id")
    counts.astype("int64").to_csv(out / "count_matrix.csv")
    frame.to_csv(out / "sample_metadata.csv", index=False)
    pd.DataFrame({"gene_id": identifiers, "original_gene_id": original}).to_csv(out / "identifier_bridge.csv", index=False)
    files = [raw, ROOT / "data/raw" / accession / f"{accession}_series_matrix.txt.gz",
             out / "count_matrix.csv", out / "sample_metadata.csv", out / "identifier_bridge.csv"]
    provenance = dict(accession=accession, source=review["source_url"],
                      count_source=review["supplementary_files"][0], genes=len(counts), samples=9,
                      excluded_htseq_summary_rows=summaries.EnsemblID.tolist(),
                      annotation="GRCm39 Gencode M32", identifier_rule="Remove Ensembl version suffix only; no duplicates permitted",
                      discrepancies=["GEO design says five per group; nine libraries deposited (5 controls, 4 mKO).",
                                     "Design prose says expected counts; processing specifies HTSeq-count and supplied values are integers."],
                      files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
