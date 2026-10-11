"""Create separate source/research releases and verify every included byte."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import zipfile
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release'
EXCLUDED={'.git','.venv','venv','node_modules','.next','__pycache__','.runtime','.pytest_cache','.mypy_cache','.ruff_cache','.DS_Store','test-results','playwright-report','.agents','.codex','.aws','release','dist','build'}

def allowed(path):
    return not any(part in EXCLUDED for part in path.relative_to(ROOT).parts) and path.suffix not in {'.pyc','.pyo','.tsbuildinfo'} and not path.name.startswith('._') and not (path.name.startswith('.env') and path.name!='.env.example') and not path.is_symlink()

def digest(data):return hashlib.sha256(data).hexdigest()

def create(name,files):
    destination=OUT/name
    hashes={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in files}
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashes,'extract_into':'Same root as the other NeuroGene Atlas ZIP','exclusions':sorted(EXCLUDED)}
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files:archive.write(path,str(path.relative_to(ROOT)))
        manifest_name='SOURCE_RELEASE_MANIFEST.json' if 'Source' in name else 'RESEARCH_RELEASE_MANIFEST.json'
        archive.writestr(manifest_name,json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None,'ZIP CRC failure'
        for name,expected in hashes.items():assert digest(archive.read(name))==expected,name
        assert not any(set(Path(name).parts)&EXCLUDED for name in archive.namelist())
    return {'path':str(destination.relative_to(ROOT)),'files':len(files),'bytes':destination.stat().st_size,'sha256':digest(destination.read_bytes()),'crc':'passed','included_sha256':'all verified','exclusions':'passed'}

def main():
    validation=json.loads((ROOT/'results/validation/final_validation.json').read_text())
    assert validation['status']=='passed','Release requires observed passing validation'
    html=ROOT/'results/reports/NeuroGene_Atlas_Scientific_Report.html'
    pdf=html.with_suffix('.pdf')
    assert html.is_file() and '<html' in html.read_text()
    assert pdf.read_bytes().startswith(b'%PDF') and b'%%EOF' in pdf.read_bytes()[-1024:]
    parsed=PdfReader(pdf)
    report_text=' '.join(page.extract_text() for page in parsed.pages)
    assert len(parsed.pages)>=3
    for heading in ['Summary','Datasets and Methods','STRING Association Network','Exploratory Candidate Prioritization','Limitations','References']:
        assert heading in report_text,heading
    OUT.mkdir(exist_ok=True)
    old=OUT/'release_validation.json'
    if old.exists() and json.loads(old.read_text()).get('phase')!=4:
        saved=OUT/'phase3';saved.mkdir(exist_ok=True)
        for name in ['NeuroGene_Atlas_Source.zip','NeuroGene_Atlas_Research_Results.zip','release_validation.json','extracted_release_validation.json','extracted_release_tests.log']:
            path=OUT/name
            if path.exists() and not (saved/name).exists():
                import shutil
                shutil.copy2(path,saved/name)
    assert validation.get('phase')==4,'Release requires current Phase 4 validation, not historical outcomes'
    for name in ['SCIENTIFIC_AUDIT_REPORT.md','SCIENTIFIC_MANUSCRIPT_DRAFT.md']:
        assert (ROOT/name).is_file() and (ROOT/name).stat().st_size>1000
    assert len(json.loads((ROOT/'results/publication/figure_manifest.json').read_text()))==14
    source=[];research=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file() or not allowed(path):continue
        relative=path.relative_to(ROOT)
        if relative.parts[0] in {'data','results'}:
            research.append(path)
        elif relative.parts[0] in {'frontend','backend','scripts','tests','docs','config'} or len(relative.parts)==1:
            source.append(path)
    for required in ['README.md','frontend/package-lock.json','backend/requirements.lock.txt','scripts/discovery/independent_deseq2.R','scripts/package_release.py']:
        assert ROOT/required in source,required
    report={'phase':4,'status':'passed','archives':[create('NeuroGene_Atlas_Source.zip',source),create('NeuroGene_Atlas_Research_Results.zip',research)],'report_html_pdf_verified':True,'pdf_pages':len(parsed.pages),'pdf_required_sections':'all verified'}
    (OUT/'release_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
