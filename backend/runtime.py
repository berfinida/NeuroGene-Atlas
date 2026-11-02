"""Read-only serving policy; data publication is an explicit, hash-bound opt-in."""
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
import uuid

from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse

VERSION = "0.6.0-rc.1"
SOURCE = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("neurogene.requests")
if not LOG.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOG.addHandler(handler)
LOG.setLevel(os.getenv("NEUROGENE_LOG_LEVEL", "INFO"))
LOG.propagate = False
UNSAFE = re.compile(rb'/(?:Users|private|var/folders|opt/homebrew|Library)/|file:[/]{2}|\bgh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----')


@dataclass(frozen=True)
class Settings:
    mode: str
    root: Path
    approval: str
    hosts: tuple[str, ...]
    origins: tuple[str, ...]
    rate: int
    timeout: float

    @classmethod
    def from_env(cls):
        mode = os.getenv("NEUROGENE_MODE", "research")
        if mode not in {"research", "preview", "public"}:
            raise ValueError("Invalid serving mode")
        if os.getenv("NEUROGENE_ENV") == "production" and mode == "research":
            raise ValueError("Production must use a reviewed serving mode")
        hosts = tuple(h.strip() for h in os.getenv("NEUROGENE_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip())
        origins = tuple(filter(None, os.getenv("NEUROGENE_CORS_ORIGINS", "").split(",")))
        if not hosts or any("*" in h for h in hosts) or any(urlsplit(o).scheme != "https" or not urlsplit(o).hostname or urlsplit(o).path or urlsplit(o).username or urlsplit(o).password or urlsplit(o).query or urlsplit(o).fragment for o in origins):
            raise ValueError("Explicit hosts and HTTPS CORS origins required")
        rate, timeout = int(os.getenv("NEUROGENE_REQUESTS_PER_MINUTE", "300")), float(os.getenv("NEUROGENE_REQUEST_TIMEOUT", "20"))
        if not 1 <= rate <= 10000 or not 0 < timeout <= 60:
            raise ValueError("Invalid request budget")
        return cls(mode, Path(os.getenv("NEUROGENE_DATA_ROOT", str(SOURCE))).resolve(),
                   os.getenv("NEUROGENE_PUBLIC_APPROVAL_SHA256", ""), hosts, origins,
                   rate, timeout)


def verify_bundle(settings):
    path = settings.root / "PUBLIC_MANIFEST.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Reviewed results manifest required")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if settings.mode == "public" and settings.approval != digest:
        raise ValueError("Explicit owner approval for this exact manifest is required")
    if UNSAFE.search(path.read_bytes()):
        raise ValueError("Unsafe manifest metadata")
    manifest = json.loads(path.read_text())
    if manifest.get("schema") != 1 or not manifest.get("files"):
        raise ValueError("Invalid results manifest")
    names = set()
    for item in manifest["files"]:
        name = item["path"]
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or name in names:
            raise ValueError("Invalid results path")
        names.add(name)
        target = settings.root / relative
        if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(settings.root):
            raise ValueError("Unsafe results file")
        content = target.read_bytes()
        if UNSAFE.search(content):
            raise ValueError("Unsafe results metadata")
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError("Results checksum mismatch")
    entries = list(settings.root.rglob("*"))
    if any(p.is_symlink() for p in entries):
        raise ValueError("Symlinks are forbidden in reviewed results")
    actual = {str(p.relative_to(settings.root)) for p in entries if p.is_file()}
    if actual != names | {"PUBLIC_MANIFEST.json"}:
        raise ValueError("Unlisted files in results directory")
    return manifest, digest, names


class WindowLimiter:
    def __init__(self, limit, capacity=4096):
        self.limit, self.capacity = limit, capacity
        self.clients = OrderedDict()

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        while self.clients and now - next(iter(self.clients.values()))[0] >= 60:
            self.clients.popitem(last=False)
        start, count = self.clients.get(key, (now, 0))
        if len(self.clients) >= self.capacity and key not in self.clients:
            return False
        self.clients[key] = (start, count + 1)
        return count < self.limit


def configure(app, settings):
    manifest, digest, allowed = (None, None, set())
    if settings.mode != "research":
        manifest, digest, allowed = verify_bundle(settings)
    app.state.serving = {"mode": settings.mode, "manifest_sha256": digest, "manifest": manifest}
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.hosts))
    if settings.origins:
        app.add_middleware(CORSMiddleware, allow_origins=list(settings.origins),
                           allow_methods=["GET", "HEAD"], allow_headers=["Accept"], allow_credentials=False)
    limiter = WindowLimiter(settings.rate)
    slots = asyncio.Semaphore(4)

    @app.middleware("http")
    async def serving_boundary(request, call_next):
        start, request_id = time.monotonic(), uuid.uuid4().hex
        path = request.url.path
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            response = JSONResponse({"detail": "Read-only research service"}, status_code=405)
        elif len(request.scope.get("query_string", b"")) > 2048 or len(path) > 512:
            response = JSONResponse({"detail": "Request too large"}, status_code=414)
        elif settings.mode != "research" and path.startswith("/api/") and not limiter.allow(request.client.host if request.client else "unknown"):
            response = JSONResponse({"detail": "Request limit reached"}, status_code=429, headers={"Retry-After": "60"})
        elif settings.mode != "research" and (path.startswith("/api/research/report/") or path.startswith("/api/final/download/") or path.startswith("/api/publication") or path in {"/api/download/report", "/api/download/session", "/api/download/provenance"} or "/download/counts" in path or "/download/session" in path):
            response = JSONResponse({"detail": "Artifact is excluded from the reviewed demo bundle"}, status_code=403)
        else:
            try:
                if settings.mode == "research":
                    response = await asyncio.wait_for(call_next(request), timeout=settings.timeout)
                else:
                    acquired = False
                    try:
                        await asyncio.wait_for(slots.acquire(), timeout=.1)
                        acquired = True
                        response = await asyncio.wait_for(call_next(request), timeout=settings.timeout)
                    finally:
                        if acquired:
                            slots.release()
            except FileNotFoundError:
                response = JSONResponse({"detail": "Scientific research data are not installed"}, status_code=503)
            except TimeoutError:
                response = JSONResponse({"detail": "Research request timed out"}, status_code=504)
            except Exception:
                response = JSONResponse({"detail": "Scientific service unavailable"}, status_code=500)
        response.headers.update({"X-Request-ID": request_id, "X-Content-Type-Options": "nosniff",
                                 "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY"})
        if settings.mode != "research":
            response.headers["X-Publication-Status"] = "approved-manifest" if settings.mode == "public" else "local-review-preview-not-approved-for-publication"
            response.headers["Cache-Control"] = "no-store"
        LOG.info(json.dumps({"request_id": request_id, "method": request.method,
                             "status": response.status_code, "duration_ms": round((time.monotonic()-start)*1000, 2),
                             "mode": settings.mode}))
        return response

    def serve(path, filename=None):
        path = Path(path)
        if settings.mode != "research":
            if not path.resolve().is_relative_to(settings.root) or path.is_symlink() or str(path.relative_to(settings.root)) not in allowed:
                raise HTTPException(403, "Artifact is excluded from the reviewed demo bundle")
            if path.stat().st_size > 32 * 1024 * 1024:
                raise HTTPException(413, "Download exceeds demo limit")
        return FileResponse(path, filename=filename)
    return serve
