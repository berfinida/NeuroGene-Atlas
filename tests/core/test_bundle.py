"""Adversarial archive software fixtures, never scientific data."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.install_research_bundle import install


class BundleSoftware(unittest.TestCase):
    def fixture(self, folder, members):
        archive = Path(folder)/'fixture.zip'
        with zipfile.ZipFile(archive,'w') as bundle:
            for name, content in members.items():
                bundle.writestr(name, content)
        return archive, hashlib.sha256(archive.read_bytes()).hexdigest()

    def test_checksum_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, _ = self.fixture(folder, {'data/fixture.txt':'synthetic'})
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                install(archive,'0'*64,Path(folder)/'target')

    def test_path_traversal_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, checksum = self.fixture(folder, {'../unsafe.txt':'synthetic'})
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                install(archive,checksum,Path(folder)/'target')

    def test_install_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, checksum = self.fixture(folder, {'data/fixture.txt':'synthetic'})
            root = Path(folder)/'target'
            self.assertEqual(install(archive,checksum,root),1)
            self.assertEqual(install(archive,checksum,root),1)
            self.assertEqual((root/'data/fixture.txt').read_text(),'synthetic')

    def test_changed_data_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, checksum = self.fixture(folder, {'data/fixture.txt':'synthetic'})
            root = Path(folder)/'target'
            install(archive,checksum,root)
            (root/'data/fixture.txt').write_text('user edit')
            with self.assertRaisesRegex(ValueError,'overwrite'):
                install(archive,checksum,root)
            self.assertEqual((root/'data/fixture.txt').read_text(),'user edit')

    def test_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            archive, checksum = self.fixture(folder, {'data/fixture.txt':'synthetic'})
            root = Path(folder)/'target'
            root.mkdir()
            (root/'data').symlink_to(Path(folder),target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'symlink'):
                install(archive,checksum,root)
