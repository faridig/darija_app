import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
from darija_modules.parquet_downloader import DarijaParquetDownloader

class TestDarijaParquetDownloader(unittest.TestCase):
    """Tests unitaires pour la classe DarijaParquetDownloader"""

    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.downloader = DarijaParquetDownloader()
        # Créer un petit DataFrame de test
        self.test_df = pd.DataFrame({
            'id': [1, 2],
            'content': ['test1', 'test2']
        })

    @patch('huggingface_hub.hf_hub_download')
    def test_download_parquet(self, mock_download):
        """Test du téléchargement d'un fichier Parquet"""
        # Configuration du mock
        mock_path = Path('test.parquet')
        mock_download.return_value = mock_path

        # Exécution du test
        result = self.downloader.download_parquet('test/file.parquet')

        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_path)
        mock_download.assert_called_once()

    @patch('pandas.read_parquet')
    @patch('pandas.DataFrame.to_csv')
    def test_convert_to_csv(self, mock_to_csv, mock_read_parquet):
        """Test de la conversion Parquet vers CSV"""
        # Configuration des mocks
        mock_read_parquet.return_value = self.test_df
        test_path = Path('test.parquet')

        # Exécution du test
        with patch.object(Path, 'unlink') as mock_unlink:
            result = self.downloader.convert_to_csv(test_path)

        # Vérifications
        self.assertIsNotNone(result)
        mock_read_parquet.assert_called_once()
        mock_to_csv.assert_called_once()
        mock_unlink.assert_called_once()

    def test_process_file(self):
        """Test du processus complet pour un fichier"""
        # Configuration des mocks
        with patch.object(self.downloader, 'download_parquet') as mock_download:
            with patch.object(self.downloader, 'convert_to_csv') as mock_convert:
                mock_download.return_value = Path('test.parquet')
                mock_convert.return_value = Path('test.csv')

                # Exécution du test
                result = self.downloader.process_file('test/file.parquet')

        # Vérifications
        self.assertTrue(result)
        mock_download.assert_called_once()
        mock_convert.assert_called_once()

    def test_run(self):
        """Test de l'exécution complète du processus"""
        # Configuration du mock
        with patch.object(self.downloader, 'process_file') as mock_process:
            mock_process.return_value = True

            # Exécution du test
            result = self.downloader.run()

        # Vérifications
        self.assertTrue(result)
        self.assertEqual(mock_process.call_count, 2)  # Deux fichiers à traiter

    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Test d'erreur de téléchargement
        with patch.object(self.downloader, 'download_parquet', return_value=None):
            result = self.downloader.process_file('test/file.parquet')
            self.assertFalse(result)

        # Test d'erreur de conversion
        with patch.object(self.downloader, 'download_parquet', return_value=Path('test.parquet')):
            with patch.object(self.downloader, 'convert_to_csv', return_value=None):
                result = self.downloader.process_file('test/file.parquet')
                self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 