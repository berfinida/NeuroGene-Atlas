"""Extract original sample fields, including external fasting context, for audit."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from scripts.discovery.review_geo import read_geo

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"results/phase4"


def main():
    records=[]
    for study in ("GSE156496","GSE132741","GSE284723"):
        rows=read_geo(ROOT/"data/raw"/study/f"{study}_series_matrix.txt.gz")
        fields={}
        for row in rows:
            if row and row[0].startswith("!Sample_"):
                fields.setdefault(row[0],[]).append(row[1:])
        selected=pd.read_csv(ROOT/"data/processed"/study/"sample_metadata.csv")
        column=next(c for c in ("geo_accession","accession") if c in selected)
        for sample in selected[column]:
            i=fields["!Sample_geo_accession"][0].index(sample)
            record=dict(study=study,accession=sample)
            for values in fields.get("!Sample_characteristics_ch1",[]):
                value=values[i]
                if ":" in value:
                    key,value=value.split(":",1);record[key.strip().lower()]=value.strip()
            records.append(record)
    (OUT/"original_sample_metadata.json").write_text(json.dumps(records,indent=2)+"\n")
    context=[]
    meta=pd.read_csv(ROOT/"data/processed/GSE132741/sample_metadata.csv").set_index("geo_accession")
    for row in records:
        if row["study"]!="GSE132741":continue
        start=datetime.strptime(row["time food removed"],"%H:%M")
        end=datetime.strptime(row["time collection"],"%H:%M")
        minutes=(end-start).total_seconds()/60
        assert 0<minutes<24*60
        sample=meta.loc[row["accession"]]
        context.append(dict(accession=row["accession"],count_column=sample.count_column,
                            condition=sample.condition,fasting_minutes=minutes,
                            collection_minutes=end.hour*60+end.minute,
                            weight_before=float(row["weight before fasting (g)"]),
                            weight_after=float(row["weight after fasting (g)"])))
    pd.DataFrame(context).to_csv(OUT/"external_context.csv",index=False)
    print(pd.DataFrame(context).groupby("condition").fasting_minutes.agg(["min","max","mean"]))


if __name__=="__main__":main()
