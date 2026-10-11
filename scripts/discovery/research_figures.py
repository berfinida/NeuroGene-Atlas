"""Render only measured results; no synthetic scientific data."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/reports/figures'

def save(fig,name):
    fig.tight_layout()
    for ext in ['png','pdf']:
        fig.savefig(OUT/f'{name}.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(ROOT/'results/discovery/replication/gene_comparison.csv')
    fig,ax=plt.subplots(figsize=(7,5))
    ax.scatter(data.log2FoldChange_discovery,data.log2FoldChange_external,s=3,alpha=.18,color='#148780',rasterized=True)
    discord=data[data.both_deg&~data.direction_agrees]
    ax.scatter(discord.log2FoldChange_discovery,discord.log2FoldChange_external,s=25,color='#b83957',label='Discordant overlapping DEGs')
    ax.axhline(0,color='#b8c7c4',lw=.5);ax.axvline(0,color='#b8c7c4',lw=.5)
    ax.set(xlabel='GSE156496 D51 vs WT / unshrunken log2FC',ylabel='GSE132741 mdx vs WT / unshrunken log2FC',title=f'{len(data):,} shared inference genes; no pooling')
    ax.legend(fontsize=8);save(fig,'effect_comparison')
    data=pd.read_csv(ROOT/'results/discovery/replication/sensitivity.csv')
    fig,ax=plt.subplots(figsize=(9,5))
    for index,(setting,group) in enumerate(data.groupby('outlier_setting',sort=False)):
        x=list(range(len(group)))
        ax.bar([i-.18+index*.36 for i in x],group.overlap,width=.36,label=setting,color=['#148780','#b83957'][index])
        ax.set_xticks(x,[f'FDR {r.fdr}\nLFC {r.lfc}' for r in group.itertuples()],fontsize=8)
    ax.set(ylabel='Overlapping DEGs',title='Threshold and external outlier-replacement sensitivity');ax.legend(fontsize=8);save(fig,'replication_sensitivity')
    data=pd.read_csv(ROOT/'results/discovery/candidates/sensitivity.csv')
    fig,(a,b)=plt.subplots(1,2,figsize=(10,5))
    a.barh(data.scenario,data.top50_overlap_with_balanced,color='#148780');a.set(xlim=(0,50),xlabel='Top 50 overlap with balanced')
    b.barh(data.scenario,data.rank_spearman_with_balanced,color='#b83957');b.set(xlim=(0,1),xlabel='Rank Spearman correlation')
    fig.suptitle('Exploratory candidate rank sensitivity / eight scenarios');save(fig,'candidate_sensitivity')
    print('Created 3 PNG and 3 PDF figures from verified tables')

if __name__=='__main__':main()
