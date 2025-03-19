import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, length, col, to_json
import pandas as pd
import json
import ast

# Charger les variables d'environnement
load_dotenv()

# Vérifier si les identifiants Azure sont bien définis
storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_CONTAINER_NAME")
parquet_folder = "data/"

if not storage_account_name or not storage_account_key or not container_name:
    raise ValueError("❌ ERREUR : Vérifie que les variables AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY et AZURE_CONTAINER_NAME sont bien définies dans .env.")

# Chemin vers les fichiers JAR Hadoop et Azure
hadoop_jars_path = os.path.expanduser("~/hadoop_jars")

# Liste des JARs nécessaires
jars = [
    f"{hadoop_jars_path}/hadoop-azure-3.3.1.jar",
    f"{hadoop_jars_path}/azure-storage-8.6.6.jar",
    f"{hadoop_jars_path}/jetty-util-9.4.40.v20210413.jar",
    f"{hadoop_jars_path}/jetty-util-ajax-9.4.40.v20210413.jar"
]

# Configuration Spark optimisée avec plus de mémoire
spark = SparkSession.builder \
    .appName("AzureParquetAnalysis") \
    .master("local[*]") \
    .config("spark.jars", ",".join(jars)) \
    .config("spark.hadoop.fs.azure", "org.apache.hadoop.fs.azure.NativeAzureFileSystem") \
    .config(f"spark.hadoop.fs.azure.account.key.{storage_account_name}.blob.core.windows.net", storage_account_key) \
    .config("spark.hadoop.fs.azure.account.auth.type", "SharedKey") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.maxResultSize", "2g") \
    .config("spark.driver.host", "localhost") \
    .getOrCreate()

print("✅ PySpark est bien configuré avec les fichiers JAR pour Azure !")

def load_and_filter_data():
    """Charge et filtre les données depuis Azure Blob Storage."""
    # URL du stockage Azure
    azure_url = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/{parquet_folder}"
    print(f"📂 Lecture des fichiers Parquet depuis : {azure_url}")
    
    # Lecture des données
    df = spark.read.parquet(azure_url)
    print("✅ Lecture réussie !")

    # 1. Réduire le nombre de partitions
    df_optimise = df.coalesce(4)

    # 2. Définir les directions à conserver
    directions_a_garder = ['dr_fr', 'fr_dr', 'en_dr', 'dr_en']

    # 3. Optimisation du filtrage avec cache
    df_filtre = df_optimise \
        .select('dataset', 'id', 'messages', 'direction') \
        .filter(col('direction').isin(directions_a_garder)) \
        .repartition(4, 'direction') \
        .persist()

    # 4. Créer le DataFrame plat avec messages_json
    df_plat = df_filtre \
        .withColumn("messages_json", to_json(col("messages"))) \
        .drop("messages") \
        .select("dataset", "id", "messages_json", "direction") \
        .toPandas()

    print(f"📊 Nombre de lignes : {len(df_plat):,}")
    print("\n📊 Distribution des directions :")
    print(df_plat['direction'].value_counts())

    return df_plat

# Dictionnaire direction → langues
DIRECTION_MAPPING = {
    "en_dr": ("en", "darija"),
    "fr_dr": ("fr", "darija"),
    "dr_fr": ("darija", "fr"),
    "dr_en": ("darija", "en")
}

def parse_messages(messages):
    """
    Parse les messages qui peuvent être soit déjà sous forme de liste,
    soit une chaîne de caractères à convertir.
    """
    if isinstance(messages, list):
        return messages
    if isinstance(messages, str):
        try:
            # Assurer une séparation correcte entre objets JSON
            messages = messages.replace("}\n {", "}, {")
            return ast.literal_eval(messages)
        except (ValueError, SyntaxError):
            return None
    return None

def clean_translations(df: pd.DataFrame):
    """
    Nettoie et structure les traductions à partir du DataFrame.
    
    Retourne une liste de traductions valides, les données invalides et le nombre d'entrées nettoyées.
    """
    valid_data = []
    invalid_data = []
    cleaned_count = 0

    for index, row in df.iterrows():
        # Utilisation de la colonne "messages_json" à la place de "messages"
        messages = parse_messages(row["messages_json"])
        direction = row.get("direction")

        # Vérifier la validité des messages
        if not messages or len(messages) < 2 or len(messages) % 2 != 0:
            invalid_data.append({
                "index": index,
                "reason": "Invalid message format",
                "messages": row["messages_json"]
            })
            continue

        # Vérifier la validité de la direction
        if direction not in DIRECTION_MAPPING:
            invalid_data.append({
                "index": index,
                "reason": "Unknown direction value",
                "direction": direction,
                "messages": messages
            })
            continue

        source_lang, target_lang = DIRECTION_MAPPING[direction]

        # Parcourir les messages deux par deux
        for i in range(0, len(messages), 2):
            user_msg = messages[i]
            assistant_msg = messages[i+1]

            if "content" not in user_msg or "content" not in assistant_msg:
                invalid_data.append({
                    "index": index,
                    "reason": "Missing 'content'",
                    "messages": [user_msg, assistant_msg]
                })
                continue

            user_content = user_msg["content"].strip()
            # Cas spécial : consigne courte ("ترجم:" suivi directement de la phrase)
            if user_content.startswith("ترجم:"):
                original_text = user_content.replace("ترجم:", "", 1).strip()
            else:
                content_parts = user_content.splitlines()
                if len(content_parts) <= 1:
                    invalid_data.append({
                        "index": index,
                        "reason": "Missing actual text to translate",
                        "messages": [user_msg, assistant_msg]
                    })
                    continue
                original_text = content_parts[1].strip()

            translation_text = assistant_msg["content"].strip()
            valid_data.append({
                "input": {source_lang: original_text, target_lang: translation_text}
            })
            cleaned_count += 1

    return valid_data, invalid_data, cleaned_count

def save_json(data, filename: str):
    """Sauvegarde les données dans un fichier JSON avec encodage UTF-8."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def structure_translations(cleaned_file: str, output_file: str):
    """
    Transforme le JSON nettoyé en un format structuré explicite 
    avec les champs 'source_lang', 'source', 'target_lang' et 'target'.
    """
    with open(cleaned_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    structured_translations = []
    for item in data.get("translations", []):
        inp = item.get("input", {})
        if len(inp) == 2:
            languages = list(inp.keys())
            structured_translations.append({
                "source_lang": languages[0],
                "source": inp[languages[0]],
                "target_lang": languages[1],
                "target": inp[languages[1]]
            })

    save_json({"translations": structured_translations}, output_file)

def save_to_csv(df: pd.DataFrame, output_dir: str):
    """Sauvegarde le DataFrame en format CSV."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "translations.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ DataFrame sauvegardé en CSV dans : {csv_path}")

if __name__ == "__main__":
    print("🚀 Démarrage du traitement des données...")
    
    # Charger et filtrer les données depuis Azure
    print("\n📥 Chargement des données depuis Azure...")
    merged_df = load_and_filter_data()
    
    # Sauvegarder en CSV
    csv_output_dir = "/projets/darija_app/data_Darija-SFT-Mixture/darija_data/csv_files"
    print("\n💾 Sauvegarde du DataFrame en CSV...")
    save_to_csv(merged_df, csv_output_dir)
    
    print("\n🧹 Nettoyage des données...")
    valid_data, invalid_data, cleaned_count = clean_translations(merged_df)

    # Obtenir le chemin du dossier courant (agregation)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Définir les chemins des fichiers de sortie dans le dossier agregation
    cleaned_file = os.path.join(current_dir, "cleaned_translations.json")
    invalid_file = os.path.join(current_dir, "invalid_translations.json")
    structured_file = os.path.join(current_dir, "structured_translations.json")

    print("\n💾 Sauvegarde des résultats...")
    save_json({"translations": valid_data}, cleaned_file)
    save_json(invalid_data, invalid_file)

    print(f"\n✅ Nettoyage terminé ! {cleaned_count} entrées nettoyées et conservées.")
    print(f"⚠️ {len(invalid_data)} entrées bruitées détectées et enregistrées dans {invalid_file}")

    if invalid_data:
        print("\n🔎 Exemples d'erreurs détectées :")
        for error in invalid_data[:5]:
            print(f"- Index {error['index']} : {error['reason']}")
            print(f"  Messages : {error['messages']}\n")

    # Structuration finale des traductions nettoyées
    print("\n🔄 Structuration finale des données...")
    structure_translations(cleaned_file, structured_file)
    print("\n✨ Traitement terminé avec succès !")

    # Arrêter la session Spark
    spark.stop()
