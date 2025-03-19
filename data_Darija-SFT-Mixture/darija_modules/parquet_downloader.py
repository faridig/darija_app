import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from azure.storage.blob import BlobServiceClient

class DarijaParquetUploader:
    """
    Cette classe télécharge les fichiers Parquet du dataset Darija
    et les envoie directement sur Azure Blob Storage, sans stockage local.
    """

    def __init__(self):
        # 1. Charger les tokens et configurations
        load_dotenv("huggingface_token.env")  # Token Hugging Face
        load_dotenv(".env")  # Configuration Azure

        self.hf_token = os.getenv('HUGGINGFACE_TOKEN')
        self.dataset_id = "MBZUAI-Paris/Darija-SFT-Mixture"

        # 2. Configuration d'Azure Blob Storage
        self.azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.azure_container_name = os.getenv("AZURE_CONTAINER_NAME")

        # 3. Initialisation de la connexion à Azure
        self.blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.azure_container_name)

        # 4. Initialisation du logger
        self.logger = logging.getLogger(__name__)

    def stream_to_azure(self, file_name):
        """
        Télécharge un fichier Parquet depuis Hugging Face et l'envoie directement sur Azure sans stockage local.
        """
        try:
            self.logger.info(f"📥 Téléchargement et envoi en direct de {file_name}")

            # Télécharger le fichier en mémoire (stream)
            file_stream = BytesIO()
            with open(hf_hub_download(repo_id=self.dataset_id, filename=file_name, repo_type="dataset", token=self.hf_token), "rb") as f:
                file_stream.write(f.read())

            file_stream.seek(0)  # Remettre le curseur au début

            # Envoi sur Azure
            blob_client = self.container_client.get_blob_client(file_name)
            blob_client.upload_blob(file_stream, overwrite=True)

            self.logger.info(f"✅ Fichier {file_name} envoyé sur Azure Blob Storage directement !")

        except Exception as e:
            self.logger.error(f"❌ Erreur lors du streaming vers Azure : {str(e)}")

    def run(self):
        """
        Exécute le processus : Téléchargement + Envoi direct sur Azure.
        """
        self.logger.info("🚀 Début du traitement des fichiers Parquet")

        files = [
            "data/train-00000-of-00002.parquet",
            "data/train-00001-of-00002.parquet"
        ]

        for file_name in files:
            self.stream_to_azure(file_name)

        self.logger.info(f"🎉 Tous les fichiers ont été envoyés directement sur Azure !")

# Point d'entrée si exécuté directement
if __name__ == "__main__":
    uploader = DarijaParquetUploader()
    uploader.run()
