"""Bundle real DESeq2 artifacts with SHA-256 provenance and a readable report."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/GSE156496/deseq2"


def main():
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["status"] == "complete"
    inputs = [ROOT / "config/gse156496.json", ROOT / "scripts/rna_seq/deseq2_gse156496.R",
              ROOT / "environment.yml", *sorted((ROOT / "data/raw/GSE156496").glob("*.gz")),
              *sorted((ROOT / "data/processed/GSE156496").glob("*.csv"))]
    report = f"""# GSE156496 DESeq2 Analysis

Mus musculus tibialis anterior: 3 WT and 3 Dmd exon 51 knockout samples.
Positive log2 fold changes indicate higher expression in D51.

## Methods
Raw integer featureCounts counts; Ensembl mouse gene identifiers (mm10).
Design: ~ condition; WT reference. Keep genes with >=10 counts in >=3 samples.
DESeq2 median-ratio normalization, parametric dispersion fitting, Wald test,
Benjamini-Hochberg adjustment with independent filtering and default Cook's cutoff.
Unshrunken estimates define DEGs: padj <0.05 and |log2FC| >1.
Separate apeglm estimates provide stabilized effect sizes and retain original p-values.
VST with blind=FALSE; PCA uses 500 highest-variance genes; heatmap uses top 30 by padj.
The fold-change cutoff is post hoc, not a test against a nonzero effect-size null.

## Results
Raw genes: {summary['raw_genes']}; filtered/tested genes: {summary['genes_tested']}.
Genes with BH padj <0.05: {summary['significant_padj']}.
DEGs passing both thresholds: {summary['significant_padj_0_05_abs_lfc_1']}.
Upregulated: {summary['upregulated']}; downregulated: {summary['downregulated']}.

## Reproducibility
Versions: {json.dumps(summary['package_versions'])}.
Parameters, source URLs, validation checks: summary.json.
Full runtime: sessionInfo.txt. Input/output hashes: provenance.json.

## Limitations
One mouse dataset, n=3 per condition; no human clinical inference.
No batch covariate supplied by the configured metadata.
Exploratory Python statistics are separate and are not used in this report.
Reactome release 95 enrichment uses a valid-inference, mapped background and BH correction per direction. See reactome_provenance.json.
Phase 3 independent mouse replication, STRING associations and exploratory rankings are exported separately under results/discovery and results/reports.
"""
    (OUT / "report.md").write_text(report)
    files = inputs + [p for p in sorted(OUT.rglob("*")) if p.is_file() and p.name not in {"provenance.json", "analysis_report.zip"}]
    provenance = {"analysis": summary, "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    (OUT / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    with zipfile.ZipFile(OUT / "analysis_report.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.name != "analysis_report.zip":
                archive.write(p, p.relative_to(OUT))
    print(json.dumps({"report": str(OUT / "analysis_report.zip"), "hashed_files": len(files)}))


if __name__ == "__main__":
    main()
