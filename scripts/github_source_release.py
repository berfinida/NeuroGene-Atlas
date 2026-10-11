"""Package source-only release candidates; never push or publish anything."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from repository_audit import audit


def main():
    record = audit()
    if record['status'] != 'passed':
        raise ValueError('Repository audit must pass before packaging')
    folder = ROOT/'release/github'
    folder.mkdir(parents=True,exist_ok=True)
    destination = folder/'NeuroGene_Atlas_Source_v0.5.1.zip'
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for item in record['files']:
            bundle.write(ROOT/item['path'],item['path'])
        bundle.writestr('SOURCE_MANIFEST.json',json.dumps(record['files'],indent=2)+'\n')
    with zipfile.ZipFile(destination) as bundle:
        assert bundle.testzip() is None
        for item in record['files']:
            assert hashlib.sha256(bundle.read(item['path'])).hexdigest() == item['sha256']
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    (folder/'SOURCE_SHA256.txt').write_text(f'{checksum}  {destination.name}\n')
    summary = {k:v for k,v in record.items() if k != 'files'}
    summary.update(archive=destination.name,archive_bytes=destination.stat().st_size,
                   archive_sha256=checksum,CRC='passed',member_sha256='passed',
                   publication='source-only archive; this script performs no publication')
    (folder/'source_release_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
