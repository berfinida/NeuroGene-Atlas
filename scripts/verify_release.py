"""Verify final archives and run scientific/API tests from their clean paired extraction."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'release'

def main():
    checked=[]
    with tempfile.TemporaryDirectory(prefix='neurogene-release-') as directory:
        target=Path(directory)
        for name,manifest in [('NeuroGene_Atlas_Source.zip','SOURCE_RELEASE_MANIFEST.json'),('NeuroGene_Atlas_Research_Results.zip','RESEARCH_RELEASE_MANIFEST.json')]:
            path=OUT/name
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                files=json.loads(archive.read(manifest))['sha256']
                for filename,expected in files.items():
                    relative=Path(filename)
                    assert not relative.is_absolute() and '..' not in relative.parts
                    assert hashlib.sha256(archive.read(filename)).hexdigest()==expected
                archive.extractall(target)
            checked.append({'archive':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'verified_files':len(files)})
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=target,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (OUT/'extracted_release_tests.log').write_text(result.stdout)
        print(result.stdout)
        count=re.search(r'Ran (\d+) tests',result.stdout)
        assert result.returncode==0,'Extracted-release tests failed'
        record={'status':'passed','archives':checked,'clean_paired_extraction':True,'python_api_tests':int(count.group(1)) if count else None,'test_exit_code':result.returncode,'log':'release/extracted_release_tests.log','python_environment':'Existing pinned environment; clean source/data extraction, not a new dependency installation'}
    (OUT/'extracted_release_validation.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
