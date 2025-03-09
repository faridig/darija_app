import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
import pandas as pd

class DarijaParquetDownloader:
    """
    Cette classe gère le téléchargement des fichiers Parquet du dataset Darija
    et leur conversion en format CSV pour une meilleure utilisation.
    """
    
    def __init__(self, parquet_dir: Path, csv_dir: Path):
        # 1. Configuration de l'accès à Hugging Face
        load_dotenv("huggingface_token.env")  # Charger le token depuis le fichier .env
        self.token = os.getenv('HUGGINGFACE_TOKEN')
        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"  # ID du dataset
        
        # 2. Utilisation des chemins fournis
        self.parquet_dir = parquet_dir
        self.csv_dir = csv_dir
        
        # 3. Utilisation du logger existant
        self.logger = logging.getLogger(__name__)
    
    def download_parquet(self, file_path):
        """
        Télécharge un fichier Parquet depuis Hugging Face.
        Paramètre : file_path - chemin du fichier sur Hugging Face
        Retourne : chemin local du fichier téléchargé ou None si erreur
        """
        try:
            self.logger.info(f"Téléchargement de {file_path}")
            
            # Utiliser l'API Hugging Face pour télécharger
            local_path = hf_hub_download(
                repo_id=self.dataset_id,      # ID du dataset
                filename=file_path,           # Fichier à télécharger
                repo_type="dataset",          # Type de dépôt
                token=self.token,             # Token d'authentification
                local_dir=self.parquet_dir    # Où sauvegarder
            )
            
            return Path(local_path)
            
        except Exception as e:
            self.logger.error(f"Erreur lors du téléchargement : {str(e)}")
            return None

    def convert_to_csv(self, parquet_path):
        """
        Convertit un fichier Parquet en CSV.
        Paramètre : parquet_path - chemin du fichier Parquet
        Retourne : chemin du fichier CSV créé ou None si erreur
        """
        try:
            # 1. Lire le fichier Parquet avec pandas
            self.logger.info(f"Conversion de {parquet_path.name}")
            df = pd.read_parquet(parquet_path)
            
            # 2. Créer et sauvegarder le fichier CSV
            csv_path = self.csv_dir / f"{parquet_path.stem}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            self.logger.info(f"Fichier converti en CSV : {csv_path.name}")
            
            # 3. Nettoyer : supprimer le fichier Parquet temporaire
            parquet_path.unlink()
            self.logger.info(f"Fichier Parquet temporaire supprimé")
            
            return csv_path
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion : {str(e)}")
            return None

    def process_file(self, file_path):
        """
        Traite un fichier : téléchargement puis conversion.
        Paramètre : file_path - chemin du fichier sur Hugging Face
        Retourne : True si succès, False si erreur
        """
        # 1. Télécharger le fichier Parquet
        parquet_path = self.download_parquet(file_path)
        if not parquet_path:
            return False
            
        # 2. Convertir en CSV
        csv_path = self.convert_to_csv(parquet_path)
        if not csv_path:
            return False
            
        return True

    def run(self):
        """
        Exécute le processus complet de téléchargement et conversion.
        C'est la méthode principale qui orchestre tout le processus.
        """
        self.logger.info("Traitement des fichiers Parquet")
        
        # Liste des fichiers à traiter (on sait qu'il y en a 2)
        files = [
            "data/train-00000-of-00002.parquet",  # Première partie
            "data/train-00001-of-00002.parquet"   # Deuxième partie
        ]
        
        # Traiter chaque fichier
        for file_path in files:
            if not self.process_file(file_path):
                self.logger.error(f"Échec du traitement de {file_path}")
                return False
        
        self.logger.info(f"Conversion terminée : {len(files)} fichiers traités")
        return True

# Point d'entrée si exécuté directement
if __name__ == "__main__":
    downloader = DarijaParquetDownloader(Path("darija_data/parquet_files"), Path("darija_data/csv_files"))
    downloader.run() 