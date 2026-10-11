"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Dna, Download, FlaskConical, GitBranch, Microscope, Search, ChevronLeft, ChevronRight, FileText, RefreshCw } from "lucide-react";
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, BarChart, Bar, Cell } from "recharts";
import NetworkView from "./NetworkView";
import { CrossDatasetView, CandidatesView } from "./DiscoveryViews";
import { EvidenceView, SensitivityView, PublicationView } from "./ResearchViews";
import StudyInspector from "./StudyInspector";

type Gene = { gene_id: string; gene_symbol: string; baseMean: number; log2FoldChange: number; lfcSE: number; pvalue: number | null; padj: number | null; neglog10padj?: number };
type Sample = {count_column: string; condition: string; geo_accession: string; library_size: number; size_factor: number; expression?: number};
type PCA = {PC1: number; PC2: number; name: string; condition: string; PC1_percent_variance: number; PC2_percent_variance: number};
type Summary = {genes_tested: number; raw_genes: number; significant_padj: number; significant_padj_0_05_abs_lfc_1: number; upregulated: number; downregulated: number; package_versions: Record<string, string>; validation: Record<string, boolean>; genes_with_pvalue: number; genes_with_padj: number; independent_filter_threshold: number};
type Dataset = {dataset: {title: string; organism: string; tissue: string; genome_build: string; sources: {geo_record: string}}, summary: Summary; samples: Sample[]};
type Pathway = {pathway_id: string; pathway: string; overlap: number; pathway_size: number; padj: number; fold_enrichment: number; url: string; genes: string};
type Enrichment = {rows: Pathway[]; provenance: {release: number; mapped_background: number; eligible_genes: number; significant_terms: Record<string, number>; limitations: string; method: string}};
type Tab = "Dataset" | "QC" | "Differential Expression" | "Gene Expression" | "Pathways" | "Network" | "Cross-Dataset Validation" | "Candidates" | "Reports" | "Study Evidence" | "Sensitivity" | "Publication";
const tabs: {name: Tab; icon: typeof Database}[] = [{name:"Dataset",icon:Database},{name:"QC",icon:Activity},{name:"Differential Expression",icon:GitBranch},{name:"Gene Expression",icon:Dna},{name:"Pathways",icon:FlaskConical},{name:"Network",icon:GitBranch},{name:"Cross-Dataset Validation",icon:Microscope},{name:"Candidates",icon:Search},{name:"Study Evidence",icon:Microscope},{name:"Sensitivity",icon:Activity},{name:"Publication",icon:FileText},{name:"Reports",icon:FileText}];
const teal = "#148780", rose = "#b83957";
const fmt = (n: number | null | undefined, digits = 2) => n == null ? "NA" : n.toLocaleString("en-US", {maximumFractionDigits: digits});
const pval = (n: number | null) => n == null ? "NA" : n < 0.001 ? n.toExponential(2) : n.toFixed(4);
async function get<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/${url}`, {signal});
  if (!response.ok) { const error = await response.json().catch(() => ({})); throw new Error(typeof error.detail === "string" ? error.detail : `Request failed (${response.status})`); }
  return response.json();
}

function PcaPlot({data}: {data: PCA[]}) {
  return <div className="chart"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{top:20,right:25,bottom:25,left:5}}>
    <CartesianGrid stroke="#e8eded"/><XAxis type="number" dataKey="PC1" name="PC1" label={{value:`PC1 (${fmt(data[0]?.PC1_percent_variance)}%)`, position:"bottom"}}/>
    <YAxis type="number" dataKey="PC2" name="PC2" label={{value:`PC2 (${fmt(data[0]?.PC2_percent_variance)}%)`,angle:-90,position:"insideLeft"}}/>
    <Tooltip cursor={{strokeDasharray:"3 3"}} content={({payload}) => payload?.[0] ? <div className="tooltip">{payload[0].payload.name}<br/>PC1: {fmt(payload[0].payload.PC1)}<br/>PC2: {fmt(payload[0].payload.PC2)}</div> : null}/>
    <Scatter name="WT" data={data.filter(p=>p.condition==="WT")} fill={teal}/><Scatter name="D51" data={data.filter(p=>p.condition==="D51")} fill={rose}/>
  </ScatterChart></ResponsiveContainer></div>;
}

export default function Page() {
  const [tab,setTab] = useState<Tab>("Dataset");
  const [study,setStudy] = useState("GSE156496");
  const studyScope = tab==="Dataset" || tab==="QC";
  const externalStudy = studyScope && study!=="GSE156496";
  const expandedStudy = ["Study Evidence","Sensitivity","Publication"].includes(tab);
  const [dataset,setDataset] = useState<Dataset>();
  const [qc,setQc] = useState<{pca:PCA[]; samples:Sample[]; summary:Summary}>();
  const [error,setError] = useState("");
  const [loading,setLoading] = useState(false);
  const [q,setQ] = useState(""); const [padj,setPadj] = useState(0.05); const [lfc,setLfc] = useState(1);
  const [direction,setDirection] = useState("all"); const [estimate,setEstimate] = useState("unshrunken"); const [sort,setSort] = useState("padj");
  const [offset,setOffset] = useState(0); const [genes,setGenes] = useState<{total:number;rows:Gene[]}>();
  const [selected,setSelected] = useState("ENSMUSG00000045103"); const [scale,setScale] = useState("normalized");
  const [expression,setExpression] = useState<{gene_id:string; samples:Sample[]; statistics:Gene[]}>();
  const [geneQuery,setGeneQuery] = useState("Dmd"); const [hits,setHits] = useState<{gene_id:string;gene_symbol:string}[]>([]);
  const [pathDirection,setPathDirection] = useState("all"); const [pathPadj,setPathPadj] = useState(0.05); const [pathQuery,setPathQuery] = useState("");
  const [pathways,setPathways] = useState<Enrichment>(); const [expanded,setExpanded] = useState("");
  const [figure,setFigure] = useState("volcano");
  useEffect(()=>{Promise.all([get<Dataset>("datasets"),get<typeof qc>("qc")]).then(([d,c])=>{setDataset(d);setQc(c)}).catch(e=>setError(e.message))},[]);
  const params = new URLSearchParams({q,padj:String(padj),lfc:String(lfc),direction,estimate,sort});
  const query = params.toString();
  useEffect(()=>{setOffset(0)},[query]);
  useEffect(()=>{
    if(tab!=="Differential Expression") return;
    const controller = new AbortController(); setLoading(true); setError("");
    get<{total:number;rows:Gene[]}>(`genes?${query}&offset=${offset}`,controller.signal).then(setGenes).catch(e=>{if(e.name!=="AbortError")setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});
    return ()=>controller.abort();
  },[tab,query,offset]);
  useEffect(()=>{
    if(tab!=="Gene Expression")return;
    const controller = new AbortController();setError("");setExpression(undefined);setLoading(true);
    get<typeof expression>(`expression/${selected}?scale=${scale}`,controller.signal).then(setExpression).catch(e=>{if(e.name!=="AbortError")setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});
    return ()=>controller.abort();
  },[tab,selected,scale]);
  useEffect(()=>{
    if(tab!=="Gene Expression" || !geneQuery.trim()){setHits([]);return;}
    const controller = new AbortController(); const timer = setTimeout(()=>get<typeof hits>(`gene-search?q=${encodeURIComponent(geneQuery)}`,controller.signal).then(setHits).catch(e=>{if(e.name!=="AbortError")setError(e.message)}),200);
    return ()=>{clearTimeout(timer);controller.abort()};
  },[tab,geneQuery]);
  useEffect(()=>{
    if(tab!=="Pathways")return;
    const controller = new AbortController();setLoading(true);setError("");
    get<Enrichment>(`pathways?direction=${pathDirection}&padj=${pathPadj}&q=${encodeURIComponent(pathQuery)}`,controller.signal).then(setPathways).catch(e=>{if(e.name!=="AbortError")setError(e.message)}).finally(()=>{if(!controller.signal.aborted)setLoading(false)});
    return ()=>controller.abort();
  },[tab,pathDirection,pathPadj,pathQuery]);
  function openGene(gene: Gene | {gene_id:string;gene_symbol:string}) {setSelected(gene.gene_id);setGeneQuery(gene.gene_symbol);setTab("Gene Expression");}
  const summary = dataset?.summary;
  return <div className="workspace">
    <a className="skip-link" href="#main-content">Skip to scientific content</a>
    <aside><div className="brand"><Microscope size={25}/><span>NeuroGene<br/><b>Atlas</b></span></div><div className="workspace-label">RESEARCH WORKSPACE</div>
      <nav aria-label="Scientific dashboard views">{tabs.map(({name,icon:Icon})=><button key={name} aria-current={tab===name?"page":undefined} className={tab===name?"active":""} onClick={()=>{setError("");setTab(name)}}><Icon size={18}/><span>{name}</span></button>)}</nav>
      <div className="sidebar-bottom"><span className="status-dot"/> DESeq2 {summary?.package_versions.DESeq2 || "..."}<br/><small>Mus musculus / {externalStudy&&study==="GSE284723"?"GRCm39":"mm10"}</small></div>
    </aside>
    <main id="main-content"><header><div><span className="eyebrow">TRANSCRIPTOMICS / {studyScope?study:expandedStudy?"GSE156496 + GSE132741 + GSE284723":tab==="Cross-Dataset Validation"||tab==="Candidates"?"GSE156496 + GSE132741":"GSE156496"}</span><h1>{tab}</h1></div><a className="command" title="GSE156496 analysis report" href="/api/download/report"><Download size={16}/>Analysis Report</a></header>
      <div className="context"><span className="tag">{externalStudy?study==="GSE132741"?"mdx vs WT":"mKO vs floxed controls":expandedStudy?"Separate D51 / mdx / conditional mKO contrasts":tab==="Cross-Dataset Validation"||tab==="Candidates"?"D51 / mdx versus WT":"D51 vs WT"}</span><span>Tibialis anterior</span><span>{externalStudy?study==="GSE132741"?"7 WT + 8 mdx libraries":"5 controls + 4 mKO libraries":expandedStudy?"6 discovery + 15 mdx + 9 conditional libraries":tab==="Cross-Dataset Validation"||tab==="Candidates"?"6 discovery + 15 external samples":"3 + 3 deposited libraries"}</span><span className="verified">{expandedStudy||(externalStudy&&study==="GSE284723")?"Exploratory outputs / cohort unresolved":"Computationally reproduced DESeq2"}</span></div>
      {(expandedStudy||(externalStudy&&study==="GSE284723"))&&<p className="limitation"><b>GSE284723: unresolved cohort discrepancy.</b> GEO design describes 10 mice, the deposit contains 9 libraries, and Figure 4 describes 8 mice. All 9 deposited libraries were analyzed; animal identifiers and exclusion reasons are unconfirmed. Third-study findings, including three-study stable candidates, are exploratory and excluded from validated headline evidence.</p>}
      {studyScope&&<section className="filters"><label>Dataset<select aria-label="Explore dataset" value={study} onChange={e=>setStudy(e.target.value)}>{["GSE156496","GSE132741","GSE284723"].map(s=><option key={s}>{s}</option>)}</select></label></section>}
      {externalStudy&&<StudyInspector study={study} qc={tab==="QC"}/>}
      {error && <div role="alert" className="error">{error}<button title="Reload" onClick={()=>location.reload()}><RefreshCw size={16}/></button></div>}
      {!dataset && !error && <p role="status">Loading analysis...</p>}
      {summary && tab==="Dataset" && !externalStudy && <>
        <section className="stats">{[["Genes tested",summary.genes_tested],["Differentially expressed",summary.significant_padj_0_05_abs_lfc_1],["Up in D51",summary.upregulated],["Down in D51",summary.downregulated]].map(([label,value],i)=><div key={label}><span>{label}</span><strong className={i===2?"rose":i===3?"teal":""}>{fmt(Number(value),0)}</strong>{i===1 && <small>padj &lt; 0.05 / |log2FC| &gt; 1</small>}</div>)}</section>
        <section className="two-columns"><div><div className="section-title"><h2>Sample structure</h2><div className="legend"><i style={{background:teal}}/>WT <i style={{background:rose}}/>D51</div></div>{qc && <PcaPlot data={qc.pca}/>}</div>
          <div className="dataset-details"><h2>GSE156496</h2><p>{dataset.dataset.title}</p><dl><dt>Organism</dt><dd>{dataset.dataset.organism}</dd><dt>Assay</dt><dd>Bulk RNA sequencing</dd><dt>Genome</dt><dd>mm10 / Ensembl gene IDs</dd><dt>Model</dt><dd>~ condition</dd><dt>Reference</dt><dd>WT</dd><dt>Raw genes</dt><dd>{fmt(summary.raw_genes,0)}</dd><dt>FDR adjustment</dt><dd>Benjamini-Hochberg</dd></dl><a href={dataset.dataset.sources.geo_record} target="_blank" rel="noreferrer">NCBI GEO source record</a></div></section>
        <section><h2>Sample registry</h2><SampleTable samples={dataset.samples}/></section>
      </>}
      {tab==="QC" && qc && !externalStudy && <><section className="two-columns"><div><h2>VST principal components</h2><PcaPlot data={qc.pca}/></div><div><h2>Sequencing depth</h2><div className="chart"><ResponsiveContainer><BarChart data={qc.samples} margin={{left:15,right:10,bottom:15}}><CartesianGrid vertical={false} stroke="#e8eded"/><XAxis dataKey="count_column"/><YAxis tickFormatter={v=>`${v/1e6}M`}/><Tooltip formatter={v=>fmt(Number(v),0)}/><Bar dataKey="library_size" name="Total counts">{qc.samples.map(s=><Cell key={s.count_column} fill={s.condition==="WT"?teal:rose}/>)}</Bar></BarChart></ResponsiveContainer></div></div></section><section><h2>Sample validation</h2><SampleTable samples={qc.samples}/></section><section className="figure-grid">{["sample_distance","heatmap"].map(name=><figure key={name}><a href={`/api/figures/${name}.pdf`} title="Download PDF"><img src={`/api/figures/${name}.png`} alt={name==="heatmap"?"Top 30 DESeq2 genes VST z-score heatmap":"VST sample Euclidean distances"}/></a></figure>)}</section><section><h2>Inference coverage</h2><p>{fmt(qc.summary.genes_with_pvalue,0)} valid p-values / {fmt(qc.summary.genes_with_padj,0)} adjusted p-values. Independent filter threshold: {fmt(qc.summary.independent_filter_threshold)} mean normalized counts.</p></section></>}
      {tab==="Differential Expression" && <>
        <section className="filters"><label className="search"><Search size={16}/><input aria-label="Search genes" placeholder="Gene symbol or Ensembl ID" value={q} onChange={e=>setQ(e.target.value)}/></label>
          <label>FDR &lt;<input aria-label="FDR threshold" type="number" min="0.000001" max="1" step="0.01" value={padj} onChange={e=>setPadj(Number(e.target.value))}/></label>
          <label>|log2FC| &gt;<input aria-label="Fold change threshold" type="number" min="0" step="0.5" value={lfc} onChange={e=>setLfc(Number(e.target.value))}/></label>
          <label>Direction<select value={direction} onChange={e=>setDirection(e.target.value)}><option value="all">All</option><option value="up">Up in D51</option><option value="down">Down in D51</option></select></label>
          <label>Estimate<select value={estimate} onChange={e=>setEstimate(e.target.value)}><option value="unshrunken">Unshrunken</option><option value="apeglm">apeglm</option></select></label>
          <label>Sort<select value={sort} onChange={e=>setSort(e.target.value)}><option value="padj">Adjusted p-value</option><option value="log2FoldChange">log2 fold change</option><option value="baseMean">Mean count</option></select></label>
          <a className="icon-button" title="Download filtered CSV" href={`/api/genes/export?${query}`}><Download size={18}/></a></section>
        <section><div className="section-title"><h2>{fmt(genes?.total,0)} genes</h2><span>{loading?"Updating...":`${estimate} estimates / D51 vs WT`}</span></div><div className="table-wrap"><table><thead><tr><th>Gene</th><th>Ensembl ID</th><th>Mean count</th><th>log2FC</th><th>Adjusted p</th><th>Direction</th></tr></thead><tbody>{genes?.rows.map(g=><tr key={g.gene_id}><td><button className="gene-link" onClick={()=>openGene(g)}>{g.gene_symbol}</button></td><td className="mono">{g.gene_id}</td><td>{fmt(g.baseMean)}</td><td className={g.log2FoldChange>0?"rose":"teal"}>{fmt(g.log2FoldChange,3)}</td><td className="mono">{pval(g.padj)}</td><td>{g.log2FoldChange>0?"Up":"Down"}</td></tr>)}</tbody></table>{genes?.total===0 && <p className="empty">No genes match these thresholds.</p>}</div><div className="pagination"><span>{genes?.total ? `${offset+1}-${Math.min(offset+50,genes.total)} of ${fmt(genes.total,0)}`:"0 genes"}</span><button title="Previous page" disabled={offset===0||loading} onClick={()=>setOffset(Math.max(0,offset-50))}><ChevronLeft size={18}/></button><button title="Next page" disabled={!genes||offset+50>=genes.total||loading} onClick={()=>setOffset(offset+50)}><ChevronRight size={18}/></button></div></section>
        <section><div className="section-title"><h2>DESeq2 figures</h2><div className="segmented">{["volcano","ma"].map(f=><button key={f} className={figure===f?"selected":""} onClick={()=>setFigure(f)}>{f==="ma"?"MA":"Volcano"}</button>)}</div><a title="Download figure PDF" href={`/api/figures/${figure}.pdf`}><Download size={18}/></a></div><img className="stat-figure" src={`/api/figures/${figure}.png`} alt={`${figure} plot of real DESeq2 results`}/></section>
      </>}
      {tab==="Gene Expression" && <><section className="filters"><label className="search"><Search size={16}/><input aria-label="Find gene" value={geneQuery} onChange={e=>setGeneQuery(e.target.value)} placeholder="Gene symbol or ID"/></label><label>Scale<select value={scale} onChange={e=>setScale(e.target.value)}><option value="normalized">DESeq2 normalized counts</option><option value="raw">Raw counts</option><option value="vst">VST</option></select></label></section>{hits.length>0 && <div className="gene-results">{hits.map(g=><button key={g.gene_id} onClick={()=>openGene(g)}>{g.gene_symbol}<small>{g.gene_id}</small></button>)}</div>}
        {expression && <section><div className="section-title"><div><h2>{expression.statistics[0]?.gene_symbol || expression.gene_id}</h2><span className="mono">{expression.gene_id}</span></div><span>Unshrunken log2FC: {fmt(expression.statistics[0]?.log2FoldChange,3)} / padj: {pval(expression.statistics[0]?.padj??null)}</span></div><div className="chart expression"><ResponsiveContainer><BarChart data={expression.samples} margin={{top:25,left:25,right:25,bottom:20}}><CartesianGrid vertical={false} stroke="#e8eded"/><XAxis dataKey="count_column"/><YAxis label={{value:scale==="vst"?"VST expression":scale==="raw"?"Raw count":"Normalized count",angle:-90,position:"insideLeft"}}/><Tooltip formatter={v=>fmt(Number(v),3)}/><Bar dataKey="expression" name="Expression">{expression.samples.map(s=><Cell key={s.count_column} fill={s.condition==="WT"?teal:rose}/>)}</Bar></BarChart></ResponsiveContainer></div><div className="legend"><i style={{background:teal}}/>WT <i style={{background:rose}}/>D51</div></section>}{loading && <p role="status">Loading expression...</p>}</>}
      {tab==="Pathways" && <><section className="filters"><label className="search"><Search size={16}/><input aria-label="Search pathways" value={pathQuery} onChange={e=>setPathQuery(e.target.value)} placeholder="Pathway name"/></label><label>Gene set<select value={pathDirection} onChange={e=>setPathDirection(e.target.value)}><option value="all">All DEGs</option><option value="up">Up in D51</option><option value="down">Down in D51</option></select></label><label>Pathway FDR &lt;<input aria-label="Pathway FDR" type="number" min="0.000001" max="1" step="0.01" value={pathPadj} onChange={e=>setPathPadj(Number(e.target.value))}/></label><a className="icon-button" title="Download all pathway results" href="/api/download/pathways"><Download size={18}/></a></section>
        {pathways && <><section className="method-note"><b>Reactome {pathways.provenance.release} / Mus musculus</b><p>{pathways.provenance.method}. Background: {fmt(pathways.provenance.mapped_background,0)} mapped genes of {fmt(pathways.provenance.eligible_genes,0)} with valid inference. DEG input: unshrunken padj &lt; 0.05, |log2FC| &gt; 1.</p></section><section><div className="section-title"><h2>{pathways.rows.length} pathways</h2><span>{loading?"Updating...":"BH adjustment per gene set"}</span></div><div className="table-wrap"><table><thead><tr><th>Pathway</th><th>Overlap</th><th>Fold enrichment</th><th>Adjusted p</th></tr></thead><tbody>{pathways.rows.map(p=><tr key={p.pathway_id}><td><button className="gene-link" onClick={()=>setExpanded(expanded===p.pathway_id?"":p.pathway_id)}>{p.pathway}</button><small className="mono">{p.pathway_id}</small>{expanded===p.pathway_id && <div className="overlap"><a href={p.url} target="_blank" rel="noreferrer">Reactome record</a>{p.genes.split(";").map(id=><button key={id} onClick={()=>{setSelected(id);setGeneQuery(id);setTab("Gene Expression")}}>{id}</button>)}</div>}</td><td>{p.overlap} / {p.pathway_size}</td><td>{fmt(p.fold_enrichment)}</td><td className="mono">{pval(p.padj)}</td></tr>)}</tbody></table>{pathways.rows.length===0 && <p className="empty">No pathways match these thresholds.</p>}</div></section><p className="limitation">{pathways.provenance.limitations}</p></>}
      </>}
      {tab==="Reports" && summary && <><section><h2>Analysis artifacts</h2><div className="downloads">{[["report","Complete analysis bundle","ZIP: results, figures, methods, provenance"],["unshrunken","Unshrunken DESeq2 results","Wald statistics and BH adjusted p-values"],["apeglm","apeglm effect estimates","Shrunken log2 fold changes"],["normalized","Normalized expression","DESeq2 median-ratio counts"],["pathways","Reactome enrichment","All tested pathways and gene overlaps"],["provenance","Provenance","SHA-256 hashes and source URLs"],["methods","Methods and results","Markdown report"],["session","Software session","R and package versions"]].map(([id,title,detail])=><a key={id} href={`/api/download/${id}`}><FileText size={21}/><span><b>{title}</b><small>{detail}</small></span><Download size={18}/></a>)}</div></section><section><h2>Software versions</h2><dl>{Object.entries(summary.package_versions).map(([key,value])=><div className="dl-row" key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section><section><h2>Validated checks</h2><div className="checks">{Object.entries(summary.validation).map(([key,value])=><span key={key}><i className="status-dot"/>{key.replaceAll("_"," ")}: {value?"passed":"failed"}</span>)}</div></section><p className="limitation">One mouse cohort, n=3 per group. No batch covariate is available in the configured metadata. Exploratory Python statistics are excluded from this workspace. These results do not establish human clinical efficacy.</p></>}
      {tab==="Network" && <NetworkView openGene={openGene}/>}
      {tab==="Cross-Dataset Validation" && <CrossDatasetView openGene={openGene}/>}
      {tab==="Candidates" && <CandidatesView openGene={openGene}/>}
      {tab==="Study Evidence" && <EvidenceView/>}
      {tab==="Sensitivity" && <SensitivityView/>}
      {tab==="Publication" && <PublicationView/>}
      {tab==="Reports" && <section><h2>Scientific research deliverables</h2><div className="downloads"><a href="/api/research/report/html"><FileText size={21}/><span><b>Scientific HTML report</b><small>Methods, results, sensitivity, limitations and references</small></span><Download size={18}/></a><a href="/api/research/report/pdf"><FileText size={21}/><span><b>Scientific PDF report</b><small>Printable research report</small></span><Download size={18}/></a><a href="/api/discovery/download/candidates"><FileText size={21}/><span><b>Exploratory candidates</b><small>Scores, evidence components and sensitivity ranks</small></span><Download size={18}/></a></div></section>}
      <footer>Mouse transcriptomics / DESeq2 Wald tests / study-specific control references / no clinical validation</footer>
    </main>
  </div>;
}

function SampleTable({samples}:{samples:Sample[]}) {
  return <div className="table-wrap"><table><thead><tr><th>Sample</th><th>GEO accession</th><th>Condition</th><th>Library size</th><th>Size factor</th></tr></thead><tbody>{samples.map(s=><tr key={s.count_column}><td className="mono">{s.count_column}</td><td><a href={`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=${s.geo_accession}`} target="_blank" rel="noreferrer">{s.geo_accession}</a></td><td><span className={`condition ${s.condition==="WT"?"wt":"d51"}`}>{s.condition}</span></td><td>{fmt(s.library_size,0)}</td><td>{fmt(s.size_factor,4)}</td></tr>)}</tbody></table></div>;
}
