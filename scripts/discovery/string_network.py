"""Cache a pinned STRING mouse network induced by all discovery DEGs."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/discovery/network"
BASE = "https://version-12-0.string-db.org/api"
CHANNELS = ["score", "nscore", "fscore", "pscore", "ascore", "escore", "dscore", "tscore"]


def fetch(method, identifiers, **params):
    cache = OUT / f"string_{method}_raw.json"
    if cache.exists():
        return json.loads(cache.read_text())
    response = httpx.post(f"{BASE}/json/{method}", data={"identifiers":"\r".join(identifiers), "species":10090,
                          "caller_identity":"neurogene-atlas", **params}, timeout=180)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected STRING payload: {payload}")
    cache.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    de = pd.read_csv(ROOT / "results/GSE156496/deseq2/deseq2_D51_vs_WT_unshrunken.csv")
    selected = de[(de.padj < .05) & (de.log2FoldChange.abs() > 1)].sort_values("gene_id")
    ids = selected.gene_id.tolist()
    mapping = pd.DataFrame(fetch("get_string_ids", ids, echo_query=1, limit=1))
    if mapping.empty:
        raise ValueError("No STRING mouse mapping")
    if not (mapping.ncbiTaxonId == 10090).all() or not mapping.stringId.str.startswith("10090.").all():
        raise ValueError("Species mismatch in STRING mapping")
    mapping["gene_id"] = mapping.queryIndex.map(lambda i: ids[int(i)])
    if not (mapping.queryItem == mapping.gene_id).all():
        raise ValueError("STRING query identifier alignment failed")
    # Exclude ambiguous gene-to-protein mappings from graph projection.
    duplicate = mapping.gene_id.duplicated(keep=False) | mapping.stringId.duplicated(keep=False)
    rejected = mapping[duplicate].copy()
    rejected.to_csv(OUT / "ambiguous_mappings.csv", index=False)
    mapping = mapping[~duplicate].copy()
    mapping.to_csv(OUT / "mapping.csv", index=False)
    payload = fetch("network", mapping.stringId.tolist(), required_score=400, network_type="functional", add_nodes=0)
    network = pd.DataFrame(payload)
    if network.empty:
        raise ValueError("No STRING edges returned")
    stop = not (pd.to_numeric(network.ncbiTaxonId, errors="raise") == 10090).all()
    if stop:
        raise ValueError("STRING network taxon mismatch")
    gene_lookup = mapping.set_index("stringId").gene_id.to_dict()
    network["source"] = network.stringId_A.map(gene_lookup)
    network["target"] = network.stringId_B.map(gene_lookup)
    if network[["source", "target"]].isna().any().any():
        raise ValueError("Unexpected extra STRING proteins")
    if not network[CHANNELS].apply(lambda col: col.between(0, 1).all()).all():
        raise ValueError("STRING scores outside [0,1]")
    network = network[(network.source != network.target) & (network.score >= .4)].copy()
    pairs = network.apply(lambda row: tuple(sorted([row.source,row.target])), axis=1)
    network = network.loc[~pairs.duplicated()].sort_values(["source","target"])
    network.to_csv(OUT / "edges.csv", index=False)
    unmapped = sorted(set(ids) - set(mapping.gene_id))
    info = {"status":"complete", "source":BASE, "string_version":"12.0", "taxid":10090,
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat(), "input":"All 1499 discovery DEGs; unshrunken padj<0.05 and abs(log2FC)>1",
            "input_genes":len(ids), "mapped_genes":len(mapping), "ambiguous_excluded":len(rejected), "unmapped_genes":unmapped,
            "edges_at_0_4":len(network), "minimum_confidence":.4, "add_nodes":0, "network_type":"functional",
            "score_units":"API scores in [0,1]; request threshold in [0,1000]", "channels":{
                "nscore":"gene neighborhood", "fscore":"gene fusion", "pscore":"phylogenetic co-occurrence", "ascore":"coexpression",
                "escore":"experiments", "dscore":"curated databases", "tscore":"text mining", "score":"combined confidence"},
            "limitations":"STRING associations are not causal or necessarily physical. Scores measure evidence confidence, not interaction strength. DEG-induced topology is selection dependent; text-mining and curated evidence introduce study bias.",
            "sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob("*.json")) if p.name != "provenance.json"}}
    (OUT / "provenance.json").write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps({k:v for k,v in info.items() if k not in {"unmapped_genes","channels","sha256"}},indent=2))


if __name__ == "__main__":
    main()
