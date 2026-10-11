"""Select WT/mdx bulk TA samples from official GEO metadata and harmonize exact unique symbols."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import httpx

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/GSE132741"
PROCESSED = ROOT / "data/processed/GSE132741"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE132nnn/GSE132741/matrix/GSE132741_series_matrix.txt.gz"
    matrix_path = RAW / "GSE132741_series_matrix.txt.gz"
    if not matrix_path.exists():
        response = httpx.get(url, timeout=60)
        response.raise_for_status()
        matrix_path.write_bytes(response.content)
    rows = {}
    with gzip.open(matrix_path, "rt") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if row and row[0].startswith("!Sample_"):
                rows.setdefault(row[0], []).append(row[1:])
    samples = []
    for i, gsm in enumerate(rows["!Sample_geo_accession"][0]):
        characteristics = {}
        for values in rows["!Sample_characteristics_ch1"]:
            if ":" in values[i]:
                key,value = values[i].split(":",1)
                characteristics[key.strip()] = value.strip()
        tissue = rows["!Sample_source_name_ch1"][0][i]
        group = characteristics.get("group")
        if "tibialis anterior" not in tissue.lower() or group not in {"WT","mdx"}:
            continue
        organism = rows["!Sample_organism_ch1"][0][i]
        if organism != "Mus musculus":
            raise ValueError("Unexpected species or age in selected cohort")
        if characteristics.get("week") != "30":
            continue
        genotype = characteristics.get("genotype/variation")
        if genotype != group:
            raise ValueError("Genotype and group disagree")
        supplementary = [vals[i] for key,values in rows.items() if key.startswith("!Sample_supplementary_file") for vals in values]
        count_urls = [s.replace("ftp://","https://") for s in supplementary if s.endswith("fragmentspergene.counts.txt.gz")]
        if len(count_urls) != 1:
            raise ValueError(f"No unique per-gene count file for {gsm}")
        filename = count_urls[0].rsplit("/",1)[1]
        path = RAW / filename
        if not path.exists():
            response = httpx.get(count_urls[0], timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
        samples.append({"geo_accession":gsm,"count_column":gsm,"condition":group,"mouse_id":characteristics["mouse id"],
                        "title":rows["!Sample_title"][0][i],"organism":organism,"tissue":tissue,"age_weeks":30,
                        "genotype":genotype,"source_url":count_urls[0],"filename":filename})
    metadata = pd.DataFrame(samples).sort_values(["condition","geo_accession"], ascending=[False,True])
    if metadata.mouse_id.duplicated().any() or min(metadata.condition.value_counts()) < 3:
        raise ValueError("Repeated animal or insufficient independent replicates")
    count_series = []
    for sample in metadata.itertuples():
        frame = pd.read_csv(RAW / sample.filename, sep="\t", header=None, names=["symbol","count"])
        frame = frame[~frame.symbol.str.startswith("__")]
        if frame.symbol.duplicated().any() or not np.isfinite(frame["count"]).all() or (frame["count"] < 0).any() or (frame["count"] % 1 != 0).any():
            raise ValueError("Invalid per-gene raw integer counts")
        count_series.append(frame.set_index("symbol")["count"].rename(sample.count_column))
    counts = pd.concat(count_series,axis=1)
    if counts.isna().any().any():
        raise ValueError("Gene universes differ across count files")
    annotation = pd.read_csv(ROOT / "data/raw/GSE156496/GSE156496_RNAseq_RawCountTable.txt.gz",sep="\t")[["Geneid","GeneName"]]
    unique = annotation[~annotation.GeneName.duplicated(keep=False) & ~annotation.Geneid.duplicated(keep=False)]
    bridge = unique[unique.GeneName.isin(counts.index)].set_index("GeneName").Geneid
    harmonized = counts.loc[bridge.index].copy()
    harmonized.index = bridge.to_numpy()
    harmonized.index.name = "Geneid"
    harmonized.to_csv(PROCESSED / "count_matrix.csv")
    metadata.to_csv(PROCESSED / "sample_metadata.csv",index=False)
    bridge.rename("gene_id").to_csv(PROCESSED / "symbol_bridge.csv")
    info = {"accession":"GSE132741","status":"counts_prepared", "geo_url":"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE132741",
            "species":"Mus musculus", "tissue":"tibialis anterior muscle", "reference":"WT", "case":"mdx", "genome_build":"mm10",
            "sample_groups":metadata.condition.value_counts().to_dict(),"n_unique_animals":int(metadata.mouse_id.nunique()),
            "selection":"Only GEO-labelled 30-week bulk TA WT and mdx; exclude blood, longitudinal blood, utrophin-altered genotypes, and four TA samples labelled 12 or 18 weeks despite the series description",
            "raw_gene_symbols":len(counts),"harmonized_genes":len(harmonized),"excluded_unmapped_or_ambiguous":len(counts)-len(harmonized),
            "mapping":"Exact case-sensitive symbols with unique Ensembl IDs in original mm10 featureCounts annotations; no alias guessing or many-to-many collapse",
            "processing_note":"GEO metadata mentions Cufflinks, while supplied fragmentspergene files contain unnormalized integer counts and HTSeq summary rows. Primary article PMC8033515 describes HTSeq-count. Summary rows are removed, counts are never rounded.",
            "heterogeneity":["mdx exon-23 nonsense model versus discovery exon-51 deletion", "30-week animals versus one-month discovery animals (original GEO sample metadata)", "Independent laboratory, cohort and library/quantification workflows", "Same tissue/species supports contextual replication, not interchangeable experimental designs"],
            "clinical_status":"Exploratory independent cross-model replication; not clinical validation",
            "sources":[url,"https://pmc.ncbi.nlm.nih.gov/articles/PMC8033515/"],
            "sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(RAW.glob("*.gz"))}}
    (PROCESSED / "provenance.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps({k:v for k,v in info.items() if k!="sha256"},indent=2))


if __name__ == "__main__":
    main()
