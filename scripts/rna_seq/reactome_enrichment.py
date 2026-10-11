"""One-sided hypergeometric ORA on pinned Reactome mouse mappings."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/GSE156496/deseq2"
SOURCE_URL = "https://download.reactome.org/95/Ensembl2Reactome.txt"


def bh(values):
    values = np.asarray(values)
    order = np.argsort(values)
    adjusted = np.minimum(1, np.minimum.accumulate((values[order] * len(values) / np.arange(1, len(values) + 1))[::-1])[::-1])
    result = np.empty(len(values))
    result[order] = adjusted
    return result


def main(source=None):
    mapping_path = ROOT / "data/annotations/reactome_v95_mouse.tsv"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    prior_path = OUT / 'reactome_provenance.json'
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    if source is not None:
        with source.open() as handle:
            rows = [row for row in csv.reader(handle, delimiter="\t") if len(row) == 6 and row[5] == "Mus musculus" and row[0].startswith("ENSMUSG")]
        if not rows:
            raise ValueError("No mouse Ensembl mapping rows found")
        mapping = pd.DataFrame(rows, columns=["gene_id", "pathway_id", "url", "pathway", "evidence", "species"]).drop_duplicates()
        mapping.to_csv(mapping_path, sep="\t", index=False)
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        retrieved = datetime.now(timezone.utc).isoformat()
    else:
        expected = '08c5f75dfce1f2c4e3f0473504e401c0a4284106b378b33a2b193b07bb12a298'
        if hashlib.sha256(mapping_path.read_bytes()).hexdigest() != expected:
            raise ValueError('Cached Reactome 95 mapping checksum mismatch')
        mapping = pd.read_csv(mapping_path,sep='\t')
        source_hash = '14f294c529e95b156a3aec274d8f404467e81b6fbd2f4ad1fad8bd7ca0504323'
        retrieved = prior.get('downloaded_at_utc')
    assert mapping.species.eq('Mus musculus').all()
    de = pd.read_csv(OUT / "deseq2_D51_vs_WT_unshrunken.csv")
    # Genes with valid inference comprise the assay background; intersect with mapped genes.
    eligible = set(de.loc[de.padj.notna(), "gene_id"])
    universe = eligible & set(mapping.gene_id)
    deg = de[(de.padj < 0.05) & (de.log2FoldChange.abs() > 1)]
    results = []
    for direction in ["all", "up", "down"]:
        subset = deg if direction == "all" else deg[deg.log2FoldChange > 0] if direction == "up" else deg[deg.log2FoldChange < 0]
        selected = set(subset.gene_id) & universe
        terms = []
        for pathway_id, group in mapping.groupby("pathway_id"):
            genes = set(group.gene_id) & universe
            if not 10 <= len(genes) <= 500:
                continue
            overlap = genes & selected
            pvalue = float(hypergeom.sf(len(overlap) - 1, len(universe), len(genes), len(selected)))
            terms.append({"direction": direction, "pathway_id": pathway_id, "pathway": group.pathway.iloc[0],
                          "url": group.url.iloc[0], "overlap": len(overlap), "pathway_size": len(genes),
                          "selected_size": len(selected), "universe_size": len(universe), "pvalue": pvalue,
                          "fold_enrichment": len(overlap) / (len(selected) * len(genes) / len(universe)) if selected else 0,
                          "genes": ";".join(sorted(overlap))})
        adjusted = bh([term["pvalue"] for term in terms])
        for term, padj in zip(terms, adjusted):
            term["padj"] = float(padj)
        results.extend(terms)
    table = pd.DataFrame(results).sort_values(["direction", "padj", "pathway_id"])
    table.to_csv(OUT / "reactome_enrichment.csv", index=False)
    provenance = {"source_url": SOURCE_URL, "release": 95, "species": "Mus musculus", "downloaded_at_utc": retrieved,
                  "computed_at_utc": datetime.now(timezone.utc).isoformat(), "mapping_input":"Original download" if source is not None else "Checksum-verified cached mouse subset; original source hash inherited from verified extraction",
                  "source_sha256": source_hash, "mouse_mapping_sha256": hashlib.sha256(mapping_path.read_bytes()).hexdigest(),
                  "mouse_mapping_rows": len(mapping), "mapped_background": len(universe), "eligible_genes": len(eligible),
                  "eligible_unmapped": len(eligible - universe), "method": "One-sided hypergeometric over-representation; BH separately per direction across all eligible terms",
                  "background": "Genes with valid DESeq2 padj intersected with Reactome mapped genes", "term_size": [10, 500],
                  "deg_threshold": "unshrunken padj <0.05 and abs(log2FC)>1", "significant_terms": table[table.padj < 0.05].groupby("direction").size().to_dict(),
                  "limitations": "Mouse Reactome annotations include electronically inferred pathways. Mapping coverage and assay selection can bias enrichment; association does not demonstrate pathway activation."}
    (OUT / "reactome_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, nargs='?', help='Original Reactome 95 download; omit to use verified bundled mouse subset')
    main(parser.parse_args().source)
