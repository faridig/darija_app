import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import requests

class DarijaStatsAPI:
    """
    Cette classe gère la récupération et l'analyse des statistiques du dataset Darija.
    Elle utilise l'API Hugging Face pour obtenir les informations.
    """
    
    def __init__(self, stats_dir: Path):
        # 1. Configuration de l'accès à l'API
        load_dotenv("huggingface_token.env")  # Charger le token depuis le fichier .env
        self.token = os.getenv('HUGGINGFACE_TOKEN')
        
        # 2. Paramètres de l'API
        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"  # ID du dataset
        self.api_url = f"https://huggingface.co/api/datasets/{self.dataset_id}"
        self.headers = {
            "Authorization": f"Bearer {self.token}",  # Token pour l'authentification
            "Accept": "application/json"              # Format de réponse souhaité
        }
        
        # 3. Utilisation du chemin fourni
        self.stats_dir = stats_dir
        
        # 4. Utilisation du logger existant
        self.logger = logging.getLogger(__name__)

    def get_dataset_info(self):
        """
        Récupère les informations du dataset via l'API Hugging Face.
        Retourne un dictionnaire avec toutes les informations ou None en cas d'erreur.
        """
        try:
            # 1. Récupérer les informations générales
            response = requests.get(self.api_url, headers=self.headers)
            info = response.json()
            
            # 2. Récupérer la liste des fichiers disponibles
            files_url = f"{self.api_url}/parquet"
            files_response = requests.get(files_url, headers=self.headers)
            info['files'] = files_response.json() if files_response.status_code == 200 else []
            
            return info
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la requête API : {str(e)}")
            return None

    def prepare_stats(self, info):
        """
        Organise les informations brutes en un format structuré et lisible.
        Paramètre : info - données brutes de l'API
        Retourne : dictionnaire organisé des statistiques
        """
        return {
            # 1. Informations sur le dataset
            "dataset": {
                "nom": info.get('id'),
                "auteur": info.get('author'),
                "licence": info.get('cardData', {}).get('license'),
                "mis_à_jour": info.get('lastModified'),
                "popularité": {
                    "téléchargements": info.get('downloads', 0),
                    "likes": info.get('likes', 0)
                }
            },
            # 2. Contenu du dataset
            "contenu": {
                "tâches": info.get('cardData', {}).get('task_categories', []),
                "taille": info.get('cardData', {}).get('size_categories', []),
                "format": "Parquet",
                "fichiers": {
                    "nombre": len(info.get('files', [])),
                    "liste": info.get('files', [])
                }
            }
        }

    def create_report(self, stats):
        """
        Crée un rapport en format Markdown à partir des statistiques.
        Paramètre : stats - statistiques organisées
        Retourne : chaîne de caractères en format Markdown
        """
        return f"""# Dataset {stats['dataset']['nom']}

## À propos
- **Auteur :** {stats['dataset']['auteur']}
- **Licence :** {stats['dataset']['licence']}
- **Dernière mise à jour :** {stats['dataset']['mis_à_jour']}

## Popularité
- {stats['dataset']['popularité']['téléchargements']} téléchargements
- {stats['dataset']['popularité']['likes']} likes

## Contenu
- **Tâches :** {', '.join(stats['contenu']['tâches'])}
- **Taille :** {', '.join(stats['contenu']['taille'])}
- **Format :** {stats['contenu']['format']}

## Fichiers ({stats['contenu']['fichiers']['nombre']})
{chr(10).join(['- ' + f for f in stats['contenu']['fichiers']['liste']])}
"""

    def save_results(self, stats, report):
        """
        Sauvegarde les résultats dans des fichiers.
        Paramètres :
            - stats : statistiques à sauvegarder en JSON
            - report : rapport à sauvegarder en Markdown
        """
        try:
            # 1. Sauvegarder les statistiques en JSON
            stats_file = self.stats_dir / "dataset_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            self.logger.info("Statistiques sauvegardées en JSON")
            
            # 2. Sauvegarder le rapport en Markdown
            report_file = self.stats_dir / "dataset_report.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info("Rapport sauvegardé en Markdown")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde : {str(e)}")
            return False

    def run(self):
        """
        Exécute l'analyse complète du dataset.
        C'est la méthode principale qui orchestre tout le processus.
        """
        self.logger.info("Analyse des statistiques du dataset")
        
        # 1. Récupérer les informations via l'API
        info = self.get_dataset_info()
        if not info:
            return False
        
        # 2. Organiser les statistiques
        stats = self.prepare_stats(info)
        
        # 3. Créer le rapport Markdown
        report = self.create_report(stats)
        
        # 4. Sauvegarder les résultats
        return self.save_results(stats, report)

# Point d'entrée si exécuté directement
if __name__ == "__main__":
    api = DarijaStatsAPI(Path("darija_data/dataset_statistics"))
    api.run() 