"use client";
import {useEffect, useState} from "react";
import {CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis} from "recharts";

type Point = {gene_id:string;gene_symbol:string;log2FoldChange:number;neglog10padj:number;padj:number};
export default function VolcanoPlot({estimate, padj, lfc, openGene}:{estimate:string;padj:number;lfc:number;openGene:(g:Point)=>void}) {
  const [data,setData] = useState<Point[]>(); const [error,setError] = useState("");
  useEffect(()=>{const c=new AbortController();setData(undefined);setError("");fetch(`/api/volcano?estimate=${estimate}`,{signal:c.signal}).then(async r=>{if(!r.ok)throw Error("Volcano data unavailable");return r.json()}).then(setData).catch(e=>{if(e.name!=="AbortError")setError(e.message)});return()=>c.abort()},[estimate]);
  if(error)return <p role="alert" className="error">{error}</p>;
  if(!data)return <p role="status">Loading volcano data...</p>;
  const significant = data.filter(p=>p.padj<padj&&Math.abs(p.log2FoldChange)>lfc);
  return <div className="chart" aria-label="Interactive DESeq2 volcano plot" data-points={data.length}>
    <ResponsiveContainer><ScatterChart margin={{top:15,right:20,bottom:25,left:15}}><CartesianGrid stroke="#e8eded"/>
      <XAxis type="number" dataKey="log2FoldChange" name="log2FC" label={{value:"log2 fold change / D51 vs WT",position:"bottom"}}/>
      <YAxis type="number" dataKey="neglog10padj" name="-log10 FDR" label={{value:"-log10 adjusted p",angle:-90,position:"insideLeft"}}/>
      <Tooltip cursor={{strokeDasharray:"3 3"}} content={({payload})=>payload?.[0]?<div className="tooltip">{payload[0].payload.gene_symbol}<br/>{payload[0].payload.gene_id}<br/>log2FC: {Number(payload[0].payload.log2FoldChange).toFixed(3)}<br/>FDR: {Number(payload[0].payload.padj).toExponential(2)}</div>:null}/>
      <Scatter name="Other valid-FDR genes" data={data.filter(p=>!(p.padj<padj&&Math.abs(p.log2FoldChange)>lfc))} fill="#c0ccca" isAnimationActive={false} onClick={p=>openGene(p.payload)}/>
      <Scatter name="Up" data={significant.filter(p=>p.log2FoldChange>0)} fill="#b83957" isAnimationActive={false} onClick={p=>openGene(p.payload)}/>
      <Scatter name="Down" data={significant.filter(p=>p.log2FoldChange<0)} fill="#148780" isAnimationActive={false} onClick={p=>openGene(p.payload)}/>
    </ScatterChart></ResponsiveContainer>
  </div>;
}
