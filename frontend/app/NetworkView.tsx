"use client";
import { useEffect, useRef, useState } from "react";
import cytoscape, { Core } from "cytoscape";
import { Download, Maximize, ZoomIn, ZoomOut } from "lucide-react";

type Node = {gene_id:string;gene_symbol:string;stringId:string;log2FoldChange:number;degree:number;degree_centrality:number;betweenness:number;pagerank:number;community:number;pathways:string;annotation:string};
type Edge = {source:string;target:string;score:number;escore:number;dscore:number;tscore:number;ascore:number;nscore:number;fscore:number;pscore:number};
type Network = {nodes:Node[];edges:Edge[];total_nodes:number;total_edges:number;displayed_nodes:number;displayed_edges:number;isolated_nodes:number;community_count:number;metrics:string;display_selection:string;provenance:{limitations:string;string_version:string;mapped_genes:number;input_genes:number}};
const colors = ["#148780","#b83957","#537ba4","#ae8438","#885687","#426949"];
export default function NetworkView({openGene}:{openGene:(gene:{gene_id:string;gene_symbol:string})=>void}) {
  const host = useRef<HTMLDivElement>(null);const graph = useRef<Core|null>(null);
  const [confidence,setConfidence]=useState(.7);const [limit,setLimit]=useState(100);const [color,setColor]=useState("effect");
  const [data,setData]=useState<Network>();const [selected,setSelected]=useState<Node>();const [edge,setEdge]=useState<Edge>();
  const [loading,setLoading]=useState(true);const [error,setError]=useState("");
  const [q,setQ]=useState("");
  useEffect(()=>{
    const controller=new AbortController();setLoading(true);setError("");setData(undefined);setSelected(undefined);setEdge(undefined);
    fetch(`/api/network?confidence=${confidence}&limit=${limit}&q=${encodeURIComponent(q)}`,{signal:controller.signal}).then(async r=>{if(!r.ok)throw new Error("Network unavailable");return r.json()}).then(setData).catch(e=>{if(e.name!=="AbortError")setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});
    return ()=>controller.abort();
  },[confidence,limit,q]);
  useEffect(()=>{
    if(!host.current||!data)return;
    const nodes=data.nodes.map(n=>({data:{id:n.gene_id,label:n.gene_symbol,displayLabel:data.nodes.length<=30?n.gene_symbol:"",color:color==="community"?colors[n.community%colors.length]:n.log2FoldChange>0?"#b83957":"#148780",size:18+Math.min(n.degree,80)/3}}));
    const edges=data.edges.map((e,i)=>({data:{id:`e${i}`,source:e.source,target:e.target,score:e.score}}));
    const cy=cytoscape({container:host.current,elements:[...nodes,...edges],minZoom:.1,maxZoom:5,
      style:[{selector:"node",style:{label:"data(displayLabel)","background-color":"data(color)",width:"data(size)",height:"data(size)","font-size":10,color:"#243335","text-valign":"bottom","text-margin-y":4}},
        {selector:"edge",style:{width:"mapData(score, 0.4, 1, 0.5, 2.5)","line-color":"#b3c5c1",opacity:.5,"curve-style":"haystack"}},
        {selector:":selected",style:{"border-color":"#243335","border-width":3,"line-color":"#243335",opacity:1}},
        {selector:"node:selected, node.hover",style:{label:"data(label)","text-background-color":"#fff","text-background-opacity":.9,"text-background-padding":"2px"}}],
      layout:{name:"cose",animate:false,fit:true,padding:30,randomize:false,nodeRepulsion:()=>10000},wheelSensitivity:.2});
    graph.current=cy;
    cy.on("mouseover","node",e=>e.target.addClass("hover"));
    cy.on("mouseout","node",e=>e.target.removeClass("hover"));
    cy.on("tap","node",e=>{setSelected(data.nodes.find(n=>n.gene_id===e.target.id()));setEdge(undefined)});
    cy.on("tap","edge",e=>{const d=e.target.data();setEdge(data.edges.find(x=>x.source===d.source&&x.target===d.target));setSelected(undefined)});
    const resize = new ResizeObserver(()=>{cy.resize();cy.fit(undefined,30)});resize.observe(host.current);
    return ()=>{resize.disconnect();cy.destroy();graph.current=null};
  },[data,color]);
  function selectNode(id:string) {const node=data?.nodes.find(n=>n.gene_id===id);setSelected(node);setEdge(undefined);graph.current?.elements().unselect();graph.current?.getElementById(id).select();}
  return <>
    <section className="filters"><label>Confidence<select aria-label="Network confidence" value={confidence} onChange={e=>setConfidence(Number(e.target.value))}><option value="0.4">0.4 / medium</option><option value="0.7">0.7 / high</option><option value="0.9">0.9 / highest</option></select></label>
      <label>Visible nodes<input aria-label="Visible network nodes" type="number" min="10" max="200" step="10" value={limit} onChange={e=>setLimit(Math.max(10,Math.min(200,Number(e.target.value))))}/></label>
      <label>Gene search<input aria-label="Search network genes" value={q} onChange={e=>setQ(e.target.value)} placeholder="Symbol or Ensembl ID"/></label>
      <label>Node color<select aria-label="Network node color" value={color} onChange={e=>setColor(e.target.value)}><option value="effect">Expression direction</option><option value="community">Community</option></select></label>
      <a className="icon-button" title="Download network nodes" href={`/api/network/export/nodes?confidence=${confidence}`}><Download size={18}/></a><a className="icon-button" title="Download network edges" href={`/api/network/export/edges?confidence=${confidence}`}><Download size={18}/></a>
    </section>
    {loading&&<p role="status">Computing network metrics...</p>}{error&&<p role="alert" className="error">{error}</p>}
    {data&&<><section className="network-overview"><span><b>{data.total_nodes.toLocaleString()}</b> mapped nodes</span><span><b>{data.total_edges.toLocaleString()}</b> associations</span><span><b>{data.isolated_nodes}</b> isolates</span><span><b>{data.community_count}</b> communities including singletons</span></section>
      <section className="network-band"><div className="section-title"><h2>STRING {data.provenance.string_version} / mouse</h2><span>{data.displayed_nodes} nodes / {data.displayed_edges} edges shown</span><div className="network-tools"><button title="Fit network" onClick={()=>graph.current?.fit(undefined,30)}><Maximize size={17}/></button><button title="Zoom in" onClick={()=>graph.current?.zoom((graph.current?.zoom()||1)*1.2)}><ZoomIn size={17}/></button><button title="Zoom out" onClick={()=>graph.current?.zoom((graph.current?.zoom()||1)/1.2)}><ZoomOut size={17}/></button></div></div>
        <div ref={host} className="network-canvas" role="img" aria-label="Interactive STRING mouse protein-association network" data-node-count={data.nodes.length}/>
        <label className="node-selector">Gene<select aria-label="Select network gene" value={selected?.gene_id||""} onChange={e=>selectNode(e.target.value)}><option value="">Select a node</option>{data.nodes.map(n=><option key={n.gene_id} value={n.gene_id}>{n.gene_symbol}</option>)}</select></label>
        <label className="node-selector">Association<select aria-label="Select network association" value={edge?`${edge.source}|${edge.target}`:""} onChange={e=>{const [source,target]=e.target.value.split('|');setEdge(data.edges.find(x=>x.source===source&&x.target===target));setSelected(undefined)}}><option value="">Select an association</option>{data.edges.map(e=><option key={`${e.source}|${e.target}`} value={`${e.source}|${e.target}`}>{data.nodes.find(n=>n.gene_id===e.source)?.gene_symbol} / {data.nodes.find(n=>n.gene_id===e.target)?.gene_symbol} ({e.score})</option>)}</select></label>
        {selected&&<div className="network-inspector"><div className="section-title"><h2>{selected.gene_symbol}</h2><button className="gene-link" onClick={()=>openGene(selected)}>Expression</button></div><p className="mono">{selected.gene_id} / {selected.stringId}</p><dl><dt>Degree</dt><dd>{selected.degree}</dd><dt>Centrality</dt><dd>{selected.degree_centrality.toFixed(4)}</dd><dt>Betweenness</dt><dd>{selected.betweenness.toFixed(4)}</dd><dt>PageRank</dt><dd>{selected.pagerank.toFixed(5)}</dd><dt>Community</dt><dd>{selected.community}</dd></dl><p>{selected.annotation}</p><p>{selected.pathways||"No enriched pathway annotation"}</p></div>}
        {edge&&<div className="network-inspector"><h2>Association evidence</h2><p className="mono">{edge.source} / {edge.target}</p><dl><dt>Combined</dt><dd>{edge.score}</dd><dt>Experiments</dt><dd>{edge.escore}</dd><dt>Databases</dt><dd>{edge.dscore}</dd><dt>Text mining</dt><dd>{edge.tscore}</dd><dt>Coexpression</dt><dd>{edge.ascore}</dd><dt>Neighborhood</dt><dd>{edge.nscore}</dd><dt>Gene fusion</dt><dd>{edge.fscore}</dd><dt>Co-occurrence</dt><dd>{edge.pscore}</dd></dl></div>}
      </section><section className="method-note"><p>{data.metrics}. {data.display_selection}.</p><p>{data.provenance.mapped_genes} / {data.provenance.input_genes} discovery DEGs mapped.</p></section><p className="limitation">{data.provenance.limitations}</p>
    </>}
  </>;
}
