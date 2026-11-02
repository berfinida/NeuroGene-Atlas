"""Synthetic security fixtures; these are not scientific result evidence."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.runtime import Settings, WindowLimiter, configure, verify_bundle


class ProductionPolicy(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name).resolve()
        (self.root / "fixture.csv").write_text("synthetic_fixture,value\nsoftware_test,1\n")
        self.manifest = {"schema": 1, "files": [{"path": "fixture.csv", "sha256": hashlib.sha256((self.root/"fixture.csv").read_bytes()).hexdigest()}]}
        self.persist()

    def persist(self):
        (self.root / "PUBLIC_MANIFEST.json").write_text(json.dumps(self.manifest))

    def settings(self, mode="preview", approval="", rate=300, timeout=20):
        return Settings(mode, self.root, approval, ("testserver",), ("https://allowed.example",), rate, timeout)

    def client(self, settings=None):
        app = FastAPI()
        serve = configure(app, settings or self.settings())
        @app.get("/api/test")
        def fixture():
            return {"fixture": "software only"}
        @app.get("/api/file")
        def file():
            return serve(self.root/"fixture.csv")
        @app.get("/api/missing")
        def missing():
            return (self.root/"missing.csv").read_text()
        @app.get("/api/failure")
        def failure():
            raise RuntimeError("Sensitive internal detail")
        @app.get("/api/slow")
        async def slow():
            await asyncio.sleep(.1)
            return {}
        return TestClient(app)

    def test_manifest_and_owner_approval(self):
        self.assertEqual(verify_bundle(self.settings())[2], {"fixture.csv"})
        with self.assertRaises(ValueError):
            verify_bundle(self.settings("public"))
        digest = hashlib.sha256((self.root/"PUBLIC_MANIFEST.json").read_bytes()).hexdigest()
        self.assertEqual(verify_bundle(self.settings("public", digest))[1], digest)

    def test_changed_and_extra_files_rejected(self):
        (self.root/"unexpected.csv").write_text("extra")
        with self.assertRaises(ValueError): verify_bundle(self.settings())
        (self.root/"unexpected.csv").unlink()
        (self.root/"fixture.csv").write_text("changed")
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_traversal_rejected(self):
        self.manifest["files"][0]["path"] = "../fixture.csv"
        self.persist()
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_symlink_rejected(self):
        original = self.root/"fixture.csv"
        other = self.root/"other.csv"
        original.rename(other)
        original.symlink_to(other)
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_duplicate_manifest_entries_rejected(self):
        self.manifest["files"].append(dict(self.manifest["files"][0]))
        self.persist()
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_unlisted_symlink_directory_rejected(self):
        (self.root / "unused_link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_credential_content_rejected(self):
        content = ("ghp_" + "A" * 40).encode()
        (self.root/"fixture.csv").write_bytes(content)
        self.manifest["files"][0]["sha256"] = hashlib.sha256(content).hexdigest()
        self.persist()
        with self.assertRaises(ValueError): verify_bundle(self.settings())

    def test_hosts_cors_and_security_headers(self):
        client = self.client()
        self.assertEqual(client.get("/api/test", headers={"Host": "evil.example"}).status_code, 400)
        response = client.get("/api/test", headers={"Origin": "https://allowed.example"})
        self.assertEqual(response.headers["access-control-allow-origin"], "https://allowed.example")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("not-approved", response.headers["x-publication-status"])
        self.assertNotIn("access-control-allow-origin", client.get("/api/test", headers={"Origin": "https://evil.example"}).headers)

    def test_read_only_and_raw_archive_denial(self):
        client = self.client()
        self.assertEqual(client.post("/api/test").status_code, 405)
        self.assertEqual(client.get("/api/download/report").status_code, 403)
        self.assertEqual(client.get("/api/studies/GSE156496/download/counts").status_code, 403)
        self.assertEqual(client.get("/api/file").status_code, 200)

    def test_error_details_and_input_budget(self):
        client = self.client()
        self.assertEqual(client.get("/api/missing").status_code, 503)
        response = client.get("/api/failure")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("Sensitive", response.text)
        self.assertEqual(client.get("/api/test?q="+"a"*2049).status_code, 414)

    def test_timeout_and_rate_limit(self):
        client = self.client(self.settings(rate=1, timeout=.01))
        self.assertEqual(client.get("/api/slow").status_code, 504)
        response = client.get("/api/test")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "60")

    def test_limiter_memory_and_window(self):
        limiter = WindowLimiter(1, capacity=1)
        self.assertTrue(limiter.allow("a", 0))
        self.assertFalse(limiter.allow("a", 1))
        self.assertFalse(limiter.allow("b", 1))
        self.assertTrue(limiter.allow("b", 61))

    def test_environment_validation(self):
        for env in ({"NEUROGENE_MODE":"invalid"}, {"NEUROGENE_ALLOWED_HOSTS":"*"},
                    {"NEUROGENE_CORS_ORIGINS":"http://example.com"}, {"NEUROGENE_REQUESTS_PER_MINUTE":"0"},
                    {"NEUROGENE_ENV":"production", "NEUROGENE_MODE":"research"}):
            with patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError): Settings.from_env()

    def test_cors_credentials_and_wildcard_hosts_rejected(self):
        for env in ({"NEUROGENE_ALLOWED_HOSTS":"*.example.com"},
                    {"NEUROGENE_CORS_ORIGINS":"https://" + "fixture-user:fixture-password" + "@example.com"},
                    {"NEUROGENE_CORS_ORIGINS":"https://example.com?query=1"}):
            with patch.dict(os.environ, env, clear=True), self.assertRaises(ValueError): Settings.from_env()
