"""Source-only software checks. Synthetic fixtures are NOT research evidence."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app, filtered


class CoreAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_schema(self):
        self.assertEqual(self.client.get('/openapi.json').status_code, 200)

    def test_scientific_scope_headers(self):
        with tempfile.TemporaryDirectory() as folder, patch('backend.main.OUT', Path(folder)):
            response = self.client.get('/api/datasets')
            self.assertIn('not clinical', response.headers['X-Scientific-Scope'])
            self.assertIn('unresolved', response.headers['X-Cohort-Caution'])

    def test_unavailable_dataset(self):
        with tempfile.TemporaryDirectory() as folder, patch('backend.main.OUT', Path(folder)):
            self.assertEqual(self.client.get('/api/datasets').status_code, 503)
            self.assertEqual(self.client.get('/api/qc').status_code, 503)

    def test_search_requires_input(self):
        for path in ('/api/gene-search', '/api/gene-search?q='):
            self.assertEqual(self.client.get(path).status_code, 422)

    def test_invalid_filter(self):
        for query in ('padj=0', 'lfc=-1', 'offset=-1', 'limit=999', 'direction=unknown'):
            self.assertEqual(self.client.get('/api/genes?' + query).status_code, 422)

    def test_download_allowlist(self):
        self.assertEqual(self.client.get('/api/final/download/credentials.txt').status_code, 404)

    def test_missing_figure(self):
        with tempfile.TemporaryDirectory() as folder, patch('backend.main.OUT', Path(folder)):
            self.assertEqual(self.client.get('/api/figures/pca.png').status_code, 404)

    def test_literal_filter_synthetic_fixture(self):
        frame = pd.DataFrame({'gene_id':['fixture1','fixture2'], 'gene_symbol':['[.*','Other'],
                              'padj':[0.01,0.02], 'log2FoldChange':[2,-3], 'baseMean':[10,20]})
        with patch('backend.main.results', return_value=frame):
            self.assertEqual(filtered('[.*', .05, 1, 'up', 'unshrunken', 'padj').gene_id.tolist(), ['fixture1'])
            body = self.client.get('/api/genes?direction=down').json()
            self.assertEqual(body['total'], 1)
            self.assertEqual(body['rows'][0]['gene_id'], 'fixture2')

    def test_study_identifier_validation(self):
        self.assertEqual(self.client.get('/api/studies/invalid').status_code, 422)
