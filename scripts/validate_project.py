"""Capture actual commands, exit codes, logs and browser evidence; never infer success."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/validation'

def run(name,command,cwd=ROOT,environment=None):
    env=os.environ.copy()
    if environment:env.update(environment)
    started=datetime.now(timezone.utc).isoformat()
    result=subprocess.run(command,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (OUT/f'{name}.log').write_text(result.stdout)
    print(result.stdout,flush=True)
    record={'command':command,'cwd':str(cwd),'environment_overrides':environment or {},'started_utc':started,'exit_code':result.returncode,'log':f'results/validation/{name}.log'}
    ledger=OUT/'executed_commands.json'
    previous=json.loads(ledger.read_text()) if ledger.exists() else []
    previous.append(record);ledger.write_text(json.dumps(previous,indent=2)+'\n')
    record['status']='passed' if result.returncode==0 else 'failed'
    return record,result.stdout

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build-only',action='store_true');parser.add_argument('--base-url',default='http://127.0.0.1:3002');parser.add_argument('--api-url',default='http://127.0.0.1:8002');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    prior=OUT/'final_validation.json'
    if prior.exists() and json.loads(prior.read_text()).get('phase')!=4:
        archive=OUT/'phase3';archive.mkdir(exist_ok=True)
        for path in OUT.iterdir():
            if path.is_file() and not (archive/path.name).exists():shutil.copy2(path,archive/path.name)
    if prior.exists() and json.loads(prior.read_text()).get('phase')==4 and json.loads(prior.read_text()).get('status')=='failed':
        archive=OUT/'phase4_initial_failure';archive.mkdir(exist_ok=True)
        for name in ['final_validation.json','playwright_results.json','playwright.log']:
            if not (archive/name).exists():shutil.copy2(OUT/name,archive/name)
        timestamp=json.loads(prior.read_text())['checked_at_utc'].replace(':','').replace('.','')
        history=OUT/'phase4_failures'/timestamp;history.mkdir(parents=True,exist_ok=True)
        for name in ['final_validation.json','python_tests.log','playwright_results.json','playwright.log']:
            if not (history/name).exists():shutil.copy2(OUT/name,history/name)
    if args.build_only:
        record,_=run('production_build',['npm','run','build'],ROOT/'frontend',{'API_INTERNAL_URL':args.api_url})
        (OUT/'build_validation.json').write_text(json.dumps(record,indent=2)+'\n')
        sys.exit(record['exit_code'])
    checks={}
    checks['python'],output=run('python_tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
    match=re.search(r'Ran (\d+) tests',output)
    checks['python']['tests_run']=int(match.group(1)) if match else None
    checks['typescript'],_=run('typecheck',['npm','run','typecheck'],ROOT/'frontend')
    checks['dependency_audit'],audit=run('dependency_audit',['npm','audit','--omit=dev','--json'],ROOT/'frontend')
    (OUT/'dependency_audit.json').write_text(audit)
    checks['playwright'],_=run('playwright',['npx','playwright','test'],ROOT/'frontend',{'E2E_BASE_URL':args.base_url})
    browser=ROOT/'frontend/test-results/results.json'
    if browser.exists():
        shutil.copy2(browser,OUT/'playwright_results.json')
        checks['playwright']['stats']=json.loads(browser.read_text())['stats']
    shots=OUT/'screenshots';shots.mkdir(exist_ok=True)
    for path in (ROOT/'frontend/test-results').glob('*.png'):shutil.copy2(path,shots/path.name)
    checks['production_build']=json.loads((OUT/'build_validation.json').read_text())
    package=ROOT/'frontend/package.json'
    api_count=len(re.findall(r'^test_\S+ \((?:test_api\.APIIntegration|test_discovery\.DiscoveryAPI|test_phase4\.Phase4API)\.',output,re.M))
    stats=checks['playwright'].get('stats',{})
    validation={'phase':4,'status':'passed' if all(c['status']=='passed' for c in checks.values()) else 'failed','checked_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'runtime':{'python':sys.version,'frontend_packages':json.loads(package.read_text())['dependencies']},'coverage':f"{checks['python']['tests_run']} Python tests including {api_count} API integration tests; {stats.get('expected',0)} passing Chromium E2E checks across desktop/mobile; production Next.js build, TypeScript and runtime dependency audit",'scientific_reproduction':'Eight discovery numeric tables matched independently from original inputs in Phase 3; current stored-fit contrast/BH audit in all three studies; no second isolated external fit reproduction','limitations':['No clinical validation','Docker unavailable, recipe untested','Chromium emulation only','Extracted release reuses pinned environment; not a new dependency install']}
    (OUT/'final_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(validation,indent=2));sys.exit(0 if validation['status']=='passed' else 1)

if __name__=='__main__':main()
