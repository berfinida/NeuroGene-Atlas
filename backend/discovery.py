"""Graph metrics are computed on the full thresholded DEG-induced network."""
import json
from functools import lru_cache
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NETWORK = ROOT / "results/discovery/network"
DE = ROOT / "results/GSE156496/deseq2"


@lru_cache(maxsize=16)
def graph_tables(confidence=.7):
    mapping = pd.read_csv(NETWORK / "mapping.csv")
    edges = pd.read_csv(NETWORK / "edges.csv")
    edges = edges[edges.score >= confidence].copy()
    graph = nx.Graph()
    graph.add_nodes_from(sorted(mapping.gene_id))
    graph.add_weighted_edges_from(edges[["source","target","score"]].itertuples(index=False,name=None))
    communities = nx.community.louvain_communities(graph, weight="weight", seed=156496) if graph.number_of_edges() else [{node} for node in graph]
    communities = sorted(communities,key=lambda c:(-len(c),min(c)))
    labels = {node:i for i,group in enumerate(communities) for node in group}
    degree = dict(graph.degree())
    betweenness = nx.betweenness_centrality(graph,k=min(64,len(graph)),seed=156496,weight=None,normalized=True)
    pagerank = nx.pagerank(graph,weight="weight")
    normalized_degree = nx.degree_centrality(graph)
    annotation = pd.read_csv(DE / "deseq2_D51_vs_WT_unshrunken.csv").set_index("gene_id")
    pathways = pd.read_csv(DE / "reactome_enrichment.csv")
    pathways = pathways[(pathways.direction=="all")&(pathways.padj<.05)]
    memberships = {}
    for row in pathways.itertuples():
        for gene in str(row.genes).split(";"):
            memberships.setdefault(gene,[]).append(row.pathway)
    nodes = mapping[["gene_id","stringId","preferredName","annotation"]].copy()
    nodes["gene_symbol"] = nodes.gene_id.map(annotation.gene_symbol)
    nodes["log2FoldChange"] = nodes.gene_id.map(annotation.log2FoldChange)
    nodes["padj"] = nodes.gene_id.map(annotation.padj)
    nodes["degree"] = nodes.gene_id.map(degree)
    nodes["degree_centrality"] = nodes.gene_id.map(normalized_degree)
    nodes["betweenness"] = nodes.gene_id.map(betweenness)
    nodes["pagerank"] = nodes.gene_id.map(pagerank)
    nodes["community"] = nodes.gene_id.map(labels)
    nodes["pathways"] = nodes.gene_id.map(lambda g:";".join(memberships.get(g,[])))
    nodes = nodes.sort_values(["degree","gene_id"],ascending=[False,True])
    return nodes,edges


def network_payload(confidence=.7,limit=100,q=""):
    nodes,edges = graph_tables(confidence)
    connected = nodes[nodes.degree>0]
    if q:
        seeds = nodes[nodes.gene_symbol.fillna('').str.contains(q,case=False,regex=False)|nodes.gene_id.str.contains(q,case=False,regex=False)]
        ids = set(seeds.gene_id)
        adjacent = edges[edges.source.isin(ids)|edges.target.isin(ids)]
        neighbors = set(adjacent.source)|set(adjacent.target)
        connected = pd.concat([seeds,nodes[nodes.gene_id.isin(neighbors-ids)]]).drop_duplicates('gene_id')
    shown = connected.head(limit)
    ids = set(shown.gene_id)
    displayed_edges = edges[edges.source.isin(ids)&edges.target.isin(ids)]
    provenance = json.loads((NETWORK / "provenance.json").read_text())
    return {"nodes":json.loads(shown.to_json(orient="records")),"edges":json.loads(displayed_edges.to_json(orient="records")),
            "confidence":confidence,"total_nodes":len(nodes),"total_edges":len(edges),"isolated_nodes":int((nodes.degree==0).sum()),
            "displayed_nodes":len(shown),"displayed_edges":len(displayed_edges),"community_count":int(nodes.community.nunique()),
            "metrics":"Full thresholded graph; normalized degree, unweighted betweenness estimated with 64 pivots, confidence-weighted PageRank; weighted Louvain communities (seed 156496)",
            "display_selection":"Search matches followed by their highest-degree neighbors; full-graph metrics unchanged" if q else "Highest-degree connected nodes, limited for visualization; metrics use all mapped nodes, including isolates",
            "provenance":provenance}
