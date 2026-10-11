"""Fresh local source install, source-only browser checks, then real-data checks.

No publication. Services are always shut down; evidence stays outside scratch.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/validation/github/clean_extract'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'validation.json').exists():
        history = OUT/'history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
        history.mkdir(parents=True)
        for path in OUT.iterdir():
            if path.is_file():
                shutil.copy2(path,history/path.name)
    commands = []
    services = []
    handles = []
    record = {'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),
              'commands':commands,'limitations':['Same macOS host, not hosted Linux CI; existing Chromium binary reused.',
                                                 'No R rerun; original Phase 5 reproduction preserved.']}

    def run(name, command, cwd, env=None):
        with (OUT/(name+'.log')).open('w') as log:
            result = subprocess.run(command,cwd=cwd,env=dict(os.environ,**(env or {})),stdout=log,stderr=subprocess.STDOUT)
        commands.append({'command':list(map(str,command)),'cwd':str(cwd),'environment':env or {},'exit_code':result.returncode,'log':name+'.log'})
        (OUT/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
        print(name, result.returncode,flush=True)
        result.check_returncode()

    try:
        archive = ROOT/'release/github/NeuroGene_Atlas_Source_v0.5.1.zip'
        record['source_archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='neurogene-github-clean-') as folder:
            scratch = Path(folder)
            with zipfile.ZipFile(archive) as bundle:
                assert bundle.testzip() is None
                manifest = json.loads(bundle.read('SOURCE_MANIFEST.json'))
                for item in manifest:
                    assert hashlib.sha256(bundle.read(item['path'])).hexdigest() == item['sha256']
                bundle.extractall(scratch)
            assert not (scratch/'data').exists() and not (scratch/'results').exists()
            run('venv',[sys.executable,'-m','venv',str(scratch/'.venv')],scratch)
            python = str(scratch/'.venv/bin/python')
            run('pip_install',[python,'-m','pip','install','-r','backend/requirements.lock.txt'],scratch)
            run('pip_check',[python,'-m','pip','check'],scratch)
            run('core_tests',[python,'-m','unittest','discover','-s','tests/core','-v'],scratch)
            run('npm_ci',['npm','ci'],scratch/'frontend')
            run('build',[python,'scripts/final_validate.py','--build-only','--api-url','http://127.0.0.1:8007','--out-dir','results/validation/github'],scratch)
            for name,command,cwd in [('api',[python,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8007'],scratch),
                                     ('frontend',['npm','run','start','--','--port','3007'],scratch/'frontend')]:
                handle = (OUT/(name+'.log')).open('w')
                handles.append(handle)
                process = subprocess.Popen(command,cwd=cwd,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
                services.append(process)
                commands.append({'command':command,'cwd':str(cwd),'service':True,'pid':process.pid})
            for attempt in range(90):
                if any(p.poll() is not None for p in services):
                    raise RuntimeError('Clean-extracted service exited prematurely')
                try:
                    if httpx.get('http://127.0.0.1:3007',timeout=2).status_code == 200 and httpx.get('http://127.0.0.1:8007/openapi.json',timeout=2).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('Service startup timed out')
            assert httpx.get('http://127.0.0.1:8007/api/datasets').status_code == 503
            run('core_browser',['npx','playwright','test'],scratch/'frontend',{'E2E_CORE':'1','E2E_BASE_URL':'http://127.0.0.1:3007'})
            core = json.loads((scratch/'frontend/test-results/results.json').read_text())['stats']
            record['source_only_browser'] = core
            run('install_research',[python,'scripts/install_research_bundle.py','--file',str(ROOT/'release/NeuroGene_Atlas_Research_Results_FINAL.zip'),
                                    '--sha256','f211ba30301105074bde3d59596ca1645edadd1b1e993ab8f14f088f7751c3bd'],scratch)
            run('full_validation',[python,'scripts/final_validate.py','--api-url','http://127.0.0.1:8007',
                                   '--base-url','http://127.0.0.1:3007','--out-dir','results/validation/github'],scratch)
            record['real_data'] = json.loads((scratch/'results/validation/github/tests.json').read_text())
            assert record['real_data']['status'] == 'passed'
            record['status'] = 'passed'
    except Exception as error:
        record.update(status='failed',error=str(error))
        raise
    finally:
        for process in services:
            try:
                os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
        for handle in handles:
            handle.close()
        record['completed_utc'] = datetime.now(timezone.utc).isoformat()
        (OUT/'validation.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record,indent=2),flush=True)


if __name__ == '__main__':
    main()
