"""Vector publication figures with source tables, captions and parameter manifests."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from scripts.discovery.phase4_analysis import ROOT, OUT, STUDIES, load

DEST = ROOT / "results/publication"
COLORS = ["#148780", "#b83957", "#536482"]
plt.rcParams.update({"font.size":9,"pdf.fonttype":42,"svg.fonttype":"none","axes.spines.top":False,"axes.spines.right":False})
MANIFEST = []


def save(fig, name, title, caption, source, parameters):
    source.to_csv(DEST/f"{name}.csv",index=False)
    fig.tight_layout()
    for extension in ("svg","pdf","png"):
        fig.savefig(DEST/f"{name}.{extension}",dpi=160)
    plt.close(fig)
    files=[DEST/f"{name}.{ext}" for ext in ("svg","pdf","png","csv")]
    MANIFEST.append(dict(name=name,title=title,caption=caption,parameters=parameters,
                         files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}))


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    for study in STUDIES:
        pca=pd.read_csv(OUT/"qc"/f"{study}_pca.csv")
        fig,ax=plt.subplots(figsize=(6,4.5))
        for color,(condition,g) in zip(COLORS,pca.groupby("condition")):
            ax.scatter(g.PC1,g.PC2,color=color,label=condition,s=45)
            for row in g.itertuples():
                ax.annotate(row.name,(row.PC1,row.PC2),xytext=(3,4),textcoords="offset points",fontsize=6)
        ax.set(xlabel=f"PC1 ({pca.PC1_percent_variance.iloc[0]:.1f}%)",ylabel=f"PC2 ({pca.PC2_percent_variance.iloc[0]:.1f}%)",title=study)
        ax.legend()
        save(fig,f"pca_{study}",f"{study} PCA",f"DESeq2 variance-stabilized expression, blind=False; PCA on the 500 highest-variance genes within {study}. Each point is a submitted library. Percentages refer to variance of these selected features. No samples excluded; separation does not establish causality or independence.",pca,{"blind":False,"ntop":500,"source":"Stored fitted dds.rds, recomputed by audit_fits.R"})
        de=load(study).copy()
        de["neglog10padj"]=-np.log10(de.padj.clip(lower=1e-300))
        de["DEG"]=(de.padj<.05)&(de.log2FoldChange.abs()>1)
        fig,ax=plt.subplots(figsize=(6,4.5))
        valid=de.dropna(subset=["padj"])
        ax.scatter(valid.log2FoldChange,valid.neglog10padj,s=3,c=np.where(valid.DEG,COLORS[1],"#899898"),alpha=.6)
        ax.axhline(-np.log10(.05),color="#536482",lw=.7,ls="--")
        ax.axvline(-1,color="#536482",lw=.7,ls="--");ax.axvline(1,color="#536482",lw=.7,ls="--")
        ax.set(xlabel="Unshrunken case / reference log2 fold change",ylabel="-log10(BH adjusted p)",title=study)
        save(fig,f"volcano_{study}",f"{study} differential expression",f"Unshrunken DESeq2 effects and BH-adjusted p-values in {study}. Rose: padj<0.05 and |log2FC|>1. Missing padj excluded from rendering; all tested rows remain in source CSV. Positive effects indicate D51, mdx or conditional mKO relative to its own control. P-values at zero are numerical underflow, displayed using 1e-300.",de,{"fdr":.05,"abs_log2fc":1,"p_floor":1e-300,"estimate":"unshrunken"})
    pair=pd.read_csv(OUT/"pairwise_summary.csv")
    fig,ax=plt.subplots(figsize=(7,4))
    labels=pair.study_a.str.replace("GSE","")+" / "+pair.study_b.str.replace("GSE","")
    ax.bar(labels,pair.concordant,label="Concordant",color=COLORS[0]);ax.bar(labels,pair.discordant,bottom=pair.concordant,label="Discordant",color=COLORS[1])
    ax.set(ylabel="DEG intersection size",xlabel="Study pair");ax.legend()
    save(fig,"deg_overlap","Pairwise DEG overlap","Pairwise DEG intersections restricted to each pair's common valid-FDR universe. Bars separate concordant and discordant effects. Universes differ by pair; these are not three-way Venn counts. Hypergeometric log10 p-values in source CSV are descriptive and do not model correlated genes.",pair,{"fdr":.05,"abs_log2fc":1,"universe":"Pair-specific common nonmissing padj"})
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    sources=[]
    for ax,row in zip(axes,pair.itertuples()):
        f=pd.read_csv(OUT/f"{row.study_a}_{row.study_b}_all_effects.csv")
        ax.scatter(f.log2FoldChange_a,f.log2FoldChange_b,s=2,alpha=.25,color=COLORS[0])
        lo=min(f.log2FoldChange_a.min(),f.log2FoldChange_b.min());hi=max(f.log2FoldChange_a.max(),f.log2FoldChange_b.max())
        ax.plot([lo,hi],[lo,hi],lw=.7,color=COLORS[1]);ax.set(xlabel=row.study_a,ylabel=row.study_b,title=f"Common finite effects, n={len(f):,}")
        f["study_a"],f["study_b"]=row.study_a,row.study_b;sources.append(f)
    save(fig,"effect_concordance","All-gene effect concordance","All commonly tested genes with finite unshrunken effects, regardless of significance or availability of adjusted p-values. Diagonal is identity, not a fitted model. Genotype, age and processing heterogeneity preclude interchangeability of effects. Selection-bias statistics are provided separately.",pd.concat(sources),{"selection":"No DEG selection","estimate":"unshrunken"})
    evidence=pd.read_csv(OUT/"candidate_evidence.csv")
    top=evidence.nsmallest(5,"rank_balanced")
    forest=[];fig,axes=plt.subplots(1,5,figsize=(13,4),sharey=True)
    for ax,g in zip(axes,top.itertuples()):
        for i,s in enumerate(STUDIES):
            lfc=getattr(g,f"{s}_log2FoldChange");se=getattr(g,f"{s}_lfcSE")
            if np.isfinite(lfc) and np.isfinite(se):
                ax.errorbar(lfc,i,xerr=1.96*se,fmt="o",color=COLORS[i],capsize=3)
            forest.append(dict(gene_id=g.gene_id,gene_symbol=g.gene_symbol,study=s,log2fc=lfc,lfcSE=se,CI_low=lfc-1.96*se,CI_high=lfc+1.96*se))
        ax.axvline(0,color="#899898",ls="--",lw=.7);ax.set(title=g.gene_symbol,xlabel="log2FC",yticks=range(3),yticklabels=STUDIES)
    save(fig,"gene_forest","Study-specific candidate effects","Five candidates selected using preserved Phase 3 balanced ranks, before adding the third study. Separate unshrunken effects with approximate Wald intervals (log2FC +/- 1.96*lfcSE). No pooled estimate. Conditional selection and small sample sizes limit interval interpretation; uncertainty is within-study, not heterogeneity-adjusted.",pd.DataFrame(forest),{"selection":"Top five Phase 3 balanced candidates","CI":"Approximate normal 95% Wald","pooling":False})
    paths=pd.read_csv(OUT/"pathway_comparison.csv")
    shared=paths[(paths.direction=="all")&(paths.padj_a<.05)&(paths.padj_b<.05)].copy()
    chosen=shared.sort_values("padj_a").head(15)
    fig,ax=plt.subplots(figsize=(8,6))
    y=np.arange(len(chosen));ax.barh(y-.16,-np.log10(chosen.padj_a.clip(lower=1e-300)),height=.3,color=COLORS[0],label="Study A")
    ax.barh(y+.16,-np.log10(chosen.padj_b.clip(lower=1e-300)),height=.3,color=COLORS[1],label="Study B")
    ax.set(yticks=y,yticklabels=[f"{r.pathway_a[:45]} ({r.study_b})" for r in chosen.itertuples()],xlabel="-log10(BH adjusted p)");ax.invert_yaxis();ax.legend()
    save(fig,"shared_pathways","Shared Reactome enrichment","Fifteen pair/pathway entries with the lowest study-A adjusted p-values among shared all-DEG enriched Reactome v95 terms. Repeated terms across pairs are intentional. Separate annotation-mapped valid-FDR backgrounds and BH families (10-500 background genes per term). Full shared/eligible results retained in source table; common-background sensitivity is a separate table.",shared,{"direction":"all","fdr":.05,"term_size":[10,500],"display_selection":"First 15 sorted by padj_a"})
    nodes=pd.read_csv(ROOT/"results/discovery/network/nodes_0.7.csv")
    edges=pd.read_csv(ROOT/"results/discovery/network/edges.csv")
    selected=nodes.sort_values(["degree","gene_id"],ascending=[False,True]).head(40)
    subset=edges[(edges.score>=.7)&edges.source.isin(selected.gene_id)&edges.target.isin(selected.gene_id)]
    graph=nx.from_pandas_edgelist(subset,"source","target",edge_attr="score");graph.add_nodes_from(selected.gene_id)
    positions=nx.spring_layout(graph,seed=156496,weight="score",iterations=100)
    fig,ax=plt.subplots(figsize=(8,7))
    selected=selected.set_index("gene_id").loc[list(graph)]
    nx.draw_networkx_edges(graph,positions,ax=ax,alpha=.25,width=.7)
    nx.draw_networkx_nodes(graph,positions,ax=ax,node_size=40+selected.degree.to_numpy()*2,node_color=selected.community.to_numpy(),cmap="tab20")
    nx.draw_networkx_labels(graph,positions,labels=selected.gene_symbol.to_dict(),font_size=6,ax=ax);ax.axis("off")
    source=selected.reset_index();source["x"]=[positions[g][0] for g in source.gene_id];source["y"]=[positions[g][1] for g in source.gene_id]
    subset.to_csv(DEST/"string_network_edges.csv",index=False)
    save(fig,"string_network","STRING association subnetwork","Induced display of the 40 highest-degree mapped discovery DEGs at combined confidence >=0.7. Node size uses degree in the full 1,408-node network; colors use full-graph Louvain communities. Spring positions seeded 156496. Edges are functional associations, not causal regulation; display selection favors hubs and cannot establish disease specificity. Exact displayed edges in string_network_edges.csv.",source,{"confidence":.7,"nodes":40,"seed":156496,"selection":"Full graph degree; ties by gene ID"})
    MANIFEST[-1]["files"]["string_network_edges.csv"]=hashlib.sha256((DEST/"string_network_edges.csv").read_bytes()).hexdigest()
    top=evidence.nsmallest(20,"rank_balanced").copy()
    columns=[f"{s}_log2FoldChange" for s in STUDIES]
    fig,ax=plt.subplots(figsize=(7,7))
    image=ax.pcolormesh(np.ma.masked_invalid(top[columns].to_numpy()),cmap="RdBu_r",vmin=-5,vmax=5,rasterized=False)
    ax.set(yticks=np.arange(len(top))+.5,yticklabels=top.gene_symbol,xticks=np.arange(3)+.5,xticklabels=STUDIES)
    ax.invert_yaxis()
    colorbar=fig.colorbar(image,ax=ax,label="Unshrunken log2FC (color clipped +/-5)")
    colorbar.solids.set_rasterized(False)
    save(fig,"candidate_evidence","Candidate study evidence","Twenty candidates selected by preserved Phase 3 balanced rank. Colors show actual unshrunken per-study effects, clipped at +/-5 for display; source CSV contains complete evidence, standard errors, FDR, missingness, pathway and network metrics. Blank cells indicate unavailable effects, not zero evidence. This is evidence visualization, not calibrated biomarker performance.",top,{"selection":"Top 20 preserved Phase 3 ranks","color_limits":[-5,5]})
    sensitivity=pd.read_csv(OUT/"statistical_sensitivity.csv")
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,((a,b),table) in zip(axes,sensitivity.groupby(["study_a","study_b"],sort=False)):
        for color,(scenario,f) in zip([*COLORS,"#8c7546","#644c73"],table[table.fdr==.05].groupby("scenario")):
            ax.plot(f.lfc,f.overlap,marker="o",color=color,label=scenario)
        ax.set(title=f"{a} / {b}",xlabel="|log2FC| threshold",ylabel="DEG intersection");ax.legend(fontsize=7)
    save(fig,"statistical_sensitivity","Threshold, outlier and count-filter sensitivity","Pairwise overlaps at FDR<0.05 across effect cutoffs 0.5, 1 and 1.5. Alternative external count replacement and third-study count-filter fits are separate analyses; Cook-cutoff-disabled estimates are diagnostic only. Full 0.01/0.05/0.1 FDR grid in source CSV. Changes in eligible universes are reported and are not confidence intervals.",sensitivity,{"fdr_display":.05,"fdr_grid":[.01,.05,.1],"lfc_grid":[.5,1,1.5]})
    rank=pd.read_csv(ROOT/"results/discovery/candidates/sensitivity.csv")
    fig,ax=plt.subplots(figsize=(7,4));ax.barh(rank.scenario,rank.top50_overlap_with_balanced,color=COLORS[0]);ax.set(xlabel="Overlap with balanced top 50",xlim=(0,50))
    save(fig,"ranking_sensitivity","Candidate weight robustness","Top-50 overlap with the Phase 3 balanced ranking across five weighting presets, two network thresholds and external outlier replacement disabled. Network contribution is capped at 10% under balanced weights. Heuristic weighting perturbations are not independent experiments or probability intervals.",rank,{"reference":"Phase 3 balanced","top_n":50,"scenarios":8})
    (DEST/"figure_manifest.json").write_text(json.dumps(MANIFEST,indent=2)+"\n")
    print(f"Generated {len(MANIFEST)} figures: SVG, PDF, PNG, source CSV, parameters and captions")


if __name__ == "__main__":
    main()
