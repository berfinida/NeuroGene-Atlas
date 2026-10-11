"""Cache official GEO evidence before selecting a third dataset."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'results/phase4/geo_review'

def cache(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        response=httpx.get(url,timeout=120,follow_redirects=True);response.raise_for_status();path.write_bytes(response.content)
    return path

def read_geo(path):
    with gzip.open(path,'rt') as handle:rows=list(csv.reader(handle,delimiter='\t'))
    return rows

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reviewed=[]
    for accession in ['GSE126416','GSE262341','GSE324363','GSE284723']:
        raw=ROOT/'data/raw'/accession
        url=f'https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:-3]}nnn/{accession}/matrix/{accession}_series_matrix.txt.gz'
        path=cache(url,raw/f'{accession}_series_matrix.txt.gz')
        rows=read_geo(path)
        fields={}
        for row in rows:
            if row and row[0].startswith('!'):fields.setdefault(row[0],[]).append(row[1:])
        ids=fields['!Sample_geo_accession'][0]
        samples=[]
        for index,gsm in enumerate(ids):
            characteristics={}
            for values in fields.get('!Sample_characteristics_ch1',[]):
                if ':' in values[index]:
                    key,value=values[index].split(':',1);characteristics[key.strip().lower()]=value.strip()
            samples.append({'accession':gsm,'title':fields['!Sample_title'][0][index], 'species':fields['!Sample_organism_ch1'][0][index],'source':fields['!Sample_source_name_ch1'][0][index],'characteristics':characteristics})
        record={'accession':accession,'source_url':url,'title':fields['!Series_title'][0][0],'design':fields.get('!Series_overall_design',[]),'samples':samples,'supplementary_files':[r[0].replace('ftp://','https://') for r in fields.get('!Series_supplementary_file',[])], 'processing':list(dict.fromkeys(value for values in fields.get('!Sample_data_processing',[]) for value in values)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        (OUT/f'{accession}.json').write_text(json.dumps(record,indent=2)+'\n')
        reviewed.append({k:record[k] for k in ['accession','title','source_url','sha256','supplementary_files']})
        if accession=='GSE284723':cache(record['supplementary_files'][0],raw/'GSE284723_rawCounts.xlsx')
    (OUT/'reviewed_sources.json').write_text(json.dumps(reviewed,indent=2)+'\n');print(json.dumps(reviewed,indent=2))

if __name__=='__main__':main()
