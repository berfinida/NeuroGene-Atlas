import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/GSE156496/deseq2"
app = FastAPI(title="NeuroGene Atlas", version="0.5.1")
DISCOVERY = ROOT / "results/discovery"


@app.middleware("http")
async def scientific_scope(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['X-Scientific-Scope'] = 'Exploratory mouse research; not clinical validation'
        response.headers['X-Cohort-Caution'] = 'GSE284723 sample-count discrepancy unresolved; third-study findings not validated headline evidence'
    return response


def records(frame):
    return json.loads(frame.to_json(orient="records"))


@lru_cache
def results(estimate: str = "unshrunken"):
    return pd.read_csv(OUT / f"deseq2_D51_vs_WT_{estimate}.csv")


@lru_cache
def expression_matrix(scale: str):
    path = ROOT / "data/processed/GSE156496/count_matrix.csv" if scale == "raw" else OUT / ("normalized_counts.csv" if scale == "normalized" else "vst_counts.csv")
    return pd.read_csv(path, index_col=0)


@app.get("/api/datasets")
def datasets():
    if not (OUT / "summary.json").exists():
        raise HTTPException(503, "DESeq2 has not completed")
    config = json.loads((ROOT / "config/gse156496.json").read_text())
    return {"dataset": config, "summary": json.loads((OUT / "summary.json").read_text()),
            "samples": records(pd.read_csv(OUT / "sample_metadata.csv"))}


def filtered(q, padj, lfc, direction, estimate, sort):
    frame = results(estimate)
    if q:
        frame = frame[frame.gene_id.str.contains(q, case=False, regex=False) | frame.gene_symbol.fillna("").str.contains(q, case=False, regex=False)]
    frame = frame[(frame.padj < padj) & (frame.log2FoldChange.abs() > lfc)]
    if direction != "all":
        frame = frame[frame.log2FoldChange > 0] if direction == "up" else frame[frame.log2FoldChange < 0]
    return frame.sort_values(sort, ascending=sort == "padj", na_position="last")


@app.get("/api/genes")
def genes(q: str = "", padj: float = Query(0.05, gt=0, le=1), lfc: float = Query(1, ge=0),
          direction: Literal["all", "up", "down"] = "all", estimate: Literal["unshrunken", "apeglm"] = "unshrunken",
          sort: Literal["padj", "log2FoldChange", "baseMean"] = "padj", offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    frame = filtered(q, padj, lfc, direction, estimate, sort)
    return {"total": len(frame), "rows": records(frame.iloc[offset:offset + limit])}


@app.get("/api/genes/export")
def export_genes(q: str = "", padj: float = Query(0.05, gt=0, le=1), lfc: float = Query(1, ge=0),
                 direction: Literal["all", "up", "down"] = "all", estimate: Literal["unshrunken", "apeglm"] = "unshrunken",
                 sort: Literal["padj", "log2FoldChange", "baseMean"] = "padj"):
    return Response(filtered(q, padj, lfc, direction, estimate, sort).to_csv(index=False), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="GSE156496_{estimate}_filtered.csv"'})


@app.get("/api/expression/{gene_id}")
def expression(gene_id: str, scale: Literal["raw", "normalized", "vst"] = "normalized"):
    matrix = expression_matrix(scale)
    if gene_id not in matrix.index:
        raise HTTPException(404, "Gene not available in this expression matrix")
    meta = pd.read_csv(OUT / "sample_metadata.csv")
    meta["expression"] = [float(matrix.loc[gene_id, sample]) for sample in meta.count_column]
    gene = results()[results().gene_id == gene_id]
    return {"gene_id": gene_id, "scale": scale, "statistics": records(gene), "samples": records(meta)}


@app.get("/api/gene-search")
def gene_search(q: str = Query(..., min_length=1)):
    frame = results()
    hits = frame[frame.gene_id.str.contains(q, case=False, regex=False) | frame.gene_symbol.fillna("").str.contains(q, case=False, regex=False)]
    return records(hits[["gene_id", "gene_symbol"]].head(20))


@app.get("/api/qc")
def qc():
    if not (OUT / "summary.json").exists():
        raise HTTPException(503, "DESeq2 research data are not installed")
    return {"pca": records(pd.read_csv(OUT / "pca_samples.csv")),
            "samples": records(pd.read_csv(OUT / "sample_metadata.csv")),
            "distances": json.loads(pd.read_csv(OUT / "sample_distances.csv", index_col=0).to_json()),
            "summary": json.loads((OUT / "summary.json").read_text())}


Study = Literal["GSE156496", "GSE132741", "GSE284723"]


@app.get("/api/studies/{study}")
def study_dataset(study: Study):
    folder = ROOT / "results" / study / "deseq2"
    cohort = next(c for c in json.loads((ROOT / "results/phase4/audit.json").read_text())["cohorts"]
                  if c["accession"] == study)
    name = "deseq2_D51_vs_WT_unshrunken.csv" if study == "GSE156496" else "unshrunken.csv"
    frame = pd.read_csv(folder / name)
    counts = pd.read_csv(ROOT / "data/processed" / study / "count_matrix.csv", index_col=0)
    meta = pd.read_csv(ROOT / "data/processed" / study / "sample_metadata.csv")
    if "accession" in meta:
        meta = meta.rename(columns={"accession": "geo_accession"})
    qc_folder = ROOT / "results/phase4/qc"
    fitted = pd.read_csv(qc_folder / f"{study}_samples.csv").set_index("sample")
    meta["library_size"] = meta.count_column.map(counts.sum())
    meta["fitted_library_size"] = meta.count_column.map(fitted.library_size)
    meta["size_factor"] = meta.count_column.map(fitted.size_factor)
    meta["median_cooks"] = meta.count_column.map(fitted.median_cooks)
    significant = (frame.padj < .05) & (frame.log2FoldChange.abs() > 1)
    return {"cohort": cohort, "summary": {"prepared_genes": len(counts), "genes_tested": len(frame),
            "valid_padj": int(frame.padj.notna().sum()), "degs": int(significant.sum()),
            "up": int((significant & (frame.log2FoldChange > 0)).sum()),
            "down": int((significant & (frame.log2FoldChange < 0)).sum())},
            "samples": records(meta), "pca": records(pd.read_csv(qc_folder / f"{study}_pca.csv")),
            "distances": json.loads(pd.read_csv(qc_folder / f"{study}_distances.csv", index_col=0).to_json()),
            "parameters": json.loads((folder / "summary.json").read_text()),
            "library_total_scope": "Prepared analysis-input gene set before low-count filtering; external unmapped symbols and HTSeq summary rows excluded"}


@app.get("/api/studies/{study}/download/{artifact}")
def study_download(study: Study, artifact: Literal["counts", "metadata", "unshrunken", "apeglm", "pca", "distances", "session"]):
    folder = ROOT / "results" / study / "deseq2"
    name = "deseq2_D51_vs_WT_" if study == "GSE156496" else ""
    paths = {"counts": ROOT / "data/processed" / study / "count_matrix.csv",
             "metadata": ROOT / "data/processed" / study / "sample_metadata.csv",
             "unshrunken": folder / f"{name}unshrunken.csv", "apeglm": folder / f"{name}apeglm.csv",
             "pca": ROOT / "results/phase4/qc" / f"{study}_pca.csv",
             "distances": ROOT / "results/phase4/qc" / f"{study}_distances.csv", "session": folder / "sessionInfo.txt"}
    path = paths[artifact]
    if not path.is_file():
        raise HTTPException(404, "Study artifact unavailable")
    return FileResponse(path, filename=f"{study}_{path.name}")


@app.get("/api/volcano")
def volcano(estimate: Literal["unshrunken", "apeglm"] = "unshrunken"):
    frame = results(estimate).dropna(subset=["padj"]).copy()
    frame["neglog10padj"] = -np.log10(frame.padj.clip(lower=1e-300))
    return records(frame[["gene_id", "gene_symbol", "log2FoldChange", "padj", "neglog10padj", "baseMean"]])


@app.get("/api/pathways")
def pathways(direction: Literal["all", "up", "down"] = "all", padj: float = Query(0.05, gt=0, le=1), q: str = ""):
    if not (OUT / "reactome_enrichment.csv").exists():
        raise HTTPException(503, "Reactome enrichment has not been generated")
    frame = pd.read_csv(OUT / "reactome_enrichment.csv")
    frame = frame[(frame.direction == direction) & (frame.padj < padj)]
    if q:
        frame = frame[frame.pathway.str.contains(q, case=False, regex=False)]
    return {"rows": records(frame), "provenance": json.loads((OUT / "reactome_provenance.json").read_text())}


DOWNLOADS = {"report": "analysis_report.zip", "methods": "report.md", "provenance": "provenance.json",
             "unshrunken": "deseq2_D51_vs_WT_unshrunken.csv", "apeglm": "deseq2_D51_vs_WT_apeglm.csv",
             "pathways": "reactome_enrichment.csv", "normalized": "normalized_counts.csv", "session": "sessionInfo.txt"}


@app.get("/api/download/{artifact}")
def download(artifact: str):
    if artifact not in DOWNLOADS or not (OUT / DOWNLOADS[artifact]).is_file():
        raise HTTPException(404, "Artifact unavailable")
    return FileResponse(OUT / DOWNLOADS[artifact], filename=DOWNLOADS[artifact])


@app.get("/api/figures/{name}")
def figure(name: str):
    if name not in {f"{figure}.{ext}" for figure in ["pca", "volcano", "ma", "heatmap", "sample_distance"] for ext in ["png", "pdf"]}:
        raise HTTPException(404, "Figure unavailable")
    path = OUT / "figures" / name
    if not path.is_file():
        raise HTTPException(404, "Figure unavailable")
    return FileResponse(path)


@app.get("/api/network")
def network(confidence: float = Query(.7, ge=.4, le=.99), limit: int = Query(100, ge=1, le=200), q: str = ""):
    from backend.discovery import network_payload
    if not (DISCOVERY / "network/edges.csv").exists():
        raise HTTPException(503, "STRING network unavailable")
    return network_payload(round(confidence,3),limit,q)


@app.get("/api/network/export/{table}")
def network_export(table: Literal["nodes","edges"], confidence: float = Query(.7,ge=.4,le=.99)):
    from backend.discovery import graph_tables
    nodes,edges = graph_tables(round(confidence,3))
    return Response((nodes if table=="nodes" else edges).to_csv(index=False),media_type="text/csv",
                    headers={"Content-Disposition":f'attachment; filename="STRING_mouse_{confidence}_{table}.csv"'})


@app.get("/api/replication")
def replication():
    path = DISCOVERY / "replication/summary.json"
    if not path.exists():
        raise HTTPException(503,"Independent evaluation not completed")
    summary = json.loads(path.read_text())
    summary["heterogeneity"] = [
        "D51 exon-51 deletion versus mdx exon-23 nonsense model",
        "Discovery age: 1 month (original GEO); external age: 30 weeks",
        "Sex not explicitly provided in GEO sample fields; external fasting and collection context differ",
        "Separate cohorts and processing workflows; same tissue/species, no pooling",
    ]
    return summary


@app.get("/api/replication/genes")
def replication_genes(q: str = "", subset: Literal["all","overlap","discordant"] = "overlap",
                      outliers: Literal["default","no_replacement"] = "default", offset: int = Query(0,ge=0), limit: int = Query(50,ge=1,le=200)):
    frame=pd.read_csv(DISCOVERY / f"replication/comparison_{outliers}.csv")
    both=(frame.padj_discovery<.05)&(frame.padj_external<.05)&(frame.log2FoldChange_discovery.abs()>1)&(frame.log2FoldChange_external.abs()>1)
    if subset!='all':
        frame=frame[both if subset=='overlap' else both&~frame.direction_agrees]
    if q:
        frame=frame[frame.gene_id.str.contains(q,case=False,regex=False)|frame.gene_symbol_discovery.fillna('').str.contains(q,case=False,regex=False)]
    frame=frame.sort_values(['padj_discovery','gene_id'])
    return {"total":len(frame),"rows":records(frame.iloc[offset:offset+limit])}


@app.get("/api/replication/pathways")
def replication_pathways():
    frame=pd.read_csv(DISCOVERY / "replication/pathway_comparison.csv")
    return records(frame[(frame.direction=='all')&frame.both_significant].sort_values('padj_discovery'))


@app.get("/api/research/figures/{name}")
def research_figure(name: str):
    if name not in {f'{stem}.{ext}' for stem in ['effect_comparison','replication_sensitivity','candidate_sensitivity'] for ext in ['png','pdf']}:
        raise HTTPException(404,'Figure unavailable')
    path=ROOT / 'results/reports/figures' / name
    if not path.is_file():
        raise HTTPException(404,'Figure unavailable')
    return FileResponse(path)


@app.get("/api/research/report/{format}")
def research_report(format: Literal['html','pdf']):
    path=ROOT / f'results/reports/NeuroGene_Atlas_Scientific_Report.{format}'
    if not path.exists():
        raise HTTPException(404,'Report not generated')
    return FileResponse(path,filename=path.name)


@app.get("/api/candidates")
def candidates(q: str = "", offset: int = Query(0,ge=0), limit: int = Query(50,ge=1,le=200),
               weighting: Literal["balanced","statistics","replication","no_network","no_pathway"] = "balanced"):
    path = DISCOVERY / "candidates/rankings.csv"
    if not path.exists():
        raise HTTPException(503,"Candidate prioritization unavailable")
    frame = pd.read_csv(path)
    if q:
        frame = frame[frame.gene_symbol.str.contains(q,case=False,regex=False)|frame.gene_id.str.contains(q,case=False,regex=False)]
    frame = frame.sort_values([f"score_{weighting}","gene_id"],ascending=[False,True])
    return {"rows":records(frame.iloc[offset:offset+limit]),"total":len(frame),
            "methods":json.loads((DISCOVERY / "candidates/methods.json").read_text())}


@app.get("/api/discovery/download/{artifact}")
def discovery_download(artifact: Literal["candidates","sensitivity","replication","comparison","network_provenance","replication_sensitivity","pathway_comparison"]):
    paths = {"candidates":"candidates/rankings.csv","sensitivity":"candidates/sensitivity.csv", "replication":"replication/summary.json",
             "comparison":"replication/gene_comparison.csv","network_provenance":"network/provenance.json",
             "replication_sensitivity":"replication/sensitivity.csv","pathway_comparison":"replication/pathway_comparison.csv"}
    path = DISCOVERY / paths[artifact]
    if not path.exists():
        raise HTTPException(404,"Discovery artifact unavailable")
    return FileResponse(path,filename=path.name)


PHASE4 = ROOT / "results/phase4"
PUBLICATION = ROOT / "results/publication"


@app.get("/api/evidence")
def evidence(q: str = "", stable: bool = False, offset: int = Query(0,ge=0), limit: int = Query(25,ge=1,le=100)):
    frame = pd.read_csv(PHASE4 / "candidate_evidence.csv")
    if q:
        frame = frame[frame.gene_id.str.contains(q,case=False,regex=False) | frame.gene_symbol.fillna("").str.contains(q,case=False,regex=False)]
    if stable:
        frame = frame[frame.three_study_filter_outlier_stable]
    return {"total":len(frame),"rows":records(frame.sort_values("rank_balanced").iloc[offset:offset+limit]),
            "ranking":"Preserved Phase 3 heuristic; third-study evidence not added to its score"}


@app.get("/api/evidence/compare")
def evidence_compare(genes: str = Query(...,max_length=200)):
    ids = genes.split(",")
    if not 1 <= len(ids) <= 4 or len(set(ids)) != len(ids):
        raise HTTPException(422,"Select one to four distinct gene IDs")
    frame = pd.read_csv(PHASE4 / "candidate_evidence.csv").set_index("gene_id",drop=False)
    if not set(ids) <= set(frame.index):
        raise HTTPException(404,"Candidate not available")
    return {"rows":records(frame.loc[ids]),"interval":"Unshrunken log2FC +/- 1.96*lfcSE, approximate within-study Wald; no pooling"}


@app.get("/api/scientific-audit")
def scientific_audit():
    return {"audit":json.loads((PHASE4/"audit.json").read_text()),
            "fits":json.loads((PHASE4/"qc/fit_audit.json").read_text())}


@app.get("/api/statistical-sensitivity")
def statistical_sensitivity(study_a: Literal["GSE156496","GSE132741"] = "GSE156496",
                           study_b: Literal["GSE132741","GSE284723"] = "GSE132741",
                           fdr: float = Query(.05,gt=0,le=1)):
    if fdr not in (.01,.05,.1):
        raise HTTPException(422,"FDR must be 0.01, 0.05 or 0.1")
    frame = pd.read_csv(PHASE4/"statistical_sensitivity.csv")
    if study_a == study_b:
        raise HTTPException(422,"Studies must differ")
    return records(frame[(frame.study_a==study_a)&(frame.study_b==study_b)&(frame.fdr==fdr)])


@app.get("/api/publication")
def publication():
    return json.loads((PUBLICATION/"figure_manifest.json").read_text())


@app.get("/api/publication/download/{name}")
def publication_download(name: str):
    manifest = publication()
    allowed = {filename for figure in manifest for filename in figure["files"]}
    allowed |= {"figure_manifest.json","string_network_edges.csv","NeuroGene_Atlas_Publication_Figures.zip"}
    if name not in allowed or not (PUBLICATION/name).is_file():
        raise HTTPException(404,"Publication artifact unavailable")
    return FileResponse(PUBLICATION/name,filename=name)


@app.get("/api/phase4/download/{artifact}")
def phase4_download(artifact: Literal["evidence","sensitivity","audit","manuscript","provenance","pathways"]):
    paths = {"evidence":PHASE4/"candidate_evidence.csv","sensitivity":PHASE4/"statistical_sensitivity.csv",
             "audit":ROOT/"SCIENTIFIC_AUDIT_REPORT.md","manuscript":ROOT/"SCIENTIFIC_MANUSCRIPT_DRAFT.md",
             "provenance":PHASE4/"audit.json","pathways":PHASE4/"pathway_comparison.csv"}
    path = paths[artifact]
    if not path.is_file():
        raise HTTPException(404,"Artifact not generated")
    return FileResponse(path,filename=path.name)


FINAL_DOCUMENTS = ("FINAL_SCIENTIFIC_AUDIT.md", "FINAL_TECHNICAL_AUDIT.md", "PUBLICATION_READINESS.md",
                   "DATASET_COMPARISON_SUMMARY.md", "CANDIDATE_GENE_EVIDENCE.md", "FINAL_TEST_RESULTS.md")


@app.get("/api/final-audit")
def final_audit():
    folder = ROOT / "results/validation/phase5"
    if not (folder / "reproduction.json").exists():
        raise HTTPException(503, "Final reproduction audit unavailable")
    reproduction = json.loads((folder / "reproduction.json").read_text())
    tests = json.loads((folder / "tests.json").read_text()) if (folder / "tests.json").exists() else None
    return {"phase": 5, "reproduction_status": reproduction["status"],
            "matched_tables": sum(len(s["tables"]) for s in reproduction["studies"].values()),
            "environment": reproduction["environment"], "limitations": reproduction["limitations"],
            "test_status": tests["status"] if tests else "not yet run", "documents": list(FINAL_DOCUMENTS)}


@app.get("/api/final/download/{name}")
def final_download(name: str):
    allowed = {doc: ROOT / doc for doc in FINAL_DOCUMENTS}
    allowed.update({f"NeuroGene_Atlas_Scientific_Report_FINAL.{ext}": ROOT / "results/reports" / f"NeuroGene_Atlas_Scientific_Report_FINAL.{ext}" for ext in ("html", "pdf")})
    if name not in allowed or not allowed[name].is_file():
        raise HTTPException(404, "Final audit artifact unavailable")
    return FileResponse(allowed[name], filename=name)
