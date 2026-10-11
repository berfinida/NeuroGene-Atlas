"""Install a trusted, SHA-256 pinned ZIP without overwriting different local data."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def install(archive, checksum, root=ROOT):
    root = Path(root).resolve()
    if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum.lower():
        raise ValueError('Archive SHA-256 mismatch')
    with zipfile.ZipFile(archive) as bundle:
        selected = []
        total = 0
        for member in bundle.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in member.filename:
                raise ValueError('Unsafe archive path')
            if member.is_dir():
                continue
            if not path.parts or path.parts[0] not in ('data','results'):
                continue
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Archive symlink rejected')
            total += member.file_size
            if total > 1024**3:
                raise ValueError('Bundle uncompressed size exceeds 1 GiB')
            target = root.joinpath(*path.parts)
            if any(parent.is_symlink() for parent in (target, *target.parents)):
                raise ValueError('Local symlink rejected')
            data = bundle.read(member)
            if target.exists() and target.read_bytes() != data:
                raise ValueError(f'Refusing to overwrite changed local artifact: {path}')
            selected.append((target, data))
        if not selected:
            raise ValueError('No scientific data in archive')
        for target, data in selected:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(data)
    return len(selected)


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--file', type=Path)
    source.add_argument('--url')
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        archive = args.file
        if args.url:
            if not args.url.startswith('https://'):
                parser.error('Only HTTPS URLs are accepted')
            archive = Path(folder)/'bundle.zip'
            with urlopen(args.url, timeout=120) as response, archive.open('wb') as out:
                if not response.url.startswith('https://'):
                    raise ValueError('Insecure redirect')
                shutil.copyfileobj(response, out)
        print(f'Verified and installed {install(archive, args.sha256)} scientific files')


if __name__ == '__main__':
    main()
