"""Audit publishable files and EVERY local Git blob, including unreachable objects.

Heuristic credential scan, not a security certification. Never prints secret values.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'github_token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})\b',
    'aws_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'openai_key': rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b',
    'credential_url': rb'https?://[^\s/:]+:[^\s/@]+@',
    'credential_assignment': rb'(?im)^\s*(?:[A-Z_]*(?:SECRET|TOKEN|PASSWORD|API_KEY))\s*=\s*[\x22\x27]?[A-Za-z0-9_+/=-]{16,}',
}
LOCAL_PATH = rb'(?:/(?:Users|private|var/folders|opt/homebrew|Library)/|file:[/]{2}|[A-Za-z]:\\Users\\)'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def source_files():
    names = set(git('ls-files', '-z').split(b'\0')) | set(git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0'))
    return sorted(n.decode() for n in names if n and (ROOT / n.decode()).is_file())


def findings(data):
    return [name for name, pattern in PATTERNS.items() if re.search(pattern, data)]


def audit():
    files = source_files()
    alerts = []
    sizes = []
    for name in files:
        path = ROOT / name
        if path.is_symlink():
            alerts.append({'file': name, 'rule':'source_symlink'})
            continue
        data = path.read_bytes()
        alerts.extend({'file':name, 'rule':rule} for rule in findings(data))
        if re.search(LOCAL_PATH, data):
            alerts.append({'file':name, 'rule':'machine_local_path'})
        sizes.append({'path':name, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()})
    objects = git('cat-file', '--batch-all-objects', '--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines()
    blobs = [line.split()[0] for line in objects if line.split()[1] == 'blob']
    with subprocess.Popen(['git','cat-file','--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE) as process:
        for oid in blobs:
            process.stdin.write((oid+'\n').encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().split()
            data = process.stdout.read(int(header[2]))
            process.stdout.read(1)
            alerts.extend({'git_blob':oid, 'rule':rule} for rule in findings(data))
        process.stdin.close()
        process.wait()
    commits = git('rev-list', '--all').decode().splitlines()
    large = [s for s in sizes if s['bytes'] > 5 * 1024 * 1024]
    forbidden = [n for n in files if n.split('/')[0] in ('data','results','release','.venv','.runtime')
                 or any(p in n.split('/') for p in ('node_modules','.next','__pycache__'))
                 or n.endswith('.zip') or (Path(n).name.startswith('.env') and Path(n).name != '.env.example')]
    return {'checked_utc':datetime.now(timezone.utc).isoformat(), 'source_files':len(files),
            'source_bytes':sum(s['bytes'] for s in sizes), 'git_commits':len(commits),
            'all_git_objects':len(objects), 'all_git_blobs_scanned':len(blobs),
            'scope':'All source candidates plus all local Git blobs, reachable and unreachable',
            'credential_findings':alerts, 'files_over_5MiB':large, 'forbidden_source_paths':forbidden,
            'status':'passed' if not (alerts or large or forbidden) else 'review_required',
            'limitations':['Pattern-based scan cannot establish absence of all secrets or personal data.',
                           'Public clinical data and credentials must never be added.'], 'files':sizes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'results/validation/github/repository_audit.json')
    args = parser.parse_args()
    record = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k != 'files'}, indent=2))
    raise SystemExit(0 if record['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
