import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
from darija_modules.dataset_statistics import DarijaStatsAPI

class TestDarijaStatsAPI(unittest.TestCase):
    """Tests unitaires pour la classe DarijaStatsAPI"""

    def setUp(self):
        """Configuration initiale pour chaque test"""
        self.api = DarijaStatsAPI()
        self.mock_info = {
            'id': 'MBZUAI-Paris/Darija-SFT-Mixture',
            'author': 'MBZUAI-Paris',
            'cardData': {
                'license': 'odc-by',
                'task_categories': ['question-answering', 'conversational'],
                'size_categories': ['100K<n<1M']
            },
            'lastModified': '2024-02-19',
            'downloads': 100,
            'likes': 10,
            'files': ['file1.parquet', 'file2.parquet']
        }

    @patch('requests.get')
    def test_get_dataset_info(self, mock_get):
        """Test de la récupération des informations du dataset"""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_info
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Exécution du test
        info = self.api.get_dataset_info()

        # Vérifications
        self.assertIsNotNone(info)
        self.assertEqual(info['id'], 'MBZUAI-Paris/Darija-SFT-Mixture')
        mock_get.assert_called()

    def test_prepare_stats(self):
        """Test de la préparation des statistiques"""
        # Exécution du test
        stats = self.api.prepare_stats(self.mock_info)

        # Vérifications
        self.assertEqual(stats['dataset']['nom'], 'MBZUAI-Paris/Darija-SFT-Mixture')
        self.assertEqual(stats['dataset']['auteur'], 'MBZUAI-Paris')
        self.assertEqual(stats['dataset']['licence'], 'odc-by')
        self.assertEqual(stats['contenu']['tâches'], ['question-answering', 'conversational'])

    def test_create_report(self):
        """Test de la création du rapport Markdown"""
        # Préparation des données
        stats = self.api.prepare_stats(self.mock_info)

        # Exécution du test
        report = self.api.create_report(stats)

        # Vérifications
        self.assertIsInstance(report, str)
        self.assertIn('# Dataset MBZUAI-Paris/Darija-SFT-Mixture', report)
        self.assertIn('## À propos', report)
        self.assertIn('## Contenu', report)

    @patch('builtins.open', create=True)
    def test_save_results(self, mock_open):
        """Test de la sauvegarde des résultats"""
        # Préparation des données
        stats = self.api.prepare_stats(self.mock_info)
        report = self.api.create_report(stats)

        # Exécution du test
        result = self.api.save_results(stats, report)

        # Vérifications
        self.assertTrue(result)
        mock_open.assert_called()

    @patch('requests.get')
    def test_run_complete_process(self, mock_get):
        """Test du processus complet"""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_info
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Exécution du test
        with patch('builtins.open', create=True):
            result = self.api.run()

        # Vérifications
        self.assertTrue(result)
        mock_get.assert_called()

if __name__ == '__main__':
    unittest.main() 