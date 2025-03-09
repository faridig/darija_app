# Importation des bibliothèques nécessaires
import logging           # Pour les logs d'exécution
from pathlib import Path # Pour manipuler les chemins
import time             # Pour mesurer le temps d'exécution
import os              # Pour les chemins absolus

# Importation de nos modules personnalisés
from dataset_statistics import DarijaStatsAPI        # Module des statistiques
from parquet_downloader import DarijaParquetDownloader  # Module de téléchargement

def get_project_paths():
    """
    Retourne les chemins des dossiers du projet.
    """
    # Utiliser le dossier parent du module comme base
    module_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    project_root = module_dir.parent.parent  # Remonter au dossier racine du projet
    base_dir = project_root / "data_Darija-SFT-Mixture" / "darija_data"
    
    return {
        "base": base_dir,
        "logs": base_dir / "execution_logs",
        "parquet": base_dir / "parquet_files",
        "csv": base_dir / "csv_files",
        "stats": base_dir / "dataset_statistics"
    }

def setup_project_directories():
    """
    Crée tous les dossiers nécessaires pour le projet.
    """
    paths = get_project_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths

def setup_logging():
    """
    Configure le système de logs global pour tout le pipeline.
    Crée un fichier de log unique pour suivre l'exécution.
    """
    paths = get_project_paths()
    
    # Configurer le format et la destination des logs
    logging.basicConfig(
        level=logging.INFO,  # Niveau de détail : INFO
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format détaillé
        handlers=[
            logging.FileHandler(paths["logs"] / "pipeline.log"),  # Sauvegarde dans un fichier
            logging.StreamHandler()                               # Affichage dans la console
        ]
    )

class DarijaPipeline:
    """
    Classe principale qui orchestre l'ensemble du processus de traitement.
    Elle coordonne l'exécution des différents modules dans le bon ordre.
    """
    
    def __init__(self):
        # Créer les dossiers du projet
        self.paths = setup_project_directories()
        
        # Initialiser le système de logs
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== Initialisation du pipeline Darija ===")

    def execute_module(self, name, module):
        """
        Exécute un module spécifique et mesure son temps d'exécution.
        
        Paramètres :
            - name : nom du module (pour les logs)
            - module : instance du module à exécuter
            
        Retourne : True si succès, False si échec
        """
        # Annoncer le début du module
        self.logger.info(f"=== Module {name} ===")
        start_time = time.time()
        
        # Exécuter le module
        success = module.run()
        duration = time.time() - start_time
        
        # Logger le résultat
        if success:
            self.logger.info(f"Module {name} terminé en {duration:.2f} secondes")
        else:
            self.logger.error(f"Échec du module {name}")
        
        return success

    def run(self):
        """
        Exécute le pipeline complet dans l'ordre suivant :
        1. Récupération des statistiques du dataset
        2. Téléchargement et conversion des fichiers
        """
        # Démarrer le chronomètre
        start_time = time.time()
        
        # 1. Module de statistiques
        stats_module = DarijaStatsAPI(self.paths["stats"])
        if not self.execute_module("statistiques", stats_module):
            self.logger.error("Pipeline arrêté : échec des statistiques")
            return False
        
        # 2. Module de téléchargement
        download_module = DarijaParquetDownloader(self.paths["parquet"], self.paths["csv"])
        if not self.execute_module("téléchargement", download_module):
            self.logger.error("Pipeline arrêté : échec du téléchargement")
            return False
        
        # Calculer et logger le temps total
        duration = time.time() - start_time
        self.logger.info(f"=== Pipeline terminé en {duration:.2f} secondes ===")
        return True

# Point d'entrée du programme
if __name__ == "__main__":
    # Créer et exécuter le pipeline
    pipeline = DarijaPipeline()
    pipeline.run() 